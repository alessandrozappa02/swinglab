"""Stima del volo della palla.

1. Velocità della testa del bastone = picco di velocità delle mani × fattore
   del bastone (raggio effettivo + rilascio), combinata con la velocità
   tipica per il livello dichiarato (media pesata sull'incertezza).
2. Velocità palla = velocità bastone × smash factor tipico del bastone.
3. Lancio e spin da tabelle per bastone (non misurabili dal video).
4. Carry con un modello fisico (resistenza aerodinamica + effetto Magnus),
   i cui coefficienti sono tarati sulle medie TrackMan PGA/LPGA Tour
   (errore medio ~3% su driver, ferro 3, 5, 7 e PW).
Tutto è restituito come intervallo con un livello di confidenza.
"""
from __future__ import annotations

import math

from . import config as C

MPH_MS = 0.44704
YD_M = 0.9144
Z80 = 1.2816  # intervallo all'80%

# Coefficienti tarati: Cd = a + b·S, Cl = c·S^0.4 (S = spin ratio)
CD_A, CD_B, CL_C = 0.1046, 0.2825, 0.1916
RHO, MASSA, DIAM = 1.225, 0.04593, 0.04267


def carry_m(v_palla_mph: float, lancio_deg: float, spin_rpm: float) -> tuple[float, float]:
    """Restituisce (carry in metri, altezza massima in metri)."""
    area, r = math.pi * DIAM ** 2 / 4, DIAM / 2
    v = v_palla_mph * MPH_MS
    th = math.radians(lancio_deg)
    w = spin_rpm * 2 * math.pi / 60
    x = y = 0.0
    vx, vy = v * math.cos(th), v * math.sin(th)
    dt, t, ymax = 0.002, 0.0, 0.0
    while t < 15:
        sp = math.hypot(vx, vy)
        s = r * w / sp
        cd, cl = CD_A + CD_B * s, CL_C * s ** 0.4
        k = 0.5 * RHO * area * sp / MASSA
        ax = -k * (cd * vx + cl * vy)
        ay = -9.81 - k * (cd * vy - cl * vx)
        nx, ny = x + vx * dt, y + vy * dt
        vx, vy = vx + ax * dt, vy + ay * dt
        t += dt
        w *= math.exp(-0.04 * dt)
        if ny < 0 and t > 0.2:
            return nx, ymax
        x, y = nx, ny
        ymax = max(ymax, y)
    return x, ymax


def traiettoria(v_palla_mph, lancio_deg, spin_rpm, passi=40):
    """Punti (x, y) in metri per disegnare la traiettoria."""
    area, r = math.pi * DIAM ** 2 / 4, DIAM / 2
    v = v_palla_mph * MPH_MS
    th = math.radians(lancio_deg)
    w = spin_rpm * 2 * math.pi / 60
    x = y = 0.0
    vx, vy = v * math.cos(th), v * math.sin(th)
    dt, t, pts = 0.01, 0.0, [(0.0, 0.0)]
    while t < 15:
        sp = math.hypot(vx, vy)
        s = r * w / sp
        cd, cl = CD_A + CD_B * s, CL_C * s ** 0.4
        k = 0.5 * RHO * area * sp / MASSA
        ax, ay = -k * (cd * vx + cl * vy), -9.81 - k * (cd * vy - cl * vx)
        x, y = x + vx * dt, y + vy * dt
        vx, vy = vx + ax * dt, vy + ay * dt
        t += dt
        w *= math.exp(-0.04 * dt)
        if y < 0:
            break
        pts.append((x, y))
    step = max(1, len(pts) // passi)
    return pts[::step] + [pts[-1]]


def _incertezza_video(fps: float) -> float:
    for soglia, rel in C.INCERTEZZA_VIDEO_PER_FPS:
        if fps >= soglia:
            return rel
    return 0.25


def stima(v_mani_ms, bastone, handicap, fps, altezza_nota, percorso_deg=None,
          launch_monitor=None):
    rapp, smash, lancio, spin, rotolo, k_mani = C.BASTONI[bastone]
    lm = launch_monitor or {}
    note = []

    # --- velocità del bastone ------------------------------------------
    hcp_prior = handicap if handicap is not None else 40
    prior = C.driver_mph_atteso(hcp_prior) * rapp
    sd_prior = C.DEV_STD_PRIOR_MPH * rapp
    if lm.get("club_mph"):
        chs, sd, fonte = lm["club_mph"], 1.0, "launch monitor"
    elif v_mani_ms:
        video = v_mani_ms * k_mani / MPH_MS
        rel = math.sqrt(_incertezza_video(fps) ** 2 + 0.08 ** 2 +
                        (0 if altezza_nota else 0.06) ** 2)
        sd_video = video * rel
        w_v, w_p = 1 / sd_video ** 2, 1 / sd_prior ** 2
        chs = (video * w_v + prior * w_p) / (w_v + w_p)
        sd = math.sqrt(1 / (w_v + w_p))
        fonte = "video + livello"
        note.append(f"Dal video: {video:.0f} mph (±{sd_video:.0f}); "
                    f"atteso per il livello: {prior:.0f} mph (±{sd_prior:.0f}).")
    else:
        chs, sd, fonte = prior, sd_prior, "solo livello"

    # --- palla ---------------------------------------------------------
    if lm.get("ball_mph"):
        bs, sd_bs = lm["ball_mph"], 1.0
    else:
        bs = chs * smash
        sd_bs = math.sqrt((sd * smash) ** 2 + (chs * 0.04) ** 2)
    rif = 94 * rapp
    spin_c = spin * (chs / rif) ** 0.6
    car, apice = carry_m(bs, lancio, spin_c)
    car_lo, _ = carry_m(bs - Z80 * sd_bs, lancio + 2, spin_c * 1.2)
    car_hi, _ = carry_m(bs + Z80 * sd_bs, lancio - 1, spin_c * 0.85)
    if lm.get("carry_m"):
        note.append(f"Carry misurato dal launch monitor: {lm['carry_m']:.0f} m.")

    rel_carry = (car_hi - car_lo) / (2 * Z80 * car)
    if fonte == "launch monitor":
        conf_v = "alta"
    elif rel_carry < 0.07:
        conf_v = "media"
    else:
        conf_v = "bassa"

    # --- direzione e curva -------------------------------------------
    if percorso_deg is None:
        direzione = dict(testo="Non stimabile: serve il video da dietro (C).", conf=None,
                         percorso=None)
    else:
        if percorso_deg < -3:
            t = ("Percorso dall'esterno all'interno: palla che parte a sinistra (pull) "
                 "o, più spesso negli amatori con faccia aperta, curva da sinistra a "
                 "destra (fade/slice).")
        elif percorso_deg > 4:
            t = ("Percorso dall'interno all'esterno: palla che parte a destra (push) "
                 "o curva da destra a sinistra (draw/hook) se la faccia è chiusa.")
        else:
            t = ("Percorso quasi neutro: volo tendenzialmente dritto; la curva dipende "
                 "dalla faccia, che il video non misura.")
        direzione = dict(testo=t, conf="bassa", percorso=percorso_deg)

    return dict(
        bastone=bastone, fonte=fonte, note=note,
        club=dict(mph=chs, lo=chs - Z80 * sd, hi=chs + Z80 * sd,
                  conf="alta" if fonte == "launch monitor" else
                  ("media" if sd / chs < 0.09 else "bassa")),
        palla=dict(mph=bs, lo=bs - Z80 * sd_bs, hi=bs + Z80 * sd_bs, smash=smash,
                   conf="alta" if lm.get("ball_mph") else "bassa"),
        lancio=dict(deg=lancio, lo=lancio - 3, hi=lancio + 3, conf="bassa"),
        spin=dict(rpm=spin_c, lo=spin_c * 0.75, hi=spin_c * 1.25, conf="bassa"),
        carry=dict(m=car, lo=car_lo, hi=car_hi, conf=conf_v, apice=apice),
        totale=dict(m=car * (1 + rotolo), lo=car_lo * (1 + rotolo * 0.5),
                    hi=car_hi * (1 + rotolo * 1.5), conf="bassa"),
        direzione=direzione,
        traiettoria=traiettoria(bs, lancio, spin_c),
    )


def percorso_da_over_the_top(delta_cm):
    """Stima grezza del percorso del bastone (gradi, + = dall'interno)."""
    if delta_cm is None:
        return None
    return -0.5 * delta_cm - 1.0
