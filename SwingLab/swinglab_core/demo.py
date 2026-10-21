"""Swing dimostrativo sintetico.

Genera un golfer 3D (destro) con parametri controllabili, lo proietta nelle
tre angolazioni come farebbe un telefono e produce keypoint "rumorosi" nello
stesso formato di MediaPipe. Serve a provare l'app senza video e come
modello di riferimento nei confronti affiancati.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import cv2
import numpy as np

from . import config as C
from .pose import Traccia, pulisci


@dataclass
class Parametri:
    t_setup: float = 0.5
    t_back: float = 0.95
    rapporto: float = 2.3        # backswing / downswing
    t_follow: float = 0.45
    t_hold: float = 0.7
    spalle_top: float = 80
    bacino_top: float = 47
    bacino_imp: float = -25
    spalle_imp: float = -5
    bacino_fin: float = -95
    spalle_fin: float = -120
    c_bacino: float = 0.62       # posizione del picco di velocità in discesa
    c_busto: float = 0.30
    c_braccia: float = 0.80
    sway_cm: float = 7
    slide_imp_cm: float = 3
    ee_cm: float = 9             # bacino verso la palla all'impatto
    busto_setup: float = 37
    busto_imp: float = 29
    tilt_setup: float = 6
    tilt_imp: float = 18
    ott_cm: float = 9
    hinge_top: float = 60
    hinge_p6: float = 0.5        # frazione mantenuta a metà discesa
    finish_x_cm: float = 15
    oscill_finish_cm: float = 2.5
    phi_top: float = 128
    phi_fin: float = -155
    piega_top: float = 0.03      # accorciamento del braccio guida al top


IDEALE = Parametri(t_back=0.85, rapporto=3.0, piega_top=0.0, spalle_top=92, bacino_top=45,
                   bacino_imp=-38, spalle_imp=-20, c_bacino=0.40, c_busto=0.58,
                   c_braccia=0.80, sway_cm=1, slide_imp_cm=9, ee_cm=-2,
                   busto_imp=36, tilt_imp=27, ott_cm=-5, hinge_p6=0.92,
                   finish_x_cm=20, oscill_finish_cm=0.5)


# ---------------------------------------------------------------------------
def _ease_picco(c, fine=0.35, n=400):
    """Funzione 0→1 con velocità a triangolo che ha il picco in c."""
    s = np.linspace(0, 1, n)
    v = np.where(s < c, 0.15 + 0.85 * s / c, 1 - (1 - fine) * (s - c) / (1 - c))
    cum = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2)])
    cum /= cum[-1]
    return lambda x: np.interp(x, s, cum)


def _rodrigues(v, asse, ang):
    k = asse / np.linalg.norm(asse)
    return v * np.cos(ang) + np.cross(k, v) * np.sin(ang) + k * np.dot(k, v) * (1 - np.cos(ang))


def _unit(v):
    return v / (np.linalg.norm(v) + 1e-9)


def scheletro_3d(p: Parametri, fps: float = 120.0):
    """Restituisce (T,33,3) in metri: X verso il bersaglio, Y in alto, Z verso la palla."""
    t_down = p.t_back / p.rapporto
    durate = [p.t_setup, p.t_back, t_down, p.t_follow, p.t_hold]
    confini = np.cumsum([0] + durate)
    T = int(confini[-1] * fps)
    e_bac, e_bus, e_bra = _ease_picco(p.c_bacino), _ease_picco(p.c_busto), _ease_picco(p.c_braccia)
    e_mani = _ease_picco(0.9, fine=0.8)
    ankle_g, ankle_d = np.array([0.22, 0.08, 0.0]), np.array([-0.22, 0.08, 0.0])
    hip0 = np.array([0.0, 0.92, -0.06])
    out = np.zeros((T, 33, 3))
    rng = np.random.default_rng(3)

    # piano delle mani
    s0 = _unit(np.array([-np.sin(np.radians(p.tilt_setup)),
                         np.cos(np.radians(p.busto_setup)),
                         np.sin(np.radians(p.busto_setup))]))
    sc0 = hip0 + 0.50 * s0
    lat0 = np.array([1.0, 0, 0]); lat0 = _unit(lat0 - np.dot(lat0, s0) * s0)
    O = sc0 + 0.19 * lat0                      # spalla guida al setup
    mani0 = np.array([0.04, 0.80, 0.40])
    r = min(np.linalg.norm(mani0 - O), 0.575)
    e1 = _unit(mani0 - O)
    e2 = np.array([-1.0, 0.0, 0.0])
    e2 = _unit(e2 - np.dot(e2, e1) * e1)
    n_piano = np.cross(e1, e2)

    for i in range(T):
        t = i / fps
        fase = np.searchsorted(confini, t, side="right") - 1
        s = np.clip((t - confini[min(fase, 4)]) / durate[min(fase, 4)], 0, 1)
        if fase <= 0:
            u = 0.0; yb = ys = 0.0; phi = 0.0; dx = dz = 0.0
            busto, tilt, hinge = p.busto_setup, p.tilt_setup, 15
            fin = 0.0
        elif fase == 1:      # backswing
            u = 0.5 - 0.5 * np.cos(np.pi * s)
            yb, ys = p.bacino_top * u, p.spalle_top * u
            phi = p.phi_top * u
            dx, dz = -p.sway_cm / 100 * u, 0.0
            busto, tilt = p.busto_setup, p.tilt_setup
            hinge = 15 + (p.hinge_top - 15) * min(1, 1.6 * u)
            fin = 0.0
        elif fase == 2:      # discesa
            yb = p.bacino_top + (p.bacino_imp - p.bacino_top) * e_bac(s)
            ys = p.spalle_top + (p.spalle_imp - p.spalle_top) * e_bus(s)
            phi = p.phi_top * (1 - e_bra(s))
            ott = p.ott_cm / 100 * np.sin(np.pi * min(1, s * 1.15))
            dx = (-p.sway_cm + (p.sway_cm + p.slide_imp_cm) * e_bac(s)) / 100
            dz = p.ee_cm / 100 * e_bac(s)
            busto = p.busto_setup + (p.busto_imp - p.busto_setup) * s ** 1.5
            tilt = p.tilt_setup + (p.tilt_imp - p.tilt_setup) * s
            # mantenimento dell'angolo dei polsi fino a ~metà discesa, poi rilascio
            keep = p.hinge_top * (1 - (1 - p.hinge_p6) * min(1, s / 0.6))
            hinge = keep if s < 0.6 else keep + (12 - keep) * (s - 0.6) / 0.4
            fin = 0.0
        else:                # follow-through e finish
            v = 1 - (1 - s) ** 2 if fase == 3 else 1.0
            vc = 0.5 - 0.5 * np.cos(np.pi * s) if fase == 3 else 1.0   # il corpo rallenta all'impatto
            yb = p.bacino_imp + (p.bacino_fin - p.bacino_imp) * vc
            ys = p.spalle_imp + (p.spalle_fin - p.spalle_imp) * vc
            phi = p.phi_fin * v
            dx = (p.slide_imp_cm + (p.finish_x_cm - p.slide_imp_cm) * v) / 100
            dz = p.ee_cm / 100 * (1 - 0.5 * v)
            busto = p.busto_imp + (8 - p.busto_imp) * v
            tilt = p.tilt_imp + (p.tilt_imp + 8 - p.tilt_imp) * v
            hinge = 12 + 40 * v
            fin = v
            if fase == 4:
                osc = p.oscill_finish_cm / 100 * np.sin(2 * np.pi * 1.6 * (t - confini[4]))
                dx += osc
        ottz = p.ott_cm / 100 * np.sin(np.pi * min(1, s * 1.15)) if fase == 2 else 0.0

        hip_c = hip0 + np.array([dx, 0.0, dz]) + np.array([0, -0.02 * fin, 0])
        ang_b = np.radians(yb)
        rotY = lambda v_: np.array([v_[0] * np.cos(ang_b) - v_[2] * np.sin(ang_b), v_[1],
                                    v_[0] * np.sin(ang_b) + v_[2] * np.cos(ang_b)])
        hip_g = hip_c + rotY(np.array([0.10, 0, 0]))
        hip_d = hip_c + rotY(np.array([-0.10, 0, 0]))

        sp = _unit(np.array([-np.sin(np.radians(tilt)), np.cos(np.radians(busto)),
                             np.sin(np.radians(busto))]))
        sc = hip_c + 0.50 * sp
        lat = np.array([1.0, 0, 0]); lat = _unit(lat - np.dot(lat, sp) * sp)
        lat = _rodrigues(lat, sp, -np.radians(ys))
        sh_g, sh_d = sc + 0.19 * lat, sc - 0.19 * lat
        avanti = np.array([0, 0, 1.0]); avanti = _unit(avanti - np.dot(avanti, sp) * sp)
        naso = sc + 0.24 * sp + 0.08 * avanti + np.array([-0.01 * u if fase == 1 else 0, 0, 0])

        # mani sul piano (con lo spostamento del bacino e l'eventuale over the top)
        ph = np.radians(phi)
        piega = p.piega_top * (u if fase == 1 else (1 - e_bra(s) if fase == 2 else 0.0))
        mani = sh_g + r * (1 - piega) * (np.cos(ph) * e1 + np.sin(ph) * e2)
        mani = mani + np.array([0, 0.25 * ottz, ottz])
        L_up, L_fa = 0.30, 0.28
        def braccio(sh, w, polo):
            d = w - sh
            dist = np.linalg.norm(d)
            if dist > L_up + L_fa - 1e-3:
                w = sh + _unit(d) * (L_up + L_fa - 1e-3); d = w - sh; dist = np.linalg.norm(d)
            cosb = (L_up ** 2 + dist ** 2 - L_fa ** 2) / (2 * L_up * dist)
            b = np.arccos(np.clip(cosb, -1, 1))
            u_ = _unit(d); w_ = _unit(polo - np.dot(polo, u_) * u_)
            gom = sh + L_up * (np.cos(b) * u_ + np.sin(b) * w_)
            return gom, w
        gom_g, pol_g = braccio(sh_g, mani, np.array([0, -1.0, -0.3]))
        avamb = _unit(pol_g - gom_g)
        dir_mano = _rodrigues(avamb, n_piano, -np.radians(hinge))
        pol_d_t = pol_g - 0.05 * dir_mano + np.array([0, 0, -0.02])
        gom_d, pol_d = braccio(sh_d, pol_d_t, np.array([0, -1.0, 0.2]))
        ind_g = pol_g + 0.08 * dir_mano
        ind_d = pol_d + 0.08 * dir_mano

        a_d = ankle_d + np.array([0.04 * fin, 0.07 * fin, 0])
        kn_g = ankle_g + 0.52 * (hip_g - ankle_g) + np.array([0, 0, 0.06])
        kn_d = a_d + 0.52 * (hip_d - a_d) + np.array([0.06 * fin, 0, 0.06])

        J = out[i]
        J[0] = naso
        for k in range(1, 11):
            J[k] = naso + np.array([0.02 * (k % 3 - 1), 0.02 * (k // 4), -0.03])
        J[11], J[12] = sh_g, sh_d
        J[13], J[14] = gom_g, gom_d
        J[15], J[16] = pol_g, pol_d
        J[17], J[19], J[21] = ind_g, ind_g, ind_g
        J[18], J[20], J[22] = ind_d, ind_d, ind_d
        J[23], J[24] = hip_g, hip_d
        J[25], J[26] = kn_g, kn_d
        J[27], J[28] = ankle_g, a_d
        J[29] = ankle_g + np.array([0, -0.05, -0.06]); J[31] = ankle_g + np.array([0.04, -0.07, 0.15])
        J[30] = a_d + np.array([0, -0.05 + 0.04 * fin, -0.06]); J[32] = ankle_d + np.array([0, -0.07, 0.15])
    return out


# ---------------------------------------------------------------------------
CAMERE = {
    "A": dict(pos=np.array([0.0, 1.0, 3.6]), avanti=np.array([0, 0, -1.0])),
    "B": dict(pos=np.array([0.0, 1.0, -3.6]), avanti=np.array([0, 0, 1.0])),
    "C": dict(pos=np.array([-3.8, 1.0, 0.45]), avanti=np.array([1.0, 0, 0])),
}
W, H, FOCALE = 720, 1280, 1500.0


def proietta(P, vista):
    cam = CAMERE[vista]
    f = cam["avanti"]; su = np.array([0, 1.0, 0]); dx = np.cross(f, su)
    rel = P - cam["pos"]
    prof = rel @ f
    u = W / 2 + FOCALE * (rel @ dx) / prof
    v = H / 2 - FOCALE * (rel @ su) / prof
    return np.stack([u, v], axis=-1)


def mondo_camera(P, vista):
    cam = CAMERE[vista]
    f = cam["avanti"]; su = np.array([0, 1.0, 0]); dx = np.cross(f, su)
    hip = (P[:, 23] + P[:, 24]) / 2
    rel = P - hip[:, None, :]
    return np.stack([rel @ dx, -(rel @ su), rel @ f], axis=-1)


PALLA = np.array([0.03, 0.021, 0.66])


_SFONDO = None


def _sfondo():
    global _SFONDO
    if _SFONDO is None:
        y = np.arange(H)[:, None] / H
        cielo = np.stack([230 - 60 * y, 205 - 30 * y, 170 + 0 * y], -1)
        prato = np.stack([70 + 0 * y, 125 + 80 * (y - 0.55), 60 + 0 * y], -1)
        col = np.where(y[..., None] < 0.55, cielo, prato)
        _SFONDO = np.repeat(col, W, axis=1).clip(0, 255).astype(np.uint8)
    return _SFONDO


def _rendi(P3, i, vista, kp_puliti, etichetta="SWING DIMOSTRATIVO (dati sintetici)"):
    img = _sfondo().copy()
    k = kp_puliti[i]
    tappeto = proietta(np.array([[-0.6, 0, -0.3], [0.6, 0, -0.3], [0.6, 0, 1.0], [-0.6, 0, 1.0]]), vista)
    cv2.fillPoly(img, [tappeto.astype(np.int32)], (60, 95, 45))
    corpo = (95, 85, 80)
    for a, b, sp in [(23, 25, 30), (25, 27, 26), (24, 26, 30), (26, 28, 26), (11, 23, 34), (12, 24, 34),
                     (11, 12, 30), (23, 24, 34), (11, 13, 20), (13, 15, 17), (12, 14, 20), (14, 16, 17),
                     (27, 31, 16), (28, 32, 16)]:
        cv2.line(img, tuple(map(int, k[a])), tuple(map(int, k[b])), corpo, sp, cv2.LINE_AA)
    cv2.circle(img, tuple(map(int, k[0])), 34, corpo, -1, cv2.LINE_AA)
    # bastone
    mani = (P3[i, 15] + P3[i, 16]) / 2
    dirm = P3[i, 19] - P3[i, 15]
    testa = mani + 1.0 * dirm / (np.linalg.norm(dirm) + 1e-9)
    pm, pt = proietta(np.stack([mani, testa]), vista)
    cv2.line(img, tuple(map(int, pm)), tuple(map(int, pt)), (200, 200, 200), 4, cv2.LINE_AA)
    pb = proietta(PALLA[None], vista)[0]
    cv2.circle(img, tuple(map(int, pb)), 7, (250, 250, 250), -1, cv2.LINE_AA)
    if etichetta:
        cv2.putText(img, etichetta, (18, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 40, 40), 2, cv2.LINE_AA)
    return img


def tracce(viste=("A", "C"), parametri: Parametri | None = None, fps=120.0,
           rumore_px=1.5, rumore_m=0.008, seme=7,
           etichetta="SWING DIMOSTRATIVO (dati sintetici)"):
    p = parametri or Parametri()
    P3 = scheletro_3d(p, fps)
    rng = np.random.default_rng(seme)
    risultati = {}
    for v in viste:
        kp_puliti = proietta(P3, v)
        kp = pulisci(kp_puliti + rng.normal(0, rumore_px, kp_puliti.shape), fps)
        mondo = pulisci(mondo_camera(P3, v) + rng.normal(0, rumore_m, (P3.shape[0], 33, 3)), fps)
        tr = Traccia(v, C.VISTE[v]["tipo"], fps, W, H, kp, np.ones(kp.shape[:2]), mondo)
        tr.render = (lambda i, P3=P3, v=v, kpp=kp_puliti: _rendi(P3, i, v, kpp, etichetta))
        risultati[v] = tr
    return risultati


def riferimento(vista, fps=120.0):
    """Traccia del modello ideale (senza rumore) per il confronto affiancato."""
    return tracce((vista,), IDEALE, fps, rumore_px=0.0, rumore_m=0.0,
                  etichetta="MODELLO DI RIFERIMENTO")[vista]
