"""Archivio permanente: utenti (email + password) e swing analizzati.

Il database si sceglie con la variabile DATABASE_URL (nei "secrets" di
Streamlit o nell'ambiente):
- online: un Postgres gratuito, per esempio Neon
  (postgresql://utente:password@host/db?sslmode=require);
- senza DATABASE_URL: un file SQLite locale (swinglab.db), comodo sul PC.
  Su Streamlit Cloud questo file si perde a ogni riavvio dell'app.

Le password non vengono mai salvate: si salva solo un'impronta
PBKDF2-SHA256 con sale casuale (standard consigliato da OWASP).
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import hmac
import json
import os
import re
import secrets
from pathlib import Path

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary,
                        MetaData, String, Table, Text, create_engine, delete, func, insert,
                        inspect, select, text, update)

ITERAZIONI = 310_000
PASSWORD_MIN = 8
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DB_LOCALE = Path(__file__).resolve().parent.parent / "swinglab.db"

meta = MetaData()

utenti = Table(
    "utenti", meta,
    Column("id", Integer, primary_key=True),
    Column("email", String(254), unique=True, nullable=False),
    Column("nome", String(80)),
    Column("sale", LargeBinary, nullable=False),
    Column("impronta", LargeBinary, nullable=False),
    Column("profilo", Text),                      # preferenze in JSON (mano, bastone, ...)
    Column("creato", DateTime, nullable=False),
)

swing = Table(
    "swing", meta,
    Column("id", Integer, primary_key=True),
    Column("utente_id", Integer, ForeignKey("utenti.id", ondelete="CASCADE"), index=True,
           nullable=False),
    Column("quando", DateTime, nullable=False),
    Column("nome", String(80)),                   # nome dato dall'utente allo swing
    Column("punteggio", Integer),
    Column("bastone", String(40)),
    Column("viste", String(20)),
    Column("priorita", String(200)),
    Column("carry", Float),
    Column("dimostrativo", Boolean, default=False),
    Column("report_gz", LargeBinary),             # report HTML compresso
    Column("video", LargeBinary),                 # video commentato (mp4)
)


class ErroreAccount(ValueError):
    """Errore da mostrare così com'è all'utente."""


def url_database(segreti: dict | None = None) -> str:
    url = (segreti or {}).get("DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return f"sqlite:///{DB_LOCALE}"
    # Neon e Supabase danno "postgres://" o "postgresql://": SQLAlchemy vuole il driver
    url = re.sub(r"^postgres(ql)?://", "postgresql+psycopg2://", url)
    return url


def e_permanente(url: str) -> bool:
    return not url.startswith("sqlite")


def crea_motore(url: str):
    kw = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
    motore = create_engine(url, **kw)
    meta.create_all(motore)
    _aggiorna_tabelle(motore)
    return motore


def _aggiorna_tabelle(motore):
    """Aggiunge le colonne nate dopo la prima versione (i dati esistenti restano)."""
    colonne = {c["name"] for c in inspect(motore).get_columns("swing")}
    with motore.begin() as c:
        if "nome" not in colonne:
            c.execute(text("ALTER TABLE swing ADD COLUMN nome VARCHAR(80)"))


# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------

def _impronta(password: str, sale: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sale, ITERAZIONI)


def _normalizza_email(email: str) -> str:
    return (email or "").strip().lower()


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

def registra(motore, email: str, password: str, nome: str = "") -> dict:
    email = _normalizza_email(email)
    if not EMAIL_RE.match(email):
        raise ErroreAccount("L'email non sembra valida: controlla di averla scritta per intero.")
    if len(password or "") < PASSWORD_MIN:
        raise ErroreAccount(f"La password deve avere almeno {PASSWORD_MIN} caratteri.")
    with motore.begin() as c:
        if c.execute(select(utenti.c.id).where(utenti.c.email == email)).first():
            raise ErroreAccount("Esiste già un account con questa email: usa \"Accedi\".")
        sale = secrets.token_bytes(16)
        nome = (nome or "").strip()[:80] or email.split("@")[0]
        r = c.execute(insert(utenti).values(
            email=email, nome=nome, sale=sale, impronta=_impronta(password, sale),
            profilo="{}", creato=dt.datetime.now()))
        return dict(id=r.inserted_primary_key[0], email=email, nome=nome, profilo={})


def accedi(motore, email: str, password: str) -> dict:
    email = _normalizza_email(email)
    with motore.connect() as c:
        u = c.execute(select(utenti).where(utenti.c.email == email)).mappings().first()
    # stesso messaggio se manca l'utente o se la password è sbagliata
    errore = ErroreAccount("Email o password non corrette.")
    if not u:
        _impronta(password or "", b"0" * 16)      # tempo simile anche se l'utente non esiste
        raise errore
    if not hmac.compare_digest(_impronta(password or "", u["sale"]), u["impronta"]):
        raise errore
    return dict(id=u["id"], email=u["email"], nome=u["nome"],
                profilo=json.loads(u["profilo"] or "{}"))


def salva_profilo(motore, utente_id: int, profilo: dict):
    with motore.begin() as c:
        c.execute(update(utenti).where(utenti.c.id == utente_id)
                  .values(profilo=json.dumps(profilo, ensure_ascii=False)))


def elimina_account(motore, utente_id: int):
    with motore.begin() as c:
        c.execute(delete(swing).where(swing.c.utente_id == utente_id))
        c.execute(delete(utenti).where(utenti.c.id == utente_id))


# ---------------------------------------------------------------------------
# Swing
# ---------------------------------------------------------------------------

def salva_swing(motore, utente_id: int, ris: dict, report_html: str, video: bytes | None,
                dimostrativo=False, nome: str | None = None) -> int:
    with motore.begin() as c:
        r = c.execute(insert(swing).values(
            utente_id=utente_id,
            quando=dt.datetime.now(),
            nome=(nome or "").strip()[:80] or None,
            punteggio=int(ris["punteggi"]["totale"]),
            bastone=ris["profilo"].bastone,
            viste=", ".join(ris["tracce"].keys()),
            priorita=(ris["difetti"][0]["titolo"] if ris["difetti"] else "Nessun difetto rilevante")[:200],
            carry=float(ris["volo"]["carry"]["m"]),
            dimostrativo=bool(dimostrativo),
            report_gz=gzip.compress(report_html.encode("utf-8")),
            video=video,
        ))
        return r.inserted_primary_key[0]


def elenco_swing(motore, utente_id: int) -> list[dict]:
    """Elenco senza i contenuti pesanti (report e video si caricano a richiesta)."""
    q = (select(swing.c.id, swing.c.quando, swing.c.nome, swing.c.punteggio, swing.c.bastone, swing.c.viste,
                swing.c.priorita, swing.c.carry, swing.c.dimostrativo,
                (swing.c.video.isnot(None)).label("ha_video"))
         .where(swing.c.utente_id == utente_id).order_by(swing.c.quando.desc()))
    with motore.connect() as c:
        return [dict(r) for r in c.execute(q).mappings()]


def conta_swing(motore, utente_id: int) -> int:
    with motore.connect() as c:
        return c.execute(select(func.count()).select_from(swing)
                         .where(swing.c.utente_id == utente_id)).scalar_one()


def carica_swing(motore, utente_id: int, swing_id: int) -> dict | None:
    """Report e video di uno swing, solo se appartiene all'utente."""
    with motore.connect() as c:
        r = c.execute(select(swing.c.report_gz, swing.c.video)
                      .where(swing.c.id == swing_id, swing.c.utente_id == utente_id)).first()
    if not r:
        return None
    return dict(report=gzip.decompress(r.report_gz).decode("utf-8") if r.report_gz else "",
                video=r.video)


def elimina_swing(motore, utente_id: int, swing_id: int):
    with motore.begin() as c:
        c.execute(delete(swing).where(swing.c.id == swing_id, swing.c.utente_id == utente_id))


def cambia_nome(motore, utente_id: int, nome: str) -> str:
    nome = (nome or "").strip()[:80]
    if not nome:
        raise ErroreAccount("Il nome non può essere vuoto.")
    with motore.begin() as c:
        c.execute(update(utenti).where(utenti.c.id == utente_id).values(nome=nome))
    return nome


def cambia_password(motore, utente_id: int, attuale: str, nuova: str):
    if len(nuova or "") < PASSWORD_MIN:
        raise ErroreAccount(f"La nuova password deve avere almeno {PASSWORD_MIN} caratteri.")
    with motore.begin() as c:
        u = c.execute(select(utenti.c.sale, utenti.c.impronta).where(utenti.c.id == utente_id)).first()
        if not u or not hmac.compare_digest(_impronta(attuale or "", u.sale), u.impronta):
            raise ErroreAccount("La password attuale non è corretta.")
        sale = secrets.token_bytes(16)
        c.execute(update(utenti).where(utenti.c.id == utente_id)
                  .values(sale=sale, impronta=_impronta(nuova, sale)))


def rinomina_swing(motore, utente_id: int, swing_id: int, nome: str):
    with motore.begin() as c:
        c.execute(update(swing).where(swing.c.id == swing_id, swing.c.utente_id == utente_id)
                  .values(nome=(nome or "").strip()[:80] or None))
