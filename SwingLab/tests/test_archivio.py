"""Controlli dell'archivio: account, password, swing per utente."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swinglab_core import archivio, demo, pipeline  # noqa: E402


def _db():
    d = tempfile.mkdtemp()
    return archivio.crea_motore(f"sqlite:///{d}/test.db")


def _ris():
    return pipeline.analizza_tracce(demo.tracce(("A",)), pipeline.Profilo())


def _errore(fn, *a):
    try:
        fn(*a)
    except archivio.ErroreAccount as e:
        return str(e)
    raise AssertionError("doveva dare errore")


def test_registra_e_accedi():
    db = _db()
    u = archivio.registra(db, " Ale@Test.it ", "password123", "Ale")
    assert u["email"] == "ale@test.it"
    assert archivio.accedi(db, "ALE@test.it", "password123")["id"] == u["id"]
    assert "non corrette" in _errore(archivio.accedi, db, "ale@test.it", "sbagliata1")
    assert "non corrette" in _errore(archivio.accedi, db, "nessuno@test.it", "password123")
    assert "già" in _errore(archivio.registra, db, "ale@test.it", "altrapass1")
    assert "8 caratteri" in _errore(archivio.registra, db, "b@test.it", "corta")
    assert "valida" in _errore(archivio.registra, db, "non-una-email", "password123")


def test_password_non_salvata_in_chiaro():
    db = _db()
    archivio.registra(db, "a@b.it", "segretissima")
    with db.connect() as c:
        riga = c.execute(archivio.select(archivio.utenti)).mappings().first()
    assert b"segretissima" not in riga["impronta"] and "segretissima" not in str(dict(riga))


def test_swing_separati_per_utente():
    db = _db()
    a = archivio.registra(db, "a@b.it", "password123")
    b = archivio.registra(db, "c@d.it", "password123")
    r = _ris()
    sid = archivio.salva_swing(db, a["id"], r, "<html>report</html>", b"video", dimostrativo=True)
    assert archivio.conta_swing(db, a["id"]) == 1 and archivio.conta_swing(db, b["id"]) == 0
    assert archivio.carica_swing(db, b["id"], sid) is None          # B non vede gli swing di A
    dati = archivio.carica_swing(db, a["id"], sid)
    assert dati["report"] == "<html>report</html>" and dati["video"] == b"video"
    archivio.elimina_swing(db, b["id"], sid)                         # B non può cancellarli
    assert archivio.conta_swing(db, a["id"]) == 1
    archivio.elimina_swing(db, a["id"], sid)
    assert archivio.conta_swing(db, a["id"]) == 0


def test_profilo_ricordato_ed_elimina_account():
    db = _db()
    u = archivio.registra(db, "a@b.it", "password123")
    archivio.salva_profilo(db, u["id"], {"bastone": "Driver", "mancino": True})
    assert archivio.accedi(db, "a@b.it", "password123")["profilo"]["bastone"] == "Driver"
    archivio.salva_swing(db, u["id"], _ris(), "x", None)
    archivio.elimina_account(db, u["id"])
    assert "non corrette" in _errore(archivio.accedi, db, "a@b.it", "password123")
    assert archivio.conta_swing(db, u["id"]) == 0


def test_nome_swing_e_vecchio_database():
    import sqlalchemy as sa
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/vecchio.db"
    # database creato dalla versione precedente, senza la colonna "nome"
    with sa.create_engine(url).begin() as c:
        c.execute(sa.text("CREATE TABLE swing (id INTEGER PRIMARY KEY, utente_id INTEGER, quando DATETIME)"))
    db = archivio.crea_motore(url)
    assert "nome" in {c["name"] for c in sa.inspect(db).get_columns("swing")}
    db2 = _db()
    u = archivio.registra(db2, "a@b.it", "password123")
    sid = archivio.salva_swing(db2, u["id"], _ris(), "x", None, nome="Driver – lavoro sul finish")
    assert archivio.elenco_swing(db2, u["id"])[0]["nome"] == "Driver – lavoro sul finish"
    archivio.rinomina_swing(db2, u["id"], sid, "Driver buono")
    assert archivio.elenco_swing(db2, u["id"])[0]["nome"] == "Driver buono"


if __name__ == "__main__":
    test = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in test:
        t()
        print("OK ", t.__name__)
    print(f"\nTutti i {len(test)} test superati.")
