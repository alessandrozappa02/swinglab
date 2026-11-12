"""SwingLab – interfaccia web locale (Streamlit).

Avvio:  python -m streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components

from swinglab_core import config as C
from swinglab_core import archivio, demo, pipeline, report, taglio, video_commento
from swinglab_core import video as V

st.set_page_config(page_title="SwingLab", page_icon="⛳", layout="wide")

# ---------------------------------------------------------------------------
# Tema "fairway": verde campo, crema sabbia, giallo bandierina
# ---------------------------------------------------------------------------
# Fraunces (titoli) + Figtree (testo); colori nel blocco :root
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Figtree:wght@400;500;600;700&display=swap');
:root{
--fairway:#0f2b1e;
--rough:#163a29;
--green:#1f5a3c;
--linea:#2c6a4a;
--crema:#f1ecd9;
--crema2:#c9d3c2;
--flag:#f2c94c;
--palla:#ffffff;
--display:"Fraunces",Georgia,serif;
--testo:"Figtree","Segoe UI",system-ui,sans-serif;
}
html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea, button {font-family:var(--testo)}
[data-testid="stAppViewContainer"]{
background:
repeating-linear-gradient(90deg, rgba(255,255,255,.022) 0 90px, rgba(0,0,0,.035) 90px 180px),
radial-gradient(1200px 500px at 70% -10%, #1d4f37 0%, transparent 60%),
var(--fairway);
}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.5rem;max-width:1150px}
[data-testid="stSidebar"]{
background:linear-gradient(180deg,#123224 0%,#0c2318 100%);
border-right:1px solid var(--linea);
}
[data-testid="stSidebar"] h2{font-family:var(--display);color:var(--crema);letter-spacing:.01em}
h1,h2,h3{font-family:var(--display)!important;color:var(--crema)!important;text-wrap:balance}
.sl-hero{position:relative;overflow:hidden;border-radius:18px;padding:26px 28px 22px;margin:0 0 18px;
border:1px solid var(--linea);
background:
repeating-linear-gradient(115deg, rgba(255,255,255,.05) 0 34px, rgba(255,255,255,0) 34px 68px),
linear-gradient(135deg,#1f5a3c 0%,#174530 55%,#123a28 100%)}
.sl-hero .eyebrow{font:600 12px/1 var(--testo);letter-spacing:.18em;text-transform:uppercase;color:var(--flag)}
.sl-hero h1{font-size:44px;line-height:1.05;margin:.35rem 0 .4rem;padding:0}
.sl-hero p{color:var(--crema2);margin:0;max-width:46ch;font-size:16px}
.sl-hero .stats{display:flex;gap:18px;flex-wrap:wrap;margin-top:14px;font-size:13px;color:var(--crema2)}
.sl-hero .stats b{color:var(--crema);font-variant-numeric:tabular-nums}
.sl-hero svg.pin{position:absolute;right:26px;bottom:-6px;height:150px;opacity:.95}
@media (max-width:700px){.sl-hero svg.pin{height:90px;right:10px;opacity:.5}.sl-hero h1{font-size:34px}}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--linea)}
.stTabs [data-baseweb="tab"]{background:rgba(255,255,255,.03);border-radius:10px 10px 0 0;padding:8px 14px;color:var(--crema2)}
.stTabs [aria-selected="true"]{background:var(--rough);color:var(--crema)!important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--flag)}
[data-testid="stFileUploaderDropzone"]{background:rgba(31,90,60,.35);border:1.5px dashed #4f8f6b;border-radius:14px}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--flag)}
.sl-tee{display:flex;align-items:flex-start;gap:8px;font-weight:600;color:var(--crema);margin:4px 0 6px;min-height:52px;line-height:1.35}
.sl-tee .bollo{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;
background:var(--palla);color:var(--fairway);font:700 13px/1 var(--testo);
box-shadow:inset -3px -3px 0 rgba(0,0,0,.08)}
.stButton>button,.stDownloadButton>button{border-radius:999px;font-weight:600;padding:.5rem 1.2rem;
border:1px solid var(--linea)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"],.stFormSubmitButton>button{color:#1b2a12!important;box-shadow:0 2px 0 #b8902a;border-radius:999px;font-weight:600}
.stButton>button:focus-visible{outline:2px solid var(--flag);outline-offset:2px}
.stButton>button:disabled{background:rgba(255,255,255,.06)!important;color:var(--crema2)!important;border:1px dashed var(--linea)!important;box-shadow:none!important;opacity:1}
[data-testid="stAlert"]{border-radius:12px}
.guida{border:1px solid var(--linea);background:rgba(255,255,255,.04);border-radius:12px;padding:10px 12px;font-size:14px;color:var(--crema2)}
.sl-card,.sl-scelta{border:1px solid var(--linea);background:rgba(22,58,41,.75);border-radius:16px;padding:20px 22px}
.sl-card h3,.sl-scelta h3{margin:0 0 8px}
.sl-passi{margin:0;padding-left:20px;color:var(--crema2);line-height:1.7}
.sl-passi b{color:var(--crema)}
.sl-scelta{min-height:150px;margin-bottom:10px}
.sl-scelta p{color:var(--crema2);margin:0}
.sl-scelta .ico{font-size:28px;line-height:1;margin-bottom:8px}
.sl-voto{font:700 40px/1 var(--display);color:var(--flag)}
.sl-voto span{font-size:14px;color:var(--crema2);margin-left:2px}
[data-testid="stForm"]{border:1px solid var(--linea);background:rgba(22,58,41,.75);border-radius:16px;padding:20px 22px}
.st-key-sl_menu{position:fixed;top:calc(env(safe-area-inset-top,0px) + 58px);right:max(16px,env(safe-area-inset-right,0px));z-index:999990;width:auto!important}
.st-key-sl_menu [data-testid="stPopover"]>div>button,.st-key-sl_menu [data-testid="stPopoverButton"],.st-key-sl_menu button{width:54px!important;height:54px!important;min-height:54px!important;padding:0!important;border-radius:50%!important;border:2px solid #0b2216!important;font-size:0!important;color:transparent!important;background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><defs><radialGradient id='g' cx='38%25' cy='32%25' r='70%25'><stop offset='0' stop-color='%23ffffff'/><stop offset='.7' stop-color='%23eef0ea'/><stop offset='1' stop-color='%23c9cec4'/></radialGradient></defs><circle cx='32' cy='32' r='30' fill='url(%23g)'/><g fill='%23b9beb4' opacity='.85'><circle cx='22' cy='18' r='2.6'/><circle cx='32' cy='15' r='2.6'/><circle cx='42' cy='18' r='2.6'/><circle cx='17' cy='27' r='2.6'/><circle cx='27' cy='25' r='2.6'/><circle cx='37' cy='25' r='2.6'/><circle cx='47' cy='27' r='2.6'/><circle cx='15' cy='37' r='2.6'/><circle cx='25' cy='34' r='2.6'/><circle cx='35' cy='34' r='2.6'/><circle cx='45' cy='36' r='2.6'/><circle cx='19' cy='46' r='2.6'/><circle cx='29' cy='43' r='2.6'/><circle cx='39' cy='43' r='2.6'/><circle cx='48' cy='45' r='2.6'/><circle cx='26' cy='52' r='2.6'/><circle cx='36' cy='52' r='2.6'/></g></svg>") center/100% no-repeat!important;box-shadow:0 4px 12px rgba(0,0,0,.45)!important}
.st-key-sl_menu button *{display:none!important}
.st-key-sl_menu button:hover{transform:rotate(25deg);transition:transform .25s}
.st-key-sl_menu button:focus-visible{outline:3px solid var(--flag)!important;outline-offset:3px}
.st-key-sl_topbar{padding-right:64px}
.st-key-sl_topbar [data-testid="stColumn"]{min-width:0!important;width:auto!important;flex:1 1 0!important}
.st-key-sl_topbar [data-testid="stColumn"]:last-child{display:flex;justify-content:flex-end}
.st-key-sl_topbar [data-testid="stColumn"]:last-child>div{width:auto!important;align-items:flex-end}
.st-key-sl_topbar [data-testid="stPopover"] button{border-radius:999px;font-weight:600;border:1px solid var(--linea)}
.sl-brand{font:700 22px/1 var(--display);color:var(--crema);padding:6px 0}
.sl-passo{font:600 13px/1 var(--testo);letter-spacing:.14em;text-transform:uppercase;color:var(--flag);margin:6px 0 2px}
iframe{border-radius:16px;border:1px solid var(--linea)!important;background:#f3f6ef}
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Illustrazioni: dove mettere il telefono (vista dall'alto)
# ---------------------------------------------------------------------------
def svg_posizione(vista: str, mancino: bool) -> str:
    # golfer al centro, linea del bersaglio orizzontale verso destra (destro)
    verso = -1 if mancino else 1
    cam = {"A": (160, 165), "B": (160, 25), "C": (160 - 120 * verso, 105)}[vista]
    freccia_x = 300 if verso > 0 else 20
    return f"""
<svg viewBox="0 0 320 190" width="100%" role="img" aria-label="Posizione del telefono">
  <rect x="0" y="0" width="320" height="190" rx="12" fill="#2f6b3f"/>
  <line x1="20" y1="105" x2="300" y2="105" stroke="#e9e3c9" stroke-dasharray="6 6" stroke-width="2"/>
  <polygon points="{freccia_x},105 {freccia_x - 12*verso},99 {freccia_x - 12*verso},111" fill="#e9e3c9"/>
  <text x="{freccia_x - 50*verso}" y="125" fill="#e9e3c9" font-size="11" text-anchor="middle">bersaglio</text>
  <circle cx="160" cy="105" r="5" fill="#fff"/>
  <ellipse cx="160" cy="72" rx="26" ry="13" fill="#d8d2c2"/>
  <circle cx="160" cy="72" r="9" fill="#8a7f6b"/>
  <text x="196" y="76" fill="#e9e3c9" font-size="11">golfer</text>
  <rect x="{cam[0]-9}" y="{cam[1]-14}" width="18" height="28" rx="4" fill="#ffd25e" stroke="#1d2420"/>
  <text x="{cam[0]}" y="{cam[1] + (28 if cam[1] < 100 else -20) - (6 if vista == 'C' else 0)}"
        fill="#ffd25e" font-size="12" font-weight="700" text-anchor="middle">{vista}</text>
</svg>"""


ISTRUZIONI = {
    "A": "Davanti al golfer, all'altezza delle mani (circa 1 m), a 3–4 m di distanza. "
         "Telefono in verticale, perpendicolare alla linea del bersaglio, centrato sul petto.",
    "B": "Dalla parte opposta, alle spalle del golfer, alla stessa altezza e distanza della vista A. "
         "Utile come seconda vista laterale.",
    "C": "Dietro le mani, sulla linea che va dai piedi al bersaglio (non sulla linea della palla), "
         "a 3–4 m, all'altezza delle mani. Inquadra dalla testa ai piedi con spazio sopra.",
}


PIN_SVG = """
<svg class="pin" viewBox="0 0 120 160" aria-hidden="true">
  <ellipse cx="54" cy="150" rx="46" ry="9" fill="#0b2216" opacity=".55"/>
  <ellipse cx="54" cy="148" rx="14" ry="4" fill="#06140d"/>
  <rect x="52" y="14" width="4" height="134" rx="2" fill="#f1ecd9"/>
  <path d="M56 16 L108 32 L56 50 Z" fill="#f2c94c"/>
  <circle cx="84" cy="140" r="9" fill="#fff"/>
  <circle cx="81" cy="137" r="1.2" fill="#d7d7d7"/><circle cx="86" cy="138" r="1.2" fill="#d7d7d7"/>
  <circle cx="83" cy="142" r="1.2" fill="#d7d7d7"/><circle cx="88" cy="142" r="1.2" fill="#d7d7d7"/>
</svg>"""


def hero(titolo="SwingLab", eyebrow="Analisi dello swing · P1–P10",
         testo="Carica da 1 a 3 video dello stesso swing: ricevi punteggio, stima del volo e consigli del maestro.",
         numeri=True):
    stats = ("""<div class="stats"><span><b>23</b> metriche biomeccaniche</span><span><b>3</b> angolazioni</span>
  <span><b>120–240</b> fps consigliati</span></div>""" if numeri else "")
    st.markdown(f"""
<div class="sl-hero">
  <div class="eyebrow">{eyebrow}</div>
  <h1>{titolo}</h1>
  <p>{testo}</p>
  {stats}
  {PIN_SVG}
</div>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Archivio (utenti e swing) e navigazione
# home (accesso / registrazione) → menu → carica swing / storico
# ---------------------------------------------------------------------------
def _segreti():
    try:
        return dict(st.secrets)
    except Exception:            # nessun file secrets.toml: si usa il database locale
        return {}


@st.cache_resource(show_spinner=False)
def motore_db(url):
    return archivio.crea_motore(url)


URL_DB = archivio.url_database(_segreti())
DB = motore_db(URL_DB)
DB_PERMANENTE = archivio.e_permanente(URL_DB)

st.session_state.setdefault("pagina", "home")


def utente():
    return st.session_state.get("utente")


def vai(pagina):
    st.session_state["pagina"] = pagina
    st.rerun()


def crea_video_commento(ris, avanzamento=None):
    """Video rallentato con assi e commento; se qualcosa va storto l'analisi resta valida."""
    try:
        return video_commento.genera(ris, progress=avanzamento)
    except Exception as exc:
        st.warning(f"Video commentato non disponibile: {exc}")
        return None


def mostra_video(video_bytes, chiave):
    if not video_bytes:
        return
    st.subheader("Il tuo swing commentato")
    st.caption("Circa 20 secondi in 4 tappe: Start, Back, Impatto, Finish. Gli assi sono verdi quando "
               "va bene, gialli per un errore lieve, rossi per un errore marcato; la linea arancione "
               "tratteggiata è la tua posizione di partenza.")
    sx, _ = st.columns([1, 1])
    with sx:
        st.video(video_bytes, format="video/mp4")
        st.download_button("Scarica il video (MP4)", video_bytes, file_name="swinglab_swing_commentato.mp4",
                           mime="video/mp4", key=f"scarica_video_{chiave}")


def salva_nello_storico(ris, html_report, dimostrativo=False, video=None, nome=None):
    u = utente()
    if not u:
        return
    try:
        archivio.salva_swing(DB, u["id"], ris, html_report, video, dimostrativo, nome=nome)
        st.toast("Swing salvato nel tuo storico")
    except Exception as exc:
        st.warning(f"Analisi completata, ma non sono riuscito a salvarla nello storico: {exc}")


def barra_superiore():
    """In alto: a sinistra il ritorno al menu; a destra la pallina da golf che apre il menu
    dell'app (resta fissa nell'angolo anche quando si scorre la pagina)."""
    pagina = st.session_state["pagina"]
    with st.container(key="sl_topbar"):
        if pagina != "menu":
            if st.button("← Menu", key=f"indietro_{pagina}"):
                vai("menu")
        else:
            st.markdown("<div class='sl-brand'>SwingLab</div>", unsafe_allow_html=True)
    with st.container(key="sl_menu"):
        with st.popover("Menu", use_container_width=False):
            u = utente()
            st.markdown(f"**{u['nome']}**  \n<span style='opacity:.75'>{u['email']}</span>",
                        unsafe_allow_html=True)
            for etichetta, dest in (("Profilo", "profilo"), ("Impostazioni", "impostazioni"),
                                    ("Storico swing", "storico"), ("Menu principale", "menu")):
                if st.button(etichetta, key=f"menu_{dest}_{pagina}", use_container_width=True,
                             disabled=pagina == dest):
                    vai(dest)
            if st.button("Esci", key=f"menu_esci_{pagina}", use_container_width=True):
                esci()


def file_temporaneo(f):
    """Copia su disco del video caricato (serve per anteprime e taglio). Una per file."""
    cache = st.session_state.setdefault("upload_tmp", {})
    voce = cache.get(f.file_id)
    if voce and os.path.exists(voce):
        return voce
    cartella = st.session_state.get("upload_dir")
    if not cartella or not os.path.isdir(cartella):
        cartella = tempfile.mkdtemp(prefix="swinglab_up_")
        st.session_state["upload_dir"] = cartella
    path = os.path.join(cartella, f"{f.file_id}{os.path.splitext(f.name)[1].lower()}")
    with open(path, "wb") as out:
        out.write(f.getbuffer())
    cache[f.file_id] = path
    return path


def pulisci_upload():
    """Cancella le copie temporanee dei video caricati."""
    import shutil
    cartella = st.session_state.pop("upload_dir", None)
    st.session_state.pop("upload_tmp", None)
    if cartella:
        shutil.rmtree(cartella, ignore_errors=True)


def editor_taglio(v, f):
    """Taglio di durata e inquadratura di un video. Restituisce (inizio, fine, ritaglio)."""
    path = file_temporaneo(f)
    inf = taglio.info(path)
    dur = max(0.1, round(inf["durata"], 1))
    k = f"{v}_{f.file_id}"
    t0, t1 = st.session_state.get(f"tempo_{k}", (0.0, dur))
    x = st.session_state.get(f"largh_{k}", (0, 100))
    y = st.session_state.get(f"alt_{k}", (0, 100))
    tagliato = not taglio.intero(t0, t1, dur, (x[0] / 100, x[1] / 100, y[0] / 100, y[1] / 100))
    riassunto = (f"{t1 - t0:.1f} s su {dur:.1f} s" + (" · inquadratura ritagliata" if (x, y) != ((0, 100), (0, 100)) else "")
                 if tagliato else f"video intero · {dur:.1f} s")
    with st.expander(f"✂ Taglia il video {v} — {riassunto}", expanded=dur > 15):
        if dur > 15:
            st.info("Il video è lungo: tieni solo lo swing, da 1-2 secondi prima del takeaway "
                    "a 1-2 secondi dopo il finish.")
        sx, dx = st.columns([1.1, 1], gap="large")
        with sx:
            t0, t1 = st.slider("Parte da analizzare (secondi)", 0.0, dur, (0.0, dur), step=0.1,
                               key=f"tempo_{k}")
            x = st.slider("Inquadratura in larghezza (%)", 0, 100, (0, 100), step=1, key=f"largh_{k}",
                          help="Togli i bordi a sinistra e a destra: il golfer deve restare tutto dentro.")
            y = st.slider("Inquadratura in altezza (%)", 0, 100, (0, 100), step=1, key=f"alt_{k}",
                          help="Lascia spazio sopra la testa per il bastone al top e sotto i piedi.")
            if x[1] - x[0] < 15 or y[1] - y[0] < 15:
                st.warning("Inquadratura troppo stretta: allargala un po'.")
            larg = int(inf["larghezza"] * (x[1] - x[0]) / 100)
            alt = int(inf["altezza"] * (y[1] - y[0]) / 100)
            st.caption(f"Risultato: {t1 - t0:.1f} s · {larg}×{alt} px "
                       f"(originale {dur:.1f} s · {inf['larghezza']}×{inf['altezza']} px, "
                       f"{f.size / 1e6:.0f} MB)")
        with dx:
            rit = (x[0] / 100, x[1] / 100, y[0] / 100, y[1] / 100)
            c1, c2 = st.columns(2)
            img = taglio.anteprima(path, t0, rit, 220)
            if img is not None:
                c1.image(img, caption=f"Inizio · {t0:.1f} s", use_container_width=True)
            img = taglio.anteprima(path, max(t0, t1 - 0.05), rit, 220)
            if img is not None:
                c2.image(img, caption=f"Fine · {t1:.1f} s", use_container_width=True)
    return t0, t1, (x[0] / 100, x[1] / 100, y[0] / 100, y[1] / 100)


def esci():
    pulisci_upload()
    st.session_state.clear()
    st.session_state["pagina"] = "home"
    st.rerun()


def preferenze():
    return dict(utente().get("profilo") or {})


def salva_preferenze(nuove):
    u = utente()
    archivio.salva_profilo(DB, u["id"], nuove)
    u["profilo"] = nuove


def _entra(u):
    st.session_state["utente"] = u
    for k in ("report", "video", "storico_aperto", "login_password", "reg_password", "reg_password2"):
        st.session_state.pop(k, None)
    vai("menu")


def pagina_home():
    hero(eyebrow="Benvenuto", titolo="Il tuo maestro di swing, in tasca",
         testo="SwingLab analizza i video del tuo swing e ti dice cosa va bene, cosa migliorare "
               "e quali esercizi fare. Accedi per ritrovare il tuo profilo e i tuoi swing.")
    sx, dx = st.columns([1, 1.15], gap="large")
    with sx:
        t_accedi, t_registra = st.tabs(["Accedi", "Crea account"])
        with t_accedi:
            with st.form("login"):
                st.text_input("Email", key="login_email", placeholder="nome@email.it")
                st.text_input("Password", type="password", key="login_password")
                entra = st.form_submit_button("Accedi", type="primary", use_container_width=True)
            if entra:
                try:
                    _entra(archivio.accedi(DB, st.session_state.get("login_email", ""),
                                           st.session_state.get("login_password", "")))
                except archivio.ErroreAccount as e:
                    st.error(str(e))
            st.caption("Prima volta? Apri la scheda \"Crea account\".")
        with t_registra:
            with st.form("registrazione"):
                st.text_input("Nome", key="reg_nome", placeholder="Come vuoi essere chiamato")
                st.text_input("Email", key="reg_email", placeholder="nome@email.it")
                st.text_input(f"Password (almeno {archivio.PASSWORD_MIN} caratteri)", type="password",
                              key="reg_password")
                st.text_input("Ripeti la password", type="password", key="reg_password2")
                ok_privacy = st.checkbox("Accetto che i miei swing (report e video commentato) vengano "
                                         "salvati nel mio account. Posso cancellarli quando voglio.",
                                         key="reg_privacy")
                crea = st.form_submit_button("Crea account", type="primary", use_container_width=True)
            if crea:
                ss = st.session_state
                if ss.get("reg_password") != ss.get("reg_password2"):
                    st.error("Le due password non coincidono.")
                elif not ok_privacy:
                    st.error("Per salvare i tuoi swing serve il consenso qui sopra.")
                else:
                    try:
                        _entra(archivio.registra(DB, ss.get("reg_email", ""), ss.get("reg_password", ""),
                                                 ss.get("reg_nome", "")))
                    except archivio.ErroreAccount as e:
                        st.error(str(e))
    with dx:
        st.markdown("""
<div class="sl-card">
  <h3>Come funziona</h3>
  <ol class="sl-passi">
    <li><b>Riprendi</b> lo swing con il telefono, meglio in slow motion.</li>
    <li><b>Carica</b> da 1 a 3 video: laterale, lato opposto, da dietro.</li>
    <li><b>Ricevi</b> punteggio, stima del volo della palla e un piano di allenamento.</li>
    <li><b>Ritrova</b> tutti i tuoi swing nello storico, ogni volta che accedi.</li>
  </ol>
</div>""", unsafe_allow_html=True)
        if not DB_PERMANENTE:
            st.caption("Nota: questa installazione usa un archivio locale (nessun database collegato).")


def pagina_menu():
    u = utente()
    barra_superiore()
    hero(eyebrow="Club house", titolo=f"Ciao {u['nome']}!", testo="Cosa vuoi fare oggi?", numeri=False)
    n = archivio.conta_swing(DB, u["id"])
    sx, dx = st.columns(2, gap="large")
    with sx:
        st.markdown("""
<div class="sl-scelta"><div class="ico"><svg viewBox="0 0 40 40" width="34" height="34" aria-hidden="true"><circle cx="20" cy="16" r="11" fill="#fff"/><g fill="#d6d6d6"><circle cx="16" cy="12" r="1.3"/><circle cx="21" cy="11" r="1.3"/><circle cx="25" cy="15" r="1.3"/><circle cx="18" cy="17" r="1.3"/><circle cx="23" cy="20" r="1.3"/><circle cx="15" cy="21" r="1.3"/></g><path d="M15 27h10l-3 4v6h-4v-6z" fill="#f2c94c"/></svg></div><h3>Carica nuovo swing</h3>
<p>Carica da 1 a 3 video e ricevi punteggio, dati di volo stimati e consigli.</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Carica nuovo swing", type="primary", use_container_width=True, key="vai_carica"):
            st.session_state.pop("report", None)
            st.session_state.pop("video", None)
            vai("analisi")
    with dx:
        st.markdown(f"""
<div class="sl-scelta"><div class="ico"><svg viewBox="0 0 40 40" width="34" height="34" aria-hidden="true"><rect x="7" y="5" width="26" height="31" rx="3" fill="#f1ecd9"/><g stroke="#1f5a3c" stroke-width="2"><line x1="12" y1="13" x2="28" y2="13"/><line x1="12" y1="19" x2="28" y2="19"/><line x1="12" y1="25" x2="22" y2="25"/></g><circle cx="27" cy="27" r="5" fill="#f2c94c"/></svg></div><h3>Storico dei tuoi swing</h3>
<p>{n} swing salvat{'o' if n == 1 else 'i'} nel tuo account. Rivedi report, video e punteggi.</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Storico dei tuoi swing", use_container_width=True, key="vai_storico"):
            vai("storico")

def pagina_profilo():
    u = utente()
    barra_superiore()
    hero(eyebrow="Account", titolo="Profilo", testo=f"Connesso come {u['email']}", numeri=False)
    sx, dx = st.columns(2, gap="large")
    with sx:
        with st.form("cambia_nome"):
            st.markdown("<h3 style='margin-top:0'>Nome</h3>", unsafe_allow_html=True)
            nuovo = st.text_input("Nome", value=u["nome"], key="prof_nome")
            if st.form_submit_button("Salva il nome", type="primary"):
                try:
                    u["nome"] = archivio.cambia_nome(DB, u["id"], nuovo)
                    st.success("Nome aggiornato.")
                except archivio.ErroreAccount as e:
                    st.error(str(e))
    with dx:
        with st.form("cambia_password", clear_on_submit=True):
            st.markdown("<h3 style='margin-top:0'>Password</h3>", unsafe_allow_html=True)
            att = st.text_input("Password attuale", type="password", key="prof_pw_att")
            nuova = st.text_input(f"Nuova password (almeno {archivio.PASSWORD_MIN} caratteri)",
                                  type="password", key="prof_pw_nuova")
            nuova2 = st.text_input("Ripeti la nuova password", type="password", key="prof_pw_nuova2")
            if st.form_submit_button("Cambia password", type="primary"):
                if nuova != nuova2:
                    st.error("Le due nuove password non coincidono.")
                else:
                    try:
                        archivio.cambia_password(DB, u["id"], att, nuova)
                        st.success("Password cambiata.")
                    except archivio.ErroreAccount as e:
                        st.error(str(e))
    st.write("")
    if st.button("Esci dal profilo", key="esci_profilo"):
        esci()
    with st.expander("Elimina account"):
        st.caption("Cancella definitivamente il profilo e tutti i tuoi swing. Non si può annullare.")
        conferma = st.checkbox("Sì, voglio eliminare il mio account e tutti i dati", key="conferma_elimina")
        if st.button("Elimina account", disabled=not conferma, key="elimina_account"):
            archivio.elimina_account(DB, u["id"])
            esci()


def pagina_impostazioni():
    barra_superiore()
    hero(eyebrow="Impostazioni", titolo="Il tuo gioco",
         testo="Servono a calibrare punteggio e stime. Valgono per tutti i prossimi swing.", numeri=False)
    pref = preferenze()
    with st.form("impostazioni"):
        mano = st.radio("Mano", ["Destro", "Mancino"], horizontal=True,
                        index=1 if pref.get("mancino") else 0, key="imp_mano")
        livello = st.radio("Livello", ["Ho un handicap", "Principiante (senza handicap)"],
                           index=1 if pref.get("principiante") else 0, key="imp_livello")
        hcp = st.number_input("Handicap (se ce l'hai)", min_value=0.0, max_value=54.0,
                              value=float(pref.get("handicap", 18.0)), step=0.1, key="imp_hcp")
        nota_alt = st.checkbox("Inserisco la mia statura (stime più precise)",
                               value=pref.get("altezza_cm", 178) is not None, key="imp_nota_alt")
        altezza = st.number_input("Statura (cm)", 140, 210, int(pref.get("altezza_cm") or 178), key="imp_alt")
        if st.form_submit_button("Salva impostazioni", type="primary"):
            pref.update(mancino=mano == "Mancino", principiante=livello.startswith("Principiante"),
                        handicap=hcp, altezza_cm=altezza if nota_alt else None)
            salva_preferenze(pref)
            st.success("Impostazioni salvate.")


def pagina_storico():
    u = utente()
    barra_superiore()
    hero(eyebrow="Scorecard", titolo="Storico dei tuoi swing",
         testo="Raggruppati per bastone, dal più recente.", numeri=False)
    elenco = archivio.elenco_swing(DB, u["id"])
    if not elenco:
        st.info("Non hai ancora analizzato nessuno swing. Torna al menu e scegli \"Carica nuovo swing\".")
        return
    ordine = list(C.BASTONI.keys())
    bastoni = sorted({s_["bastone"] for s_ in elenco}, key=lambda b_: ordine.index(b_) if b_ in ordine else 99)
    gruppi = [("Tutti", elenco)] + [(b_, [s_ for s_ in elenco if s_["bastone"] == b_]) for b_ in bastoni]
    schede = st.tabs([f"{nome} · {len(lista)}" for nome, lista in gruppi])
    for (nome, lista), scheda in zip(gruppi, schede):
        with scheda:
            if len(lista) >= 2:
                punti = [s_["punteggio"] for s_ in reversed(lista)]
                st.caption(f"Andamento del punteggio{'' if nome == 'Tutti' else ' con ' + nome}: "
                           f"da {punti[0]} a {punti[-1]} ({punti[-1] - punti[0]:+d}) in {len(punti)} swing.")
                st.line_chart({"Punteggio": punti}, height=150)
            for s_ in lista:
                _riga_storico(u, s_, nome)
    sid = st.session_state.get("storico_aperto")
    if sid is not None:
        dati = archivio.carica_swing(DB, u["id"], sid)
        if dati:
            quando = next((s_["quando"] for s_ in elenco if s_["id"] == sid), None)
            sel = next((s_ for s_ in elenco if s_["id"] == sid), {})
            st.subheader(sel.get("nome") or (f"Swing del {quando:%d/%m/%Y %H:%M}" if quando else "Swing"))
            mostra_video(dati["video"], f"storico_{sid}")
            st.download_button("Scarica il report (HTML)", dati["report"], file_name=f"swinglab_{sid}.html",
                               mime="text/html", key=f"scarica_{sid}")
            mostra_report(dati["report"])


def _riga_storico(u, s_, gruppo):
    sid = s_["id"]
    k = f"{gruppo}_{sid}"
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 1.4])
        c1.markdown(f"<div class='sl-voto'>{s_['punteggio']}<span>/100</span></div>", unsafe_allow_html=True)
        titolo = s_.get("nome") or f"{s_['bastone']} · {s_['quando']:%d/%m %H:%M}"
        c2.markdown(f"**{titolo}**  \n{s_['bastone']} · {s_['quando']:%d/%m/%Y %H:%M} · viste {s_['viste']}"
                    f"{' · dimostrativo' if s_['dimostrativo'] else ''}  \n"
                    f"Priorità: {s_['priorita']} · carry stimato {s_['carry']:.0f} m")
        if c3.button("Apri", key=f"apri_{k}", use_container_width=True):
            st.session_state["storico_aperto"] = sid
        with c3.popover("Rinomina", use_container_width=True):
            nuovo = st.text_input("Nuovo nome", value=s_.get("nome") or "", key=f"rin_txt_{k}", max_chars=80)
            if st.button("Salva", key=f"rin_ok_{k}", type="primary"):
                archivio.rinomina_swing(DB, u["id"], sid, nuovo)
                st.rerun()
        if c3.button("Elimina", key=f"elimina_{k}", use_container_width=True):
            archivio.elimina_swing(DB, u["id"], sid)
            if st.session_state.get("storico_aperto") == sid:
                st.session_state.pop("storico_aperto")
            st.rerun()


def mostra_report(html):
    if hasattr(st, "iframe"):          # Streamlit recenti
        st.iframe(html, height=1400)
    else:                              # versioni precedenti
        components.html(html, height=1400, scrolling=True)


def pagina_analisi():
    pref = preferenze()
    bastoni = list(C.BASTONI.keys())
    barra_superiore()
    hero()

    # 1. bastone usato per questo swing (si può cambiare a ogni caricamento)
    st.markdown("<div class='sl-passo'>Con che bastone hai tirato?</div>", unsafe_allow_html=True)
    cb, clm = st.columns([1, 1.4])
    with cb:
        bastone = st.selectbox("Bastone per questo swing", bastoni, key="bastone_swing",
                               index=bastoni.index(pref.get("bastone")) if pref.get("bastone") in bastoni
                               else bastoni.index("Ferro 7"))
    with clm:
        with st.expander("Dati di un launch monitor per questo colpo (facoltativo)"):
            st.caption("Se li hai, servono a confrontare e correggere le stime.")
            lm_club = st.number_input("Velocità bastone (km/h)", 0.0, 300.0, 0.0, step=1.0, key="lm_club")
            lm_ball = st.number_input("Velocità palla (km/h)", 0.0, 350.0, 0.0, step=1.0, key="lm_ball")
            lm_carry = st.number_input("Carry (m)", 0.0, 350.0, 0.0, step=1.0, key="lm_carry")
    nome_swing = st.text_input("Nome dello swing (facoltativo)", key="nome_swing", max_chars=80,
                               placeholder=f"es. {bastone} – campo pratica, lavoro sul backswing")
    mancino = bool(pref.get("mancino"))
    hcp = None if pref.get("principiante") else float(pref.get("handicap", 18.0))
    altezza = pref.get("altezza_cm", 178)
    st.caption(f"Impostazioni: {'mancino' if mancino else 'destro'} · "
               f"{'principiante' if hcp is None else f'handicap {hcp:g}'} · "
               f"{'statura ' + str(altezza) + ' cm' if altezza else 'statura non indicata'} "
               "(si cambiano da ☰ Menu › Impostazioni)")
    launch = {k: v for k, v in {
        "club_mph": lm_club / 1.609344 if lm_club else None,
        "ball_mph": lm_ball / 1.609344 if lm_ball else None,
        "carry_m": lm_carry or None}.items() if v}
    profilo = pipeline.Profilo(mancino=mancino, bastone=bastone, altezza_cm=altezza,
                               handicap=hcp, launch_monitor=launch)
    if pref.get("bastone") != bastone:          # ricorda l'ultimo bastone usato
        pref["bastone"] = bastone
        salva_preferenze(pref)

    tab_analisi, tab_guida, tab_privacy = st.tabs(["Analizza", "Come riprendere lo swing", "Privacy e limiti"])

    # ---------------------------------------------------------------------------
    with tab_guida:
        st.subheader("Posiziona il telefono così")
        cols = st.columns(3)
        for col, v in zip(cols, ("A", "B", "C")):
            with col:
                st.markdown(f"<div class='sl-tee'><span class='bollo'>{v}</span>{C.VISTE[v]['nome']}</div>",
                            unsafe_allow_html=True)
                st.markdown(svg_posizione(v, mancino), unsafe_allow_html=True)
                st.markdown(f"<div class='guida'>{ISTRUZIONI[v]}</div>", unsafe_allow_html=True)
        st.markdown("""
    **Regole per tutte le angolazioni**
    - Usa lo **slow motion a 120 o 240 fps** (iPhone: Impostazioni › Fotocamera › Registra slow‑motion).
    - Telefono **fermo** su treppiede o appoggiato, mai in mano.
    - Golfer **intero** nell'inquadratura, dalla testa ai piedi, con spazio sopra per il bastone al top.
    - **Luce** abbondante, sfondo il più possibile uniforme, palla visibile a terra.
    - Video brevi: inizia 1–2 s prima dello swing e fermati 1–2 s dopo il finish (massimo 15 s).
    - Se riprendi più angolazioni insieme, usa più telefoni sullo **stesso swing**: l'app li allinea sull'impatto.
    """)

    with tab_privacy:
        st.markdown("""
    **Dove finiscono i tuoi video.**
    - **Se usi l'app dal link online** (Streamlit Community Cloud): il video viene caricato sul server che
      ospita l'app, copiato in una cartella temporanea, analizzato e **cancellato subito dopo** la generazione
      del report. Non viene salvato né riutilizzato. Il server è gestito da Snowflake, con sede negli Stati Uniti.
    - **Se usi l'app sul tuo PC** (`localhost`): il video non lascia mai il computer.

    **Cosa resta nel tuo account.** Per ogni swing: punteggio, dati principali, il report e il video
    commentato (che contiene fotogrammi del tuo swing). Restano finché non li elimini dallo storico; da
    *Menu › Account* puoi cancellare l'account e tutti i dati. La password non viene mai salvata: si
    conserva solo un'impronta cifrata (PBKDF2), da cui non si può risalire alla password.

    L'unico download esterno è il modello di posa di MediaPipe, dai server di Google. Il report
    scaricabile contiene fotogrammi del video: conservalo e condividilo come faresti con una tua foto.
    Le statistiche d'uso di Streamlit sono disattivate nel file `.streamlit/config.toml`.
    Non caricare video di altre persone senza il loro consenso (per i minori serve quello dei genitori).

    **Cosa l'app non può misurare da un video del telefono.** Faccia del bastone all'impatto, punto di
    contatto sulla faccia, spin e lancio reali, volo della palla. Per questo velocità, distanza e
    direzione sono **stime con un intervallo**, mai misure. Le metriche 3D (rotazioni, sequenza) arrivano
    da un modello che stima la profondità da una sola telecamera: trattale come indicazioni.
    """)

    # ---------------------------------------------------------------------------
    with tab_analisi:
        cols = st.columns(3)
        caricati, fps_manuali = {}, {}
        for col, v in zip(cols, ("A", "B", "C")):
            with col:
                st.markdown(f"<div class='sl-tee'><span class='bollo'>{v}</span>{C.VISTE[v]['nome']}</div>",
                            unsafe_allow_html=True)
                f = st.file_uploader(f"Video {v}", type=["mp4", "mov"], key=f"up_{v}",
                                     label_visibility="collapsed")
                if f:
                    caricati[v] = f
                    fps = st.number_input("Frame rate reale (0 = automatico)", 0, 960, 0, key=f"fps_{v}",
                                          help="Se il video slow motion è stato esportato a 30 fps, "
                                               "indica qui il frame rate reale di ripresa (es. 240).")
                    fps_manuali[v] = fps or None

        tagli = {}
        if caricati:
            st.markdown("<div class='sl-passo'>Taglia i video (facoltativo)</div>", unsafe_allow_html=True)
            for v, f in caricati.items():
                tagli[v] = editor_taglio(v, f)
        if caricati and len(caricati) < 3:
            st.warning(pipeline.AVVISO_PRECISIONE[len(caricati)])
        if caricati:
            mancanti = pipeline.analisi_mancanti(caricati.keys())
            for nome, cosa in mancanti:
                st.info(f"Senza la vista **{nome}** non posso calcolare: {cosa.lower()}.")

        st.caption("Caricando un video confermi di essere la persona ripresa o di avere il suo consenso. "
                   "Il video originale viene cancellato a fine analisi; nel tuo account restano il report "
                   "e il video commentato, che puoi eliminare dallo storico.")
        c1, c2 = st.columns([1, 1])
        vai = c1.button("Analizza lo swing", type="primary", disabled=not caricati)
        prova = c2.button("Prova con uno swing dimostrativo")

        if prova:
            with st.spinner("Analizzo lo swing dimostrativo…"):
                tr = demo.tracce(("A", "C"))
                ris = pipeline.analizza_tracce(tr, profilo)
                nome = nome_swing.strip() or "Swing dimostrativo"
                st.session_state["report"] = report.genera(ris, dimostrativo=True, nome_swing=nome)
                st.session_state["nome_report"] = "swinglab_report_dimostrativo.html"
            with st.spinner("Preparo il video commentato…"):
                st.session_state["video"] = crea_video_commento(ris)
            salva_nello_storico(ris, st.session_state["report"], dimostrativo=True,
                                video=st.session_state["video"], nome=nome)

        if vai:
            barra = st.progress(0.0, text="Preparo i video…")
            def progress(msg, frac=None):
                barra.progress(min(1.0, frac or 0.0), text=msg)
            try:
                with tempfile.TemporaryDirectory(prefix="swinglab_") as tmp:
                    percorsi, errori = {}, False
                    avvisi = {}
                    for v, f in caricati.items():
                        orig = file_temporaneo(f)
                        t0, t1, rit = tagli[v]
                        if taglio.intero(t0, t1, taglio.info(orig)["durata"], rit):
                            path = orig
                        else:
                            progress(f"Taglio il video {v}…", 0.02)
                            path = os.path.join(tmp, f"video_{v}.mp4")
                            taglio.applica(orig, path, t0, t1, rit)
                        esito = V.valida_file(path, f.name, fps_manuali.get(v))
                        for e in esito["errori"]:
                            st.error(f"Video {v}: {e}")
                            errori = True
                        for a in esito["avvisi"]:
                            st.warning(f"Video {v}: {a}")
                        avvisi[v] = esito["avvisi"]
                        percorsi[v] = path
                    if not errori:
                        ris = pipeline.analizza_video(percorsi, profilo, fps_manuali, progress)
                        for v, av in avvisi.items():
                            ris["avvisi"].setdefault(v, [])[:0] = av
                        progress("Scrivo il report…", 1.0)
                        nome = nome_swing.strip() or f"{bastone} · {dt.datetime.now():%d/%m %H:%M}"
                        st.session_state["report"] = report.genera(ris, nome_swing=nome)
                        st.session_state["nome_report"] = "swinglab_report.html"
                        # il video va creato qui, finché i file originali esistono ancora
                        st.session_state["video"] = crea_video_commento(ris, progress)
                        salva_nello_storico(ris, st.session_state["report"], video=st.session_state["video"],
                                            nome=nome)
                # qui la cartella temporanea è già stata cancellata; poi anche le copie dei caricamenti
                pulisci_upload()
                barra.empty()
            except Exception as exc:  # messaggio comprensibile all'utente
                barra.empty()
                pulisci_upload()
                st.error(f"Analisi non riuscita: {exc}")

        if "report" in st.session_state:
            mostra_video(st.session_state.get("video"), "analisi")
            st.subheader("La tua analisi")
            st.download_button("Scarica il report (HTML)", st.session_state["report"],
                               file_name=st.session_state["nome_report"], mime="text/html")
            mostra_report(st.session_state["report"])



PAGINE = {"home": pagina_home, "menu": pagina_menu, "analisi": pagina_analisi, "storico": pagina_storico,
          "profilo": pagina_profilo, "impostazioni": pagina_impostazioni}
if not utente():
    st.session_state["pagina"] = "home"
PAGINE.get(st.session_state["pagina"], pagina_home)()
