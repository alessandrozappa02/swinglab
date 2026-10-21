"""Rilevamento delle fasi P1-P10 dalla traiettoria delle mani.

Idea: l'altezza delle mani descrive lo swing in modo robusto da qualsiasi
angolazione. Il top (P4) è il punto più alto prima del picco di velocità;
l'impatto (P7) è il punto più basso dopo il top; le fasi intermedie si
fissano a frazioni dell'altezza raggiunta (approssimazione del sistema P).
"""
from __future__ import annotations

import numpy as np

from . import config as C

NOMI_FASI = {
    "P1": "Setup", "P2": "Takeaway", "P3": "Metà backswing", "P4": "Top",
    "P5": "Inizio discesa", "P6": "Metà discesa", "P7": "Impatto",
    "P8": "Rilascio", "P9": "Follow-through", "P10": "Finish",
}


def mani(kp: np.ndarray) -> np.ndarray:
    return (kp[:, C.POLSO_SX] + kp[:, C.POLSO_DX]) / 2.0


def velocita(punti: np.ndarray, fps: float) -> np.ndarray:
    v = np.gradient(punti, axis=0) * fps
    return np.linalg.norm(v, axis=1)


def rileva_fasi(kp: np.ndarray, fps: float) -> dict:
    T = kp.shape[0]
    m = mani(kp)
    alt = -m[:, 1]                      # in immagine y cresce verso il basso
    vel = velocita(m, fps)
    vmax = np.nanmax(vel)
    i_vmax = int(np.nanargmax(vel))

    # Il picco di velocità in discesa deve avere prima un top: se cade troppo
    # presto (rumore), prendiamo il secondo picco.
    if i_vmax < int(0.25 * fps):
        i_vmax = int(np.nanargmax(vel[int(0.25 * fps):])) + int(0.25 * fps)

    i_top = int(np.argmax(alt[:i_vmax])) if i_vmax > 1 else 0

    # Impatto: punto più basso delle mani tra il top e 0,6 s dopo
    fine = min(T, i_top + int(0.6 * fps))
    i_imp = i_top + int(np.argmin(alt[i_top:fine])) if fine > i_top + 1 else i_vmax

    # Inizio del takeaway: risalendo dal top, ultimo istante in cui le mani
    # sono ancora alla quota del setup (la più bassa prima del top)
    htop = alt[i_top]
    h_basso = np.min(alt[:i_top + 1]) if i_top > 0 else alt[0]
    soglia_h = h_basso + 0.04 * (htop - h_basso)
    i_start = i_top
    while i_start > 0 and alt[i_start] > soglia_h:
        i_start -= 1
    # piccolo arretramento finché le mani sono davvero ferme
    soglia_v = 0.04 * vmax
    while i_start > 0 and vel[i_start] > soglia_v:
        i_start -= 1
    i_setup = max(0, i_start - int(0.1 * fps))

    h0 = np.median(alt[max(0, i_start - int(0.3 * fps)):i_start + 1])

    def primo(intervallo, frazione, salendo=True):
        livello = h0 + frazione * (htop - h0)
        for i in intervallo:
            if (alt[i] >= livello) if salendo else (alt[i] <= livello):
                return i
        return intervallo[-1] if len(intervallo) else i_top

    p2 = primo(range(i_start, i_top + 1), 0.25)
    p3 = primo(range(i_start, i_top + 1), 0.60)
    p5 = primo(range(i_top, i_imp + 1), 0.60, salendo=False)
    p6 = primo(range(i_top, i_imp + 1), 0.25, salendo=False)

    # Dopo l'impatto le mani risalgono verso il finish
    resto = range(i_imp, T)
    hfin = np.max(alt[i_imp:]) if T > i_imp else htop
    def dopo(frazione):
        livello = h0 + frazione * (hfin - h0)
        for i in resto:
            if alt[i] >= livello:
                return i
        return T - 1
    p8, p9 = dopo(0.25), dopo(0.60)

    # Finish: mani di nuovo quasi ferme dopo il follow-through
    i_fin = T - 1
    for i in range(p9, T):
        if vel[i] < 0.08 * vmax:
            i_fin = min(T - 1, i + int(0.15 * fps))
            break

    fasi = dict(P1=i_setup, P2=p2, P3=p3, P4=i_top, P5=p5, P6=p6, P7=i_imp,
                P8=p8, P9=p9, P10=i_fin)
    tempi = dict(inizio=i_start, top=i_top, impatto=i_imp, vmax=i_vmax)
    return dict(fasi=fasi, indici=tempi)


def sincronizza(fasi_per_vista: dict, fps_per_vista: dict) -> dict:
    """Allinea le viste sull'impatto: restituisce l'offset in secondi di
    ciascuna vista rispetto a un tempo comune (impatto = 0 s)."""
    return {v: -f["indici"]["impatto"] / fps_per_vista[v]
            for v, f in fasi_per_vista.items()}
