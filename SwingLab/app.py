"""SwingLab – interfaccia web locale (Streamlit).

Avvio:  python -m streamlit run app.py
"""
from __future__ import annotations

import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components

from swinglab_core import config as C
from swinglab_core import demo, pipeline, report
from swinglab_core import video as V

st.set_page_config(page_title="SwingLab", page_icon="⛳", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:2rem;max-width:1150px}
h1{font-family:Georgia,serif}
.guida{border:1px solid rgba(128,128,128,.25);border-radius:12px;padding:10px 12px;font-size:14px}
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
  <text x="160" y="50" fill="#e9e3c9" font-size="11" text-anchor="middle">golfer</text>
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

st.title("SwingLab")
st.caption("Carica da 1 a 3 video dello stesso swing: ricevi punteggio, stima del volo e consigli del maestro.")

tab_analisi, tab_guida, tab_privacy = st.tabs(["Analizza", "Come riprendere lo swing", "Privacy e limiti"])

# ---------------------------------------------------------------------------
with tab_guida:
    st.subheader("Posiziona il telefono così")
    cols = st.columns(3)
    for col, v in zip(cols, ("A", "B", "C")):
        with col:
            st.markdown(f"**{v} – {C.VISTE[v]['nome']}**")
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
            st.markdown(f"**Video {v} – {C.VISTE[v]['nome']}**")
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
            # qui la cartella temporanea e i video sono già stati cancellati
            barra.empty()
        except Exception as exc:  # messaggio comprensibile all'utente
            barra.empty()
            st.error(f"Analisi non riuscita: {exc}")

    if "report" in st.session_state:
        st.download_button("Scarica il report (HTML)", st.session_state["report"],
                           file_name=st.session_state["nome_report"], mime="text/html")
        if hasattr(st, "iframe"):          # Streamlit recenti
            st.iframe(st.session_state["report"], height=1400)
        else:                              # versioni precedenti
            components.html(st.session_state["report"], height=1400, scrolling=True)
