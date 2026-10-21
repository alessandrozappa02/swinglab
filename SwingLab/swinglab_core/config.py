"""Costanti, tabelle di riferimento e pesi del punteggio.

Tutti i valori numerici di riferimento sono raccolti qui, così un maestro
può tararli senza toccare il resto del codice.
"""

# ---------------------------------------------------------------------------
# Vincoli di caricamento
# ---------------------------------------------------------------------------
FORMATI_AMMESSI = (".mp4", ".mov")
DURATA_MAX_S = 15.0          # durata reale consigliata dello swing
DURATA_MAX_FILE_S = 60.0     # un video slow motion esportato a 30 fps dura 4-8 volte di più
FRAME_MAX = 2400             # limite di fotogrammi per tenere l'analisi veloce
DIMENSIONE_MAX_MB = 200
FPS_MINIMO = 25
FPS_CONSIGLIATO = 120

# ---------------------------------------------------------------------------
# Angolazioni
# ---------------------------------------------------------------------------
VISTE = {
    "A": {"nome": "Laterale sinistro (face-on)", "tipo": "FO",
          "breve": "Face-on"},
    "B": {"nome": "Laterale destro (face-on dal lato opposto)", "tipo": "FO2",
          "breve": "Lato opposto"},
    "C": {"nome": "Da dietro (down-the-line)", "tipo": "DTL",
          "breve": "Down-the-line"},
}

# Indici dei landmark MediaPipe Pose (33 punti)
NASO = 0
SPALLA_SX, SPALLA_DX = 11, 12
GOMITO_SX, GOMITO_DX = 13, 14
POLSO_SX, POLSO_DX = 15, 16
INDICE_SX, INDICE_DX = 19, 20
ANCA_SX, ANCA_DX = 23, 24
GINOCCHIO_SX, GINOCCHIO_DX = 25, 26
CAVIGLIA_SX, CAVIGLIA_DX = 27, 28
TALLONE_SX, TALLONE_DX = 29, 30
PUNTA_SX, PUNTA_DX = 31, 32

# Collegamenti per disegnare lo scheletro
SCHELETRO = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (15, 19), (16, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
    (27, 29), (29, 31), (27, 31), (28, 30), (30, 32), (28, 32),
]

# Proporzioni antropometriche (Drillis & Contini): tronco + coscia + gamba
# ≈ 0,78 × statura. Servono a convertire i pixel in centimetri.
FRAZIONE_SEGMENTI_ALTEZZA = 0.78
ALTEZZA_DEFAULT_M = 1.75

# ---------------------------------------------------------------------------
# Bastoni: rapporto di velocità rispetto al driver, smash factor tipico
# amatoriale, lancio e spin di riferimento, rotolo, fattore mani→testa.
# Fonti: medie TrackMan PGA Tour 2023-24 (driver 115 mph / 171 mph / 282 yd;
# ferro 7: 92 / 123 / 176 yd), TrackMan Combine (golfista medio hcp 14,5:
# 94 mph club speed, 133 mph ball speed), TrackMan Optimizer (driver a
# 94 mph → 13,6° di lancio; PW a 72 mph → 26,7°).
# ---------------------------------------------------------------------------
BASTONI = {
    #  nome          v/driver smash lancio  spin  rotolo k_mani
    "Driver":      (1.00, 1.45, 13.0, 2900, 0.10, 4.6),
    "Legno 3":     (0.94, 1.44, 11.5, 3700, 0.06, 4.4),
    "Legno 5":     (0.91, 1.43, 12.5, 4200, 0.05, 4.3),
    "Ibrido":      (0.89, 1.41, 13.0, 4500, 0.04, 4.2),
    "Ferro 3":     (0.87, 1.40, 12.5, 4600, 0.035, 4.1),
    "Ferro 4":     (0.855, 1.39, 13.5, 5000, 0.03, 4.0),
    "Ferro 5":     (0.835, 1.37, 14.5, 5400, 0.025, 4.0),
    "Ferro 6":     (0.82, 1.35, 16.0, 6200, 0.02, 3.9),
    "Ferro 7":     (0.80, 1.33, 17.5, 7000, 0.02, 3.8),
    "Ferro 8":     (0.785, 1.30, 19.5, 7800, 0.015, 3.7),
    "Ferro 9":     (0.77, 1.27, 21.5, 8500, 0.015, 3.6),
    "PW":          (0.75, 1.24, 24.0, 9000, 0.01, 3.5),
    "Wedge (GW/SW/LW)": (0.70, 1.15, 29.0, 9800, 0.005, 3.4),
}

# Velocità del driver attesa per livello (mph): retta che passa per
# hcp 14,5 → 94 mph (TrackMan Combine) e scende di ~0,62 mph per colpo.
def driver_mph_atteso(handicap: float) -> float:
    return max(60.0, 103.0 - 0.62 * handicap)

DEV_STD_PRIOR_MPH = 10.0

# Incertezza relativa (1 dev. std.) della velocità mani→testa dal video
INCERTEZZA_VIDEO_PER_FPS = [(240, 0.10), (120, 0.12), (60, 0.18), (0, 0.25)]

# ---------------------------------------------------------------------------
# Livelli di gioco e tolleranza del punteggio
# ---------------------------------------------------------------------------
def livello_da_handicap(hcp):
    if hcp is None:
        return "Principiante", 1.7
    if hcp <= 5:
        return "Avanzato (hcp 0-5)", 1.0
    if hcp <= 15:
        return "Intermedio (hcp 6-15)", 1.2
    if hcp <= 28:
        return "Amatore (hcp 16-28)", 1.4
    return "In crescita (hcp 29-54)", 1.6

# ---------------------------------------------------------------------------
# Categorie del punteggio e pesi (somma 100)
# ---------------------------------------------------------------------------
CATEGORIE = {
    "Setup": 15,
    "Backswing": 20,
    "Transizione": 15,
    "Impatto": 25,
    "Finish": 10,
    "Tempo": 15,
}

# Ogni metrica: categoria, peso nella categoria, banda ideale [lo, hi],
# tolleranza (quanto oltre la banda il punteggio arriva a 0, per un giocatore
# avanzato), viste da cui si calcola, unità, etichetta.
METRICHE = {
    # --- Setup -------------------------------------------------------------
    "inclinazione_busto": dict(cat="Setup", peso=3, ideale=(30, 45), tol=15,
        viste=("DTL",), unita="°", nome="Inclinazione del busto al setup"),
    "flessione_ginocchia": dict(cat="Setup", peso=2, ideale=(15, 30), tol=15,
        viste=("DTL",), unita="°", nome="Flessione delle ginocchia al setup"),
    "distanza_palla": dict(cat="Setup", peso=2, ideale=(0, 14), tol=15,
        viste=("DTL",), unita="cm", nome="Mani rispetto alle spalle (distanza dalla palla)"),
    "larghezza_stance": dict(cat="Setup", peso=2, ideale=(0.95, 1.35), tol=0.35,
        viste=("FO", "FO2"), unita="× spalle", nome="Larghezza dei piedi"),
    "tilt_setup": dict(cat="Setup", peso=1, ideale=(2, 12), tol=10,
        viste=("FO", "FO2"), unita="°", nome="Inclinazione laterale della colonna al setup"),
    # --- Backswing ---------------------------------------------------------
    "rotazione_spalle": dict(cat="Backswing", peso=3, ideale=(80, 105), tol=30,
        viste=("FO", "FO2", "DTL"), unita="°", nome="Rotazione delle spalle al top"),
    "rotazione_bacino": dict(cat="Backswing", peso=2, ideale=(35, 55), tol=25,
        viste=("FO", "FO2", "DTL"), unita="°", nome="Rotazione del bacino al top"),
    "x_factor": dict(cat="Backswing", peso=2, ideale=(35, 55), tol=25,
        viste=("FO", "FO2", "DTL"), unita="°", nome="X-factor (spalle − bacino)"),
    "sway": dict(cat="Backswing", peso=3, ideale=(-3, 5), tol=12,
        viste=("FO", "FO2"), unita="cm", nome="Sway del bacino nel backswing"),
    "testa_backswing": dict(cat="Backswing", peso=2, ideale=(-4, 6), tol=12,
        viste=("FO", "FO2"), unita="cm", nome="Spostamento laterale della testa al top"),
    "braccio_guida_top": dict(cat="Backswing", peso=2, ideale=(160, 180), tol=35,
        viste=("FO", "FO2"), unita="°", nome="Angolo del braccio guida al top"),
    # --- Transizione -------------------------------------------------------
    "over_the_top": dict(cat="Transizione", peso=3, ideale=(-12, 2), tol=14,
        viste=("DTL",), unita="cm", nome="Percorso delle mani in discesa (over the top)"),
    "sequenza": dict(cat="Transizione", peso=3, ideale=(2, 2), tol=2,
        viste=("FO", "FO2", "DTL"), unita="/2", nome="Sequenza cinematica"),
    "lag": dict(cat="Transizione", peso=1, ideale=(60, 115), tol=55,
        viste=("FO", "FO2"), unita="%", nome="Angolo dei polsi mantenuto a metà discesa (lag, stima)"),
    # --- Impatto -----------------------------------------------------------
    "early_extension": dict(cat="Impatto", peso=4, ideale=(-6, 3), tol=12,
        viste=("DTL",), unita="cm", nome="Early extension (bacino verso la palla)"),
    "perdita_postura": dict(cat="Impatto", peso=2, ideale=(-5, 5), tol=12,
        viste=("DTL",), unita="°", nome="Variazione dell'inclinazione del busto all'impatto"),
    "testa_verticale": dict(cat="Impatto", peso=2, ideale=(-4, 4), tol=10,
        viste=("DTL",), unita="cm", nome="Movimento verticale della testa (setup→impatto)"),
    "peso_impatto": dict(cat="Impatto", peso=3, ideale=(0.58, 0.80), tol=0.30,
        viste=("FO", "FO2"), unita="", nome="Trasferimento del peso all'impatto (0=dietro, 1=avanti)"),
    "tilt_impatto": dict(cat="Impatto", peso=1, ideale=(15, 35), tol=15,
        viste=("FO", "FO2"), unita="°", nome="Inclinazione laterale della colonna all'impatto"),
    # --- Finish ------------------------------------------------------------
    "peso_finish": dict(cat="Finish", peso=2, ideale=(0.85, 1.15), tol=0.35,
        viste=("FO", "FO2"), unita="", nome="Peso sul piede avanti al finish"),
    "equilibrio": dict(cat="Finish", peso=2, ideale=(0, 3), tol=9,
        viste=("FO", "FO2", "DTL"), unita="cm", nome="Stabilità al finish (oscillazione)"),
    # --- Tempo -------------------------------------------------------------
    "rapporto_tempo": dict(cat="Tempo", peso=3, ideale=(2.7, 3.3), tol=1.4,
        viste=("FO", "FO2", "DTL"), unita=":1", nome="Rapporto backswing/downswing"),
    "durata_backswing": dict(cat="Tempo", peso=1, ideale=(0.70, 1.05), tol=0.45,
        viste=("FO", "FO2", "DTL"), unita="s", nome="Durata del backswing"),
}
