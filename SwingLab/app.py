"""SwingLab – interfaccia web locale (Streamlit).

Avvio:  python -m streamlit run app.py
"""
from __future__ import annotations

import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components

from swinglab_core import config as C
from swinglab_core import demo, pipeline, report, video_commento
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
# Navigazione: home (benvenuto + login) → menu → carica swing / storico
# ---------------------------------------------------------------------------
st.session_state.setdefault("pagina", "home")
st.session_state.setdefault("storico", [])


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
    st.caption("Rallentatore con gli assi del corpo: le linee bianche segnano dove eri al setup, "
               "in rosso quello che va corretto.")
    sx, _ = st.columns([1, 1])
    with sx:
        st.video(video_bytes, format="video/mp4")
        st.download_button("Scarica il video (MP4)", video_bytes, file_name="swinglab_swing_commentato.mp4",
                           mime="video/mp4", key=f"scarica_video_{chiave}")


def salva_nello_storico(ris, html_report, dimostrativo=False, video=None):
    import datetime as dt
    st.session_state["storico"].insert(0, dict(
        quando=dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
        punteggio=ris["punteggi"]["totale"],
        bastone=ris["profilo"].bastone,
        viste=", ".join(ris["tracce"].keys()),
        priorita=ris["difetti"][0]["titolo"] if ris["difetti"] else "Nessun difetto rilevante",
        carry=ris["volo"]["carry"]["m"],
        dimostrativo=dimostrativo,
        report=html_report,
        video=video,
    ))


def barra_indietro(etichetta="← Menu", dove="menu"):
    if st.button(etichetta, key=f"indietro_{st.session_state['pagina']}"):
        vai(dove)


def pagina_home():
    hero(eyebrow="Benvenuto", titolo="Il tuo maestro di swing, in tasca",
         testo="SwingLab analizza i video del tuo swing e ti dice cosa va bene, cosa migliorare "
               "e quali esercizi fare. Accedi per iniziare.")
    sx, dx = st.columns([1, 1.15], gap="large")
    with sx:
        with st.form("login"):
            st.markdown("<h3 style='margin-top:0'>Accedi</h3>", unsafe_allow_html=True)
            st.text_input("Email", key="login_email", placeholder="nome@email.it")
            st.text_input("Password", type="password", key="login_password")
            entra = st.form_submit_button("Accedi", type="primary", use_container_width=True)
            st.caption("Versione di prova: l'accesso non richiede ancora un account.")
        if entra:
            st.session_state["utente"] = (st.session_state.get("login_email") or "").split("@")[0]
            vai("menu")
    with dx:
        st.markdown("""
<div class="sl-card">
  <h3>Come funziona</h3>
  <ol class="sl-passi">
    <li><b>Riprendi</b> lo swing con il telefono, meglio in slow motion.</li>
    <li><b>Carica</b> da 1 a 3 video: laterale, lato opposto, da dietro.</li>
    <li><b>Ricevi</b> punteggio, stima del volo della palla e un piano di allenamento.</li>
  </ol>
</div>""", unsafe_allow_html=True)


def pagina_menu():
    nome = st.session_state.get("utente") or ""
    hero(eyebrow="Club house", titolo=f"Ciao{(' ' + nome) if nome else ''}!",
         testo="Cosa vuoi fare oggi?", numeri=False)
    n = len(st.session_state["storico"])
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
<p>{n} swing analizzat{'o' if n == 1 else 'i'} in questa sessione. Rivedi i report e i punteggi.</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Storico dei tuoi swing", use_container_width=True, key="vai_storico"):
            vai("storico")
    st.write("")
    if st.button("Esci", key="esci"):
        st.session_state.pop("utente", None)
        vai("home")


def pagina_storico():
    barra_indietro()
    hero(eyebrow="Scorecard", titolo="Storico dei tuoi swing",
         testo="I report che hai generato. Per ora restano finché la pagina è aperta: "
               "il salvataggio permanente arriverà con gli account.", numeri=False)
    storico = st.session_state["storico"]
    if not storico:
        st.info("Non hai ancora analizzato nessuno swing. Torna al menu e scegli \"Carica nuovo swing\".")
        return
    for i, s in enumerate(storico):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 1.4])
            c1.markdown(f"<div class='sl-voto'>{s['punteggio']}<span>/100</span></div>", unsafe_allow_html=True)
            c2.markdown(f"**{s['quando']}** · {s['bastone']} · viste {s['viste']}"
                        f"{' · dimostrativo' if s['dimostrativo'] else ''}  \n"
                        f"Priorità: {s['priorita']} · carry stimato {s['carry']:.0f} m")
            if c3.button("Apri report", key=f"apri_{i}", use_container_width=True):
                st.session_state["storico_aperto"] = i
            c3.download_button("Scarica", s["report"], file_name=f"swinglab_{i + 1}.html",
                               mime="text/html", key=f"scarica_{i}", use_container_width=True)
    j = st.session_state.get("storico_aperto")
    if j is not None and j < len(storico):
        st.subheader(f"Report del {storico[j]['quando']}")
        mostra_video(storico[j].get("video"), f"storico_{j}")
        mostra_report(storico[j]["report"])


def mostra_report(html):
    if hasattr(st, "iframe"):          # Streamlit recenti
        st.iframe(html, height=1400)
    else:                              # versioni precedenti
        components.html(html, height=1400, scrolling=True)


def pagina_analisi():
    # ---------------------------------------------------------------------------
    # Barra laterale: profilo
    # ---------------------------------------------------------------------------
    with st.sidebar:
        st.header("Il tuo profilo")
        mano = st.radio("Mano", ["Destro", "Mancino"], horizontal=True)
        bastone = st.selectbox("Bastone usato", list(C.BASTONI.keys()), index=list(C.BASTONI).index("Ferro 7"))
        livello = st.radio("Livello", ["Ho un handicap", "Principiante (senza handicap)"])
        hcp = None
        if livello == "Ho un handicap":
            hcp = st.number_input("Handicap", min_value=0.0, max_value=54.0, value=18.0, step=0.1)
        nota_alt = st.checkbox("Inserisco la mia statura (stime più precise)", value=True)
        altezza = st.number_input("Statura (cm)", 140, 210, 178) if nota_alt else None
        with st.expander("Dati di un launch monitor (facoltativo)"):
            st.caption("Se li hai, servono a confrontare e correggere le stime.")
            lm_club = st.number_input("Velocità bastone (km/h)", 0.0, 300.0, 0.0, step=1.0)
            lm_ball = st.number_input("Velocità palla (km/h)", 0.0, 350.0, 0.0, step=1.0)
            lm_carry = st.number_input("Carry (m)", 0.0, 350.0, 0.0, step=1.0)
        st.divider()
        st.caption("I video servono solo per l'analisi e vengono cancellati subito dopo: non li salviamo.")

    mancino = mano == "Mancino"
    launch = {k: v for k, v in {
        "club_mph": lm_club / 1.609344 if lm_club else None,
        "ball_mph": lm_ball / 1.609344 if lm_ball else None,
        "carry_m": lm_carry or None}.items() if v}
    profilo = pipeline.Profilo(mancino=mancino, bastone=bastone, altezza_cm=altezza,
                               handicap=hcp, launch_monitor=launch)

    barra_indietro()
    hero()
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

    In entrambi i casi l'unico download è il modello di posa di MediaPipe, dai server di Google. Il report
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

        if caricati and len(caricati) < 3:
            st.warning(pipeline.AVVISO_PRECISIONE[len(caricati)])
        if caricati:
            mancanti = pipeline.analisi_mancanti(caricati.keys())
            for nome, cosa in mancanti:
                st.info(f"Senza la vista **{nome}** non posso calcolare: {cosa.lower()}.")

        st.caption("Caricando un video confermi di essere la persona ripresa o di avere il suo consenso. "
                   "Il video viene cancellato a fine analisi.")
        c1, c2 = st.columns([1, 1])
        vai = c1.button("Analizza lo swing", type="primary", disabled=not caricati)
        prova = c2.button("Prova con uno swing dimostrativo")

        if prova:
            with st.spinner("Analizzo lo swing dimostrativo…"):
                tr = demo.tracce(("A", "C"))
                ris = pipeline.analizza_tracce(tr, profilo)
                st.session_state["report"] = report.genera(ris, dimostrativo=True)
                st.session_state["nome_report"] = "swinglab_report_dimostrativo.html"
            with st.spinner("Preparo il video commentato…"):
                st.session_state["video"] = crea_video_commento(ris)
            salva_nello_storico(ris, st.session_state["report"], dimostrativo=True,
                                video=st.session_state["video"])

        if vai:
            barra = st.progress(0.0, text="Preparo i video…")
            def progress(msg, frac=None):
                barra.progress(min(1.0, frac or 0.0), text=msg)
            try:
                with tempfile.TemporaryDirectory(prefix="swinglab_") as tmp:
                    percorsi, errori = {}, False
                    avvisi = {}
                    for v, f in caricati.items():
                        path = os.path.join(tmp, f"video_{v}{os.path.splitext(f.name)[1].lower()}")
                        with open(path, "wb") as out:
                            out.write(f.getbuffer())
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
                        st.session_state["report"] = report.genera(ris)
                        st.session_state["nome_report"] = "swinglab_report.html"
                        # il video va creato qui, finché i file originali esistono ancora
                        st.session_state["video"] = crea_video_commento(ris, progress)
                        salva_nello_storico(ris, st.session_state["report"], video=st.session_state["video"])
                # qui la cartella temporanea e i video sono già stati cancellati
                barra.empty()
            except Exception as exc:  # messaggio comprensibile all'utente
                barra.empty()
                st.error(f"Analisi non riuscita: {exc}")

        if "report" in st.session_state:
            mostra_video(st.session_state.get("video"), "analisi")
            st.subheader("Il report completo")
            st.download_button("Scarica il report (HTML)", st.session_state["report"],
                               file_name=st.session_state["nome_report"], mime="text/html")
            mostra_report(st.session_state["report"])



PAGINE = {"home": pagina_home, "menu": pagina_menu, "analisi": pagina_analisi, "storico": pagina_storico}
PAGINE.get(st.session_state["pagina"], pagina_home)()
