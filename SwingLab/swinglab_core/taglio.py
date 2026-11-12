"""Taglio dei video prima dell'analisi: durata (inizio-fine) e inquadratura.

Il ritaglio dell'inquadratura riduce anche il peso del file e velocizza
l'analisi; l'importante è lasciare dentro tutto il golfer (testa, mani,
piedi e spazio sopra per il bastone al top).
"""
from __future__ import annotations

import cv2
import numpy as np


def info(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return dict(fps=fps, frames=n, larghezza=w, altezza=h, durata=n / fps if fps else 0.0)


def _rettangolo(w, h, ritaglio):
    """ritaglio = (sinistra, destra, alto, basso) in frazioni 0-1 → pixel, lati pari."""
    x0, x1, y0, y1 = ritaglio
    a, b = int(round(x0 * w)), int(round(x1 * w))
    c, d = int(round(y0 * h)), int(round(y1 * h))
    b = a + max(16, (b - a) // 2 * 2)
    d = c + max(16, (d - c) // 2 * 2)
    return a, min(b, w), c, min(d, h)


def anteprima(path, secondi, ritaglio=(0, 1, 0, 1), larghezza=360):
    """Fotogramma (RGB) al tempo indicato, con la parte esclusa scurita."""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(np.clip(round(secondi * fps), 0, n - 1)))
    ok, f = cap.read()
    cap.release()
    if not ok:
        return None
    h, w = f.shape[:2]
    a, b, c, d = _rettangolo(w, h, ritaglio)
    scuro = (f * 0.3).astype(np.uint8)
    scuro[c:d, a:b] = f[c:d, a:b]
    cv2.rectangle(scuro, (a, c), (b - 1, d - 1), (76, 201, 242), max(2, w // 200))
    s = larghezza / w
    scuro = cv2.resize(scuro, (larghezza, int(h * s)), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(scuro, cv2.COLOR_BGR2RGB)


def applica(path_in, path_out, inizio_s, fine_s, ritaglio=(0, 1, 0, 1)) -> dict:
    """Scrive il video tagliato mantenendo il frame rate originale."""
    cap = cv2.VideoCapture(str(path_in))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    i0 = int(np.clip(round(inizio_s * fps), 0, max(0, n - 1)))
    i1 = int(np.clip(round(fine_s * fps), i0 + 1, n))
    a, b, c, d = _rettangolo(w, h, ritaglio)
    out = cv2.VideoWriter(str(path_out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (b - a, d - c))
    cap.set(cv2.CAP_PROP_POS_FRAMES, i0)
    scritti = 0
    for _ in range(i1 - i0):
        ok, f = cap.read()
        if not ok:
            break
        out.write(np.ascontiguousarray(f[c:d, a:b]))
        scritti += 1
    cap.release()
    out.release()
    return dict(fps=fps, frames=scritti, larghezza=b - a, altezza=d - c, durata=scritti / fps)


def intero(inizio_s, fine_s, durata, ritaglio):
    return inizio_s <= 0.01 and fine_s >= durata - 0.01 and tuple(ritaglio) == (0, 1, 0, 1)
