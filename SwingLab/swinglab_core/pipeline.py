"""Orchestrazione: dai video (o dalle tracce) al risultato completo."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ballflight, coaching, config as C, metrics, phases, scoring
from . import video as V


@dataclass
class Profilo:
    mancino: bool = False
    bastone: str = "Ferro 7"
    altezza_cm: float | None = None
    handicap: float | None = None      # None = principiante senza handicap
    launch_monitor: dict = field(default_factory=dict)


# Analisi che richiedono una certa angolazione
REQUISITI = [
    ("C", "Piano dello swing e over the top, early extension, postura al setup, "
          "direzione e curva della palla"),
    ("A", "Sway e slide del bacino, trasferimento del peso, braccio guida al top, "
          "lag dei polsi, larghezza dei piedi"),
]


def analisi_mancanti(viste_presenti):
    tipi = {C.VISTE[v]["tipo"] for v in viste_presenti}
    out = []
    if "DTL" not in tipi:
        out.append(("Da dietro (C)", REQUISITI[0][1]))
    if not tipi & {"FO", "FO2"}:
        out.append(("Laterale (A o B)", REQUISITI[1][1]))
    return out


AVVISO_PRECISIONE = {
    1: ("Hai caricato un solo video: l'analisi funziona, ma con meno video è meno precisa e alcune "
        "metriche non sono disponibili. Per un risultato migliore aggiungi le altre angolazioni "
        "(ideale: laterale A + da dietro C)."),
    2: ("Hai caricato due video: l'analisi è buona. Con la terza angolazione alcune misure "
        "diventano più affidabili."),
}


def correggi_slowmotion(tracce: dict, fps_fissati=(), avvisi=None):
    """Riconosce i video slow motion esportati a velocità rallentata e
    corregge il frame rate (a meno che l'utente non l'abbia indicato)."""
    from .pose import pulisci
    note = {}
    for v, tr in tracce.items():
        if v in fps_fissati:
            continue
        f = phases.stima_fattore_slowmo(tr.kp, tr.fps)
        if f > 1:
            nuovo = tr.fps * f
            note[v] = (f"Rilevato uno slow motion rallentato ×{f}: frame rate reale stimato "
                       f"{nuovo:.0f} fps (il file dichiara {tr.fps:.0f}). Se non è corretto, "
                       "indica il frame rate reale nel campo sotto il video.")
            tr.fps = nuovo
            tr.kp = pulisci(tr.kp, nuovo)
            if tr.mondo is not None:
                tr.mondo = pulisci(tr.mondo, nuovo)
            if avvisi is not None:
                avvisi.setdefault(v, []).append(note[v])
    return note


def analizza_tracce(tracce: dict, profilo: Profilo, avvisi_video=None, fps_fissati=()) -> dict:
    altezza_m = (profilo.altezza_cm or C.ALTEZZA_DEFAULT_M * 100) / 100
    fasi, per_vista, avvisi = {}, {}, dict(avvisi_video or {})
    slowmo = correggi_slowmotion(tracce, fps_fissati, avvisi)
    for v, tr in tracce.items():
        F = phases.rileva_fasi(tr.kp, tr.fps)
        fasi[v] = F
        per_vista[v] = metrics.calcola_vista(tr, F, profilo.mancino, altezza_m)
        av = avvisi.setdefault(v, [])
        av += V.controlli_inquadratura(tr.kp, tr.vis, tr.larghezza, tr.altezza, F["fasi"]["P1"])
        if tr.path:
            fr = tr.frame(F["fasi"]["P1"])
            if fr is not None and not V.cerca_palla(fr, tr.kp[F["fasi"]["P1"]]):
                av.append("Palla non individuata al setup: verifica che sia visibile "
                          "(serve per i riferimenti visivi).")
        if F["fasi"]["P10"] >= tr.T - 2:
            av.append("Il video termina prima della fine del finish: lascia 1-2 s dopo lo swing.")

    tipi = {v: tr.tipo for v, tr in tracce.items()}
    finali = metrics.unisci(per_vista, tipi)
    punti = scoring.calcola(finali, profilo.handicap)

    # Velocità mani: preferenza alla vista frontale
    ordine = sorted(per_vista, key=lambda v: metrics.ORDINE_TIPO[tipi[v]])
    v_vel = ordine[0]
    fps_vel = tracce[v_vel].fps
    ott = finali.get("over_the_top")
    percorso = ballflight.percorso_da_over_the_top(ott["valore"] if ott else None)
    volo = ballflight.stima(per_vista[v_vel]["v_mani"], profilo.bastone, profilo.handicap,
                            fps_vel, profilo.altezza_cm is not None, percorso,
                            profilo.launch_monitor)
    volo["vista_velocita"] = v_vel

    difetti = coaching.diagnosi(punti, profilo.mancino)
    forze = coaching.punti_di_forza(punti, profilo.mancino)
    sync = phases.sincronizza(fasi, {v: t.fps for v, t in tracce.items()})

    return dict(profilo=profilo, tracce=tracce, fasi=fasi, per_vista=per_vista,
                metriche=finali, punteggi=punti, volo=volo, difetti=difetti,
                forze=forze, piano=coaching.piano(difetti), sync=sync,
                avvisi=avvisi, mancanti=analisi_mancanti(tracce.keys()), slowmo=slowmo,
                precisione=AVVISO_PRECISIONE.get(len(tracce)))


def analizza_video(video: dict, profilo: Profilo, fps_manuali=None, progress=None) -> dict:
    """video: {"A": percorso, ...} già validati."""
    from .pose import stima_posa
    fps_manuali = {k: f for k, f in (fps_manuali or {}).items() if f}
    tracce, avvisi = {}, {}
    for v, path in video.items():
        info = V.info_video(path, fps_manuali.get(v))
        tracce[v] = stima_posa(path, v, C.VISTE[v]["tipo"], info["fps"], progress)
    return analizza_tracce(tracce, profilo, avvisi, fps_fissati=set(fps_manuali))
