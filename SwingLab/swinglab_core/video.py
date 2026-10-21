"""Validazione dei video, lettura dei fotogrammi e controlli di qualità."""
from __future__ import annotations

import os
import cv2
import numpy as np

from . import config as C


def apri(path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Impossibile aprire il video")
    return cap


def info_video(path, fps_manuale: float | None = None) -> dict:
    cap = apri(path)
    fps_meta = cap.get(cv2.CAP_PROP_FPS) or 0.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    fps = float(fps_manuale) if fps_manuale else float(fps_meta)
    durata = n / fps_meta if fps_meta > 0 else 0.0  # durata reale del file
    return dict(fps=fps, fps_metadati=fps_meta, frames=n, larghezza=w,
                altezza=h, durata=durata)


def valida_file(path, nome_file: str, fps_manuale: float | None = None) -> dict:
    """Controlli bloccanti (errori) e non bloccanti (avvisi) sul file."""
    errori, avvisi = [], []
    ext = os.path.splitext(nome_file)[1].lower()
    if ext not in C.FORMATI_AMMESSI:
        errori.append(f"Formato {ext or 'sconosciuto'} non supportato: usa mp4 o mov.")
    size_mb = os.path.getsize(path) / 1e6
    if size_mb > C.DIMENSIONE_MAX_MB:
        errori.append(f"Il file pesa {size_mb:.0f} MB (massimo {C.DIMENSIONE_MAX_MB} MB).")
    try:
        info = info_video(path, fps_manuale)
    except ValueError:
        return dict(ok=False, errori=errori + ["Il file non è un video leggibile."],
                    avvisi=avvisi, info={})
    if info["frames"] < 10:
        errori.append("Il video è troppo corto o danneggiato.")
    if info["durata"] > C.DURATA_MAX_S:
        errori.append(f"Il video dura {info['durata']:.1f} s (massimo {C.DURATA_MAX_S:.0f} s). "
                      "Taglialo intorno allo swing.")
    if info["fps"] < C.FPS_MINIMO:
        errori.append(f"Frame rate troppo basso ({info['fps']:.0f} fps).")
    elif info["fps"] < 100:
        avvisi.append(f"Video a {info['fps']:.0f} fps: le fasi veloci (impatto, velocità) "
                      "saranno meno precise. Meglio lo slow motion a 120 o 240 fps.")
    if min(info["larghezza"], info["altezza"]) < 360:
        avvisi.append("Risoluzione bassa: i punti del corpo saranno meno precisi.")

    if not errori:
        avvisi += controlli_qualita(path, info)
    return dict(ok=not errori, errori=errori, avvisi=avvisi, info=info)


def controlli_qualita(path, info) -> list[str]:
    """Luce e stabilità del telefono su un campione di fotogrammi."""
    avvisi = []
    cap = apri(path)
    n = info["frames"]
    idx = np.linspace(0, max(n - 1, 0), num=min(12, n)).astype(int)
    grigi, luci = [], []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(cv2.resize(f, (320, int(320 * f.shape[0] / f.shape[1]))),
                         cv2.COLOR_BGR2GRAY)
        grigi.append(g.astype(np.float32))
        luci.append(float(g.mean()))
    cap.release()
    if luci and np.median(luci) < 60:
        avvisi.append("Il video è buio: cerca più luce o riprendi all'aperto.")
    if len(grigi) >= 3:
        spost = []
        for g in grigi[1:]:
            (dx, dy), _ = cv2.phaseCorrelate(grigi[0], g)
            spost.append(np.hypot(dx, dy) / grigi[0].shape[1])
        if np.median(spost) > 0.02:
            avvisi.append("Sembra che il telefono si muova: usa un treppiede o appoggialo fermo.")
    return avvisi


def controlli_inquadratura(kp: np.ndarray, vis: np.ndarray, w: int, h: int,
                           i_setup: int) -> list[str]:
    """Dopo la stima della posa: golfer intero nell'inquadratura."""
    avvisi = []
    punti = [C.NASO, C.CAVIGLIA_SX, C.CAVIGLIA_DX, C.POLSO_SX, C.POLSO_DX]
    v = vis[i_setup, punti]
    xy = kp[i_setup, punti]
    fuori = (xy[:, 0] < 0.01 * w) | (xy[:, 0] > 0.99 * w) | \
            (xy[:, 1] < 0.01 * h) | (xy[:, 1] > 0.99 * h)
    if (v < 0.5).any() or fuori.any():
        avvisi.append("Il golfer non è interamente visibile al setup (testa, mani e piedi "
                      "devono stare nell'inquadratura).")
    alto = np.nanmax(kp[:, :, 1]) - np.nanmin(kp[:, :, 1])
    if alto < 0.35 * h:
        avvisi.append("Il golfer appare piccolo: avvicina il telefono (deve occupare "
                      "almeno metà dell'altezza dell'immagine).")
    return avvisi


def cerca_palla(frame: np.ndarray, kp_setup: np.ndarray) -> bool:
    """Cerca un piccolo cerchio chiaro vicino ai piedi. Euristica: serve solo
    come avviso, non blocca l'analisi."""
    h, w = frame.shape[:2]
    piedi = kp_setup[[C.CAVIGLIA_SX, C.CAVIGLIA_DX, C.PUNTA_SX, C.PUNTA_DX]]
    if np.isnan(piedi).any():
        return False
    cx, cy = np.mean(piedi[:, 0]), np.max(piedi[:, 1])
    larg = max(int(0.4 * w), int(abs(piedi[0, 0] - piedi[1, 0]) * 1.6))
    x0, x1 = int(max(0, cx - larg)), int(min(w, cx + larg))
    y0, y1 = int(max(0, cy - 0.12 * h)), int(min(h, cy + 0.08 * h))
    roi = frame[y0:y1, x0:x1]
    if roi.size == 0:
        return False
    g = cv2.GaussianBlur(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    r_max = max(6, int(0.02 * h))
    cerchi = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=10, param1=80,
                              param2=14, minRadius=2, maxRadius=r_max)
    if cerchi is None:
        return False
    for x, y, r in cerchi[0]:
        x, y, r = int(x), int(y), max(1, int(r))
        patch = g[max(0, y - r):y + r, max(0, x - r):x + r]
        if patch.size and patch.mean() > 150:
            return True
    return False


def leggi_frame(path, indice: int):
    cap = apri(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(indice))
    ok, f = cap.read()
    cap.release()
    return f if ok else None


def itera_frame(path, lato_max: int = 960):
    """Restituisce (indice, frame_rgb_ridimensionato, scala)."""
    cap = apri(path)
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        h, w = f.shape[:2]
        s = min(1.0, lato_max / max(h, w))
        if s < 1.0:
            f = cv2.resize(f, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        yield i, cv2.cvtColor(f, cv2.COLOR_BGR2RGB), s
        i += 1
    cap.release()
