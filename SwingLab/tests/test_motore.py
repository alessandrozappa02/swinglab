"""Controlli automatici del motore di analisi sullo swing sintetico.

Avvio:  python tests/test_motore.py      (oppure:  python -m pytest tests)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swinglab_core import ballflight, demo, pipeline, report  # noqa: E402


def _analizza(parametri=None, viste=("A", "C"), **profilo):
    tr = demo.tracce(viste, parametri)
    return pipeline.analizza_tracce(tr, pipeline.Profilo(**profilo))


def test_fasi_in_ordine():
    r = _analizza()
    for F in r["fasi"].values():
        valori = [F["fasi"][f"P{i}"] for i in range(1, 11)]
        assert valori == sorted(valori), valori


def test_tempi_dello_swing_sintetico():
    # backswing 0,95 s e rapporto 2,3:1 impostati nel generatore
    r = _analizza()
    assert 2.0 < r["metriche"]["rapporto_tempo"]["valore"] < 2.6
    assert 0.8 < r["metriche"]["durata_backswing"]["valore"] < 1.05


def test_ideale_batte_amatore():
    amatore = _analizza(handicap=18)
    ideale = _analizza(demo.IDEALE, handicap=18)
    assert ideale["punteggi"]["totale"] >= 95
    assert amatore["punteggi"]["totale"] < ideale["punteggi"]["totale"] - 10
    assert not ideale["difetti"]


def test_difetti_attesi_rilevati():
    ids = [d["id"] for d in _analizza(handicap=18)["difetti"]]
    assert "early_extension" in ids and "over_the_top" in ids


def test_livello_cambia_il_punteggio():
    basso = _analizza(handicap=3)["punteggi"]
    alto = _analizza(handicap=None)["punteggi"]
    assert basso["assoluto"] == alto["assoluto"]
    assert alto["totale"] > basso["totale"]


def test_vista_singola_segnala_le_mancanze():
    r = _analizza(viste=("A",))
    assert "over_the_top" not in r["metriche"]
    assert r["mancanti"] and r["volo"]["direzione"]["percorso"] is None


def test_mancino_specchiato():
    r = _analizza(viste=("A",), mancino=True)
    assert r["punteggi"]["totale"] > 0


def test_modello_di_volo_tarato_sul_tour():
    # medie TrackMan PGA Tour: driver 171 mph, ~10,4°, 2545 rpm → 282 yd di carry
    carry, _ = ballflight.carry_m(171, 10.4, 2545)
    assert abs(carry / 0.9144 - 282) < 12
    carry7, _ = ballflight.carry_m(123, 16.3, 7097)
    assert abs(carry7 / 0.9144 - 176) < 12


def test_launch_monitor_sostituisce_la_stima():
    r = _analizza(launch_monitor={"club_mph": 85.0})
    assert r["volo"]["club"]["mph"] == 85.0 and r["volo"]["club"]["conf"] == "alta"


def _finto_slowmo(fps_reale, fps_dichiarato, parametri=None):
    tr = demo.tracce(("A",), parametri, fps=fps_reale)
    tr["A"].fps = fps_dichiarato          # come un file esportato "rallentato"
    return tr


def test_slowmotion_riconosciuto():
    for reale in (120, 240):
        tr = _finto_slowmo(reale, 30)
        r = pipeline.analizza_tracce(tr, pipeline.Profilo())
        assert abs(tr["A"].fps - reale) < 1, tr["A"].fps
        assert 2.0 < r["metriche"]["rapporto_tempo"]["valore"] < 2.6
        assert r["slowmo"]


def test_tempo_reale_non_corretto():
    for fps in (30, 60, 120, 240):
        tr = demo.tracce(("A",), fps=fps)
        r = pipeline.analizza_tracce(tr, pipeline.Profilo())
        assert tr["A"].fps == fps and not r["slowmo"]


def test_fps_indicato_dall_utente_non_cambia():
    tr = _finto_slowmo(240, 30)
    pipeline.analizza_tracce(tr, pipeline.Profilo(), fps_fissati={"A"})
    assert tr["A"].fps == 30


def test_avviso_precisione():
    assert "meno precisa" in _analizza(viste=("C",))["precisione"]
    assert _analizza(viste=("A", "B", "C"))["precisione"] is None


def test_report_html():
    html = report.genera(_analizza(), dimostrativo=True)
    assert html.startswith("<!doctype html>") and "Cosa migliorare" in html


if __name__ == "__main__":
    test = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in test:
        t()
        print("OK ", t.__name__)
    print(f"\nTutti i {len(test)} test superati.")
