"""Metriche biomeccaniche per ciascuna vista.

Convenzioni:
- coordinate immagine in pixel, y verso il basso;
- le distanze vengono convertite in cm con la statura dell'utente;
- "guida" = lato verso il bersaglio (sinistro per un destro).
Ogni metrica restituisce: valore, vista, confidenza, fase di riferimento.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter

from . import config as C
from .phases import mani

# -------------------------------------------------------------------------
# Geometria
# -------------------------------------------------------------------------

def lati(mancino: bool):
    """Indici (guida, dietro) di spalla, gomito, polso, indice, anca, caviglia."""
    sx = dict(spalla=C.SPALLA_SX, gomito=C.GOMITO_SX, polso=C.POLSO_SX,
              indice=C.INDICE_SX, anca=C.ANCA_SX, ginocchio=C.GINOCCHIO_SX,
              caviglia=C.CAVIGLIA_SX)
    dx = dict(spalla=C.SPALLA_DX, gomito=C.GOMITO_DX, polso=C.POLSO_DX,
              indice=C.INDICE_DX, anca=C.ANCA_DX, ginocchio=C.GINOCCHIO_DX,
              caviglia=C.CAVIGLIA_DX)
    return (dx, sx) if mancino else (sx, dx)


def medio(kp, a, b):
    return (kp[..., a, :] + kp[..., b, :]) / 2.0


def angolo3(a, b, c):
    """Angolo in b (gradi) tra i segmenti b→a e b→c."""
    v1, v2 = a - b, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cos, -1, 1))))


def pixel_per_metro(kp_setup: np.ndarray, altezza_m: float) -> float:
    s = medio(kp_setup, C.SPALLA_SX, C.SPALLA_DX)
    h = medio(kp_setup, C.ANCA_SX, C.ANCA_DX)
    tronco = np.linalg.norm(s - h)
    gambe = []
    for anca, gin, cav in ((C.ANCA_SX, C.GINOCCHIO_SX, C.CAVIGLIA_SX),
                           (C.ANCA_DX, C.GINOCCHIO_DX, C.CAVIGLIA_DX)):
        gambe.append(np.linalg.norm(kp_setup[anca] - kp_setup[gin]) +
                     np.linalg.norm(kp_setup[gin] - kp_setup[cav]))
    return (tronco + max(gambe)) / (C.FRAZIONE_SEGMENTI_ALTEZZA * altezza_m)


def _proietta(v, asse):
    asse = asse / (np.linalg.norm(asse) + 1e-9)
    return v - np.dot(v, asse) * asse


def angolo_firmato(v0, v1, asse):
    """Angolo (gradi) da v0 a v1 attorno all'asse."""
    a, b = _proietta(v0, asse), _proietta(v1, asse)
    a /= np.linalg.norm(a) + 1e-9
    b /= np.linalg.norm(b) + 1e-9
    return float(np.degrees(np.arctan2(np.dot(np.cross(a, b), asse / np.linalg.norm(asse)),
                                       np.dot(a, b))))


def serie_rotazione(mondo, i0, idx_a, idx_b, asse):
    """Rotazione nel tempo del segmento a→b attorno all'asse, rispetto al frame i0."""
    v0 = mondo[i0, idx_a] - mondo[i0, idx_b]
    out = np.array([angolo_firmato(v0, mondo[t, idx_a] - mondo[t, idx_b], asse)
                    for t in range(mondo.shape[0])])
    return np.degrees(np.unwrap(np.radians(out)))


def _r(valore, vista, conf, fase, **extra):
    return dict(valore=float(valore), vista=vista, conf=conf, fase=fase, **extra)


# -------------------------------------------------------------------------
# Metriche comuni a tutte le viste (rotazioni, sequenza, tempo, equilibrio)
# -------------------------------------------------------------------------

def metriche_comuni(tr, F, mancino, ppm):
    g, d = lati(mancino)
    f, idx = F["fasi"], F["indici"]
    out, serie = {}, {}
    fps = tr.fps

    # Tempo
    t_back = (idx["top"] - idx["inizio"]) / fps
    t_down = max(1, idx["impatto"] - idx["top"]) / fps
    out["rapporto_tempo"] = _r(t_back / t_down, tr.vista,
                               "media" if fps < 100 else "alta", "P4",
                               back_s=t_back, down_s=t_down)
    out["durata_backswing"] = _r(t_back, tr.vista, "alta" if fps >= 60 else "media", "P4")

    # Equilibrio: oscillazione del bacino nell'ultimo 0,4 s fino al finish
    i1 = f["P10"]
    i0 = max(f["P9"], i1 - int(0.4 * fps))
    if i1 - i0 >= 3:
        bac = medio(tr.kp[i0:i1 + 1], C.ANCA_SX, C.ANCA_DX)
        osc = np.max(np.linalg.norm(bac - bac.mean(axis=0), axis=1)) / ppm * 100
        out["equilibrio"] = _r(osc, tr.vista, "media", "P10")

    # Rotazioni dai landmark 3D (stima monoculare: confidenza media/bassa)
    m = tr.mondo
    if m is not None and not np.isnan(m).any():
        i_s, i_t = f["P1"], f["P4"]
        spine = medio(m[i_s], C.SPALLA_SX, C.SPALLA_DX) - medio(m[i_s], C.ANCA_SX, C.ANCA_DX)
        verticale = np.array([0.0, -1.0, 0.0])  # y del mondo MediaPipe punta in basso
        rs = serie_rotazione(m, i_s, g["spalla"], d["spalla"], spine)
        rb = serie_rotazione(m, i_s, g["anca"], d["anca"], verticale)
        # ogni segmento orientato in modo che il backswing sia positivo
        rs = rs * (np.sign(rs[i_t]) or 1.0)
        rb = rb * (np.sign(rb[i_t]) or 1.0)
        # braccia: angolo 2D del braccio guida nell'immagine
        vb = tr.kp[:, g["polso"]] - tr.kp[:, g["spalla"]]
        rb_braccio = np.degrees(np.unwrap(np.arctan2(vb[:, 1], vb[:, 0])))
        rb_braccio = (rb_braccio - rb_braccio[i_s]) * (np.sign(rb_braccio[i_t] - rb_braccio[i_s]) or 1.0)
        out["rotazione_spalle"] = _r(abs(rs[i_t]), tr.vista, "media", "P4")
        out["rotazione_bacino"] = _r(abs(rb[i_t]), tr.vista, "media", "P4")
        out["x_factor"] = _r(abs(rs[i_t]) - abs(rb[i_t]), tr.vista, "bassa", "P4")

        # Sequenza cinematica: picchi di velocità angolare in discesa
        win = max(5, int(round(fps * 0.10)) | 1)
        liscia = (lambda x: savgol_filter(x, win, 2)) if len(rs) > win + 2 else (lambda x: x)
        w_b = -np.gradient(liscia(rb)) * fps
        w_s = -np.gradient(liscia(rs)) * fps
        w_a = -np.gradient(liscia(rb_braccio)) * fps
        v_m = np.linalg.norm(np.gradient(mani(tr.kp), axis=0), axis=1) * fps / ppm
        a, b = f["P4"], min(tr.T - 1, idx["impatto"] + max(2, int(0.03 * fps)))
        picchi = {k: a + int(np.argmax(s[a:b + 1])) for k, s in
                  (("bacino", w_b), ("busto", w_s), ("braccia", w_a), ("mani", v_m))}
        ordine = ["bacino", "busto", "braccia"]
        corretti = sum(picchi[ordine[i]] <= picchi[ordine[i + 1]] for i in range(2))
        out["sequenza"] = _r(corretti, tr.vista, "bassa" if fps < 100 else "media",
                             "P6", picchi={k: (v - idx["impatto"]) / fps for k, v in picchi.items()})
        serie.update(bacino=w_b, busto=w_s, braccia=w_a, mani=v_m)
    return out, serie


# -------------------------------------------------------------------------
# Vista frontale (face-on)
# -------------------------------------------------------------------------

def metriche_face_on(tr, F, mancino, ppm):
    g, d = lati(mancino)
    f = F["fasi"]
    kp = tr.kp
    cm = 100.0 / ppm
    p1, p4, p6, p7, p10 = f["P1"], f["P4"], f["P6"], f["P7"], f["P10"]
    conf = "media" if tr.tipo == "FO" else "bassa"

    # Direzione del bersaglio in immagine: la spalla guida sta dal lato del bersaglio
    verso = np.sign(kp[p1, g["spalla"], 0] - kp[p1, d["spalla"], 0]) or 1.0
    out = {"_verso": verso}

    larg_piedi = abs(kp[p1, g["caviglia"], 0] - kp[p1, d["caviglia"], 0])
    larg_spalle = abs(kp[p1, g["spalla"], 0] - kp[p1, d["spalla"], 0]) + 1e-6
    out["larghezza_stance"] = _r(larg_piedi / larg_spalle, tr.vista, conf, "P1")

    def tilt(i):
        s = medio(kp[i], C.SPALLA_SX, C.SPALLA_DX) - medio(kp[i], C.ANCA_SX, C.ANCA_DX)
        return np.degrees(np.arctan2(-verso * s[0], -s[1]))
    out["tilt_setup"] = _r(tilt(p1), tr.vista, conf, "P1")
    out["tilt_impatto"] = _r(tilt(p7), tr.vista, conf, "P7")

    bac = medio(kp, C.ANCA_SX, C.ANCA_DX)
    out["sway"] = _r(-verso * (bac[p4, 0] - bac[p1, 0]) * cm, tr.vista, conf, "P4")
    out["testa_backswing"] = _r(-verso * (kp[p4, C.NASO, 0] - kp[p1, C.NASO, 0]) * cm,
                                tr.vista, conf, "P4")

    def peso(i):
        xd, xg = kp[i, d["caviglia"], 0], kp[i, g["caviglia"], 0]
        return (bac[i, 0] - xd) / (xg - xd + 1e-6)
    out["peso_impatto"] = _r(peso(p7), tr.vista, conf, "P7", setup=peso(p1))
    out["peso_finish"] = _r(peso(p10), tr.vista, conf, "P10")

    out["braccio_guida_top"] = _r(angolo3(kp[p4, g["spalla"]], kp[p4, g["gomito"]],
                                          kp[p4, g["polso"]]), tr.vista, conf, "P4")

    # Lag (stima): deviazione polso-mano mantenuta a metà discesa rispetto al top
    def hinge(i):
        return 180 - angolo3(kp[i, g["gomito"]], kp[i, g["polso"]], kp[i, g["indice"]])
    h_top, h_p6 = hinge(p4), hinge(p6)
    if h_top > 8:
        out["lag"] = _r(100 * h_p6 / h_top, tr.vista, "bassa", "P6",
                        top=h_top, p6=h_p6)
    return out


# -------------------------------------------------------------------------
# Vista da dietro (down-the-line)
# -------------------------------------------------------------------------

def metriche_dtl(tr, F, mancino, ppm):
    g, d = lati(mancino)
    f = F["fasi"]
    kp = tr.kp
    cm = 100.0 / ppm
    p1, p4, p7 = f["P1"], f["P4"], f["P7"]
    m = mani(kp)
    bac = medio(kp, C.ANCA_SX, C.ANCA_DX)
    spa = medio(kp, C.SPALLA_SX, C.SPALLA_DX)
    # Lato della palla: le mani al setup stanno davanti al bacino
    verso = np.sign(m[p1, 0] - bac[p1, 0]) or 1.0
    out = {"_verso": verso}

    def busto(i):
        s = spa[i] - bac[i]
        return np.degrees(np.arctan2(abs(s[0]), -s[1]))
    out["inclinazione_busto"] = _r(busto(p1), tr.vista, "media", "P1")
    out["perdita_postura"] = _r(busto(p7) - busto(p1), tr.vista, "media", "P7")

    fless = [180 - angolo3(kp[p1, a], kp[p1, k], kp[p1, c]) for a, k, c in
             ((g["anca"], g["ginocchio"], g["caviglia"]), (d["anca"], d["ginocchio"], d["caviglia"]))]
    out["flessione_ginocchia"] = _r(np.mean(fless), tr.vista, "media", "P1")

    out["distanza_palla"] = _r(verso * (m[p1, 0] - spa[p1, 0]) * cm, tr.vista, "media", "P1")
    out["early_extension"] = _r(verso * (bac[p7, 0] - bac[p1, 0]) * cm, tr.vista, "media", "P7")
    out["testa_verticale"] = _r((kp[p1, C.NASO, 1] - kp[p7, C.NASO, 1]) * cm,
                                tr.vista, "media", "P7")

    # Over the top: confronto del percorso delle mani in salita e in discesa
    h = -m[:, 1]
    h0, ht = h[p1], h[p4]
    livelli = h0 + np.linspace(0.25, 0.75, 9) * (ht - h0)
    sal = slice(p1, p4 + 1)
    disc = slice(p4, p7 + 1)

    def x_a_quota(seg):
        hs, xs = h[seg], m[seg, 0]
        ordine = np.argsort(hs)
        return np.interp(livelli, hs[ordine], xs[ordine])

    if p4 - p1 > 3 and p7 - p4 > 3:
        delta = np.mean(x_a_quota(disc) - x_a_quota(sal)) * verso * cm
        out["over_the_top"] = _r(delta, tr.vista, "bassa" if tr.fps < 100 else "media", "P5")
    return out


# -------------------------------------------------------------------------
# Velocità delle mani (per la stima della velocità della testa del bastone)
# -------------------------------------------------------------------------

def picco_velocita_mani(tr, F, mancino, ppm) -> float:
    """Velocità di picco del polso guida in discesa, in m/s."""
    g, _ = lati(mancino)
    a = F["fasi"]["P4"]
    b = min(tr.T - 1, F["indici"]["impatto"] + 2)
    if tr.tipo == "DTL" and tr.mondo is not None and not np.isnan(tr.mondo).any():
        p = tr.mondo[:, g["polso"]]
        v = np.linalg.norm(np.gradient(p, axis=0), axis=1) * tr.fps
    else:
        p = tr.kp[:, g["polso"]]
        v = np.linalg.norm(np.gradient(p, axis=0), axis=1) * tr.fps / ppm
    return float(np.max(v[a:b + 1]))


def calcola_vista(tr, F, mancino, altezza_m):
    ppm = pixel_per_metro(tr.kp[F["fasi"]["P1"]], altezza_m)
    comuni, serie = metriche_comuni(tr, F, mancino, ppm)
    if tr.tipo in ("FO", "FO2"):
        spec = metriche_face_on(tr, F, mancino, ppm)
    else:
        spec = metriche_dtl(tr, F, mancino, ppm)
    verso = spec.pop("_verso")
    return dict(metriche={**comuni, **spec}, serie=serie, ppm=ppm, verso=verso,
                v_mani=picco_velocita_mani(tr, F, mancino, ppm))


# Metriche indipendenti dalla vista: si fa la media tra le viste disponibili
MEDIA_TRA_VISTE = {"rotazione_spalle", "rotazione_bacino", "x_factor",
                   "rapporto_tempo", "durata_backswing", "equilibrio"}
ORDINE_TIPO = {"FO": 0, "FO2": 1, "DTL": 2}


def unisci(per_vista: dict, tipi: dict) -> dict:
    """Combina le metriche di più viste in un unico insieme."""
    finali = {}
    for nome, spec in C.METRICHE.items():
        cand = [(v, r["metriche"][nome]) for v, r in per_vista.items()
                if nome in r["metriche"] and tipi[v] in spec["viste"]]
        if not cand:
            continue
        if nome in MEDIA_TRA_VISTE and len(cand) > 1:
            val = float(np.mean([c["valore"] for _, c in cand]))
            base = dict(cand[0][1])
            base.update(valore=val, vista="+".join(v for v, _ in cand))
            finali[nome] = base
        else:
            cand.sort(key=lambda vc: spec["viste"].index(tipi[vc[0]]))
            finali[nome] = cand[0][1]
    return finali
