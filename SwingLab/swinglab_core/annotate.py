"""Fotogrammi annotati: scheletro, linee di riferimento, angoli."""
from __future__ import annotations

import base64

import cv2
import numpy as np

from . import config as C
from .metrics import lati, medio
from .phases import mani

BIANCO = (245, 245, 245)
VERDE = (90, 200, 120)
ARANCIO = (40, 130, 240)     # BGR
AZZURRO = (230, 160, 60)
GIALLO = (40, 210, 240)
NERO = (20, 20, 20)


def _p(x):
    return int(round(float(x[0]))), int(round(float(x[1])))


def _tratteggio(img, a, b, col, spess=2, passo=14):
    a, b = np.array(a, float), np.array(b, float)
    n = max(1, int(np.linalg.norm(b - a) / passo))
    for k in range(0, n, 2):
        p, q = a + (b - a) * k / n, a + (b - a) * min(k + 1, n) / n
        cv2.line(img, _p(p), _p(q), col, spess, cv2.LINE_AA)


def _testo(img, s, org, scala=None, col=BIANCO):
    h = img.shape[0]
    scala = scala or max(0.5, h / 1300)
    sp = max(1, int(scala * 2))
    x, y = int(org[0]), int(org[1])
    (tw, th), _ = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, scala, sp)
    x = min(max(4, x), img.shape[1] - tw - 4)
    y = min(max(th + 4, y), h - 4)
    cv2.rectangle(img, (x - 4, y - th - 6), (x + tw + 4, y + 6), NERO, -1)
    cv2.putText(img, s, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scala, col, sp, cv2.LINE_AA)


def scheletro(img, k, spess=None):
    h = img.shape[0]
    sp = spess or max(2, int(h / 300))
    for a, b in C.SCHELETRO:
        cv2.line(img, _p(k[a]), _p(k[b]), VERDE, sp, cv2.LINE_AA)
    for j in [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]:
        cv2.circle(img, _p(k[j]), sp + 2, BIANCO, -1, cv2.LINE_AA)


def annota(tr, F, nome_metrica, fase, mancino, valore=None, extra_testo=None):
    """Restituisce il fotogramma della fase con lo scheletro e la linea
    specifica della metrica."""
    i = F["fasi"].get(fase, F["fasi"]["P1"])
    img = tr.frame(i)
    if img is None:
        img = np.full((tr.altezza, tr.larghezza, 3), 60, np.uint8)
    k = tr.kp[i]
    k0 = tr.kp[F["fasi"]["P1"]]
    g, d = lati(mancino)
    scheletro(img, k)
    h = img.shape[0]
    sp = max(2, int(h / 350))
    bac, bac0 = medio(k, C.ANCA_SX, C.ANCA_DX), medio(k0, C.ANCA_SX, C.ANCA_DX)
    spa, spa0 = medio(k, C.SPALLA_SX, C.SPALLA_DX), medio(k0, C.SPALLA_SX, C.SPALLA_DX)
    m = nome_metrica

    if m in ("sway", "testa_backswing", "peso_impatto", "peso_finish", "slide"):
        for x0, col in ((bac0[0], GIALLO), (k0[C.NASO][0], AZZURRO)):
            _tratteggio(img, (x0, 0.05 * h), (x0, 0.95 * h), col, sp)
        cv2.line(img, _p((bac[0], bac[1] - 40)), _p((bac[0], bac[1] + 40)), ARANCIO, sp + 1)
        cv2.line(img, _p(k[g["caviglia"]]), _p(k[d["caviglia"]]), BIANCO, sp)
    elif m in ("early_extension", "perdita_postura", "testa_verticale", "inclinazione_busto",
               "flessione_ginocchia", "distanza_palla"):
        _tratteggio(img, (bac0[0], bac0[1] - 0.25 * h), (bac0[0], bac0[1] + 0.3 * h), GIALLO, sp)
        _tratteggio(img, bac0, spa0, AZZURRO, sp)
        cv2.line(img, _p(bac), _p(spa), ARANCIO, sp + 1, cv2.LINE_AA)
        y0 = k0[C.NASO][1]
        _tratteggio(img, (0.05 * img.shape[1], y0), (0.95 * img.shape[1], y0), AZZURRO, sp)
        if m == "distanza_palla":
            mm = mani(k0[None])[0]
            _tratteggio(img, (spa0[0], spa0[1]), (spa0[0], mm[1] + 40), BIANCO, sp)
    elif m == "over_the_top":
        mp_ = mani(tr.kp)
        f = F["fasi"]
        sal = mp_[f["P1"]:f["P4"] + 1]
        disc = mp_[f["P4"]:f["P7"] + 1]
        cv2.polylines(img, [sal.astype(np.int32)], False, AZZURRO, sp + 1, cv2.LINE_AA)
        cv2.polylines(img, [disc.astype(np.int32)], False, ARANCIO, sp + 1, cv2.LINE_AA)
        _testo(img, "salita", sal[len(sal) // 2] + [15, 0], col=(255, 210, 150))
        _testo(img, "discesa", disc[len(disc) // 2] + [15, 25], col=(150, 200, 255))
    elif m in ("tilt_setup", "tilt_impatto", "spalle_livellate"):
        cv2.line(img, _p(bac), _p(spa), ARANCIO, sp + 1, cv2.LINE_AA)
        _tratteggio(img, bac, (bac[0], bac[1] - 0.35 * h), BIANCO, sp)
    elif m in ("braccio_guida_top", "lag"):
        cv2.line(img, _p(k[g["spalla"]]), _p(k[g["gomito"]]), ARANCIO, sp + 2, cv2.LINE_AA)
        cv2.line(img, _p(k[g["gomito"]]), _p(k[g["polso"]]), ARANCIO, sp + 2, cv2.LINE_AA)
        if m == "lag":
            cv2.line(img, _p(k[g["polso"]]), _p(k[g["indice"]]), GIALLO, sp + 2, cv2.LINE_AA)
    elif m in ("rotazione_spalle", "rotazione_bacino", "x_factor"):
        cv2.line(img, _p(k[g["spalla"]]), _p(k[d["spalla"]]), ARANCIO, sp + 2, cv2.LINE_AA)
        cv2.line(img, _p(k[g["anca"]]), _p(k[d["anca"]]), GIALLO, sp + 2, cv2.LINE_AA)

    if valore is not None:
        spec = C.METRICHE.get(m)
        if spec:
            u = spec["unita"].replace("°", " gradi").replace("×", "x")
            if u in ("/2", ":1"):
                txt = f"{valore:.0f}{u}" if u == "/2" else f"{valore:.1f}{u}"
            else:
                txt = f"{valore:.2f} {u}" if abs(valore) < 3 else f"{valore:.0f} {u}"
            _testo(img, txt.strip(), (12, 0.075 * h))
    if extra_testo:
        _testo(img, extra_testo, (12, 0.12 * h))
    return img


def a_base64(img, larghezza=360, qualita=82):
    h, w = img.shape[:2]
    s = larghezza / w
    img = cv2.resize(img, (larghezza, int(h * s)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, qualita])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
