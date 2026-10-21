"""Punteggio 0-100 per metrica, categoria e totale, calibrato sul livello."""
from __future__ import annotations

from . import config as C


def punteggio_metrica(valore: float, spec: dict, fattore: float) -> float:
    lo, hi = spec["ideale"]
    if lo <= valore <= hi:
        return 100.0
    distanza = (lo - valore) if valore < lo else (valore - hi)
    tol = spec["tol"] * fattore
    # calo rapido appena fuori dalla banda, poi più graduale
    return max(0.0, 100.0 * (1.0 - min(1.0, distanza / tol) ** 0.75))


def calcola(metriche: dict, handicap):
    livello, fattore = C.livello_da_handicap(handicap)
    dettaglio, categorie = {}, {}
    for nome, r in metriche.items():
        spec = C.METRICHE[nome]
        s_liv = punteggio_metrica(r["valore"], spec, fattore)
        s_abs = punteggio_metrica(r["valore"], spec, 1.0)
        dettaglio[nome] = dict(r, punteggio=s_liv, assoluto=s_abs, **{
            "nome": spec["nome"], "cat": spec["cat"], "peso": spec["peso"],
            "ideale": spec["ideale"], "unita": spec["unita"]})

    peso_disponibile = 0.0
    for cat, peso_cat in C.CATEGORIE.items():
        voci = [d for d in dettaglio.values() if d["cat"] == cat]
        attese = [n for n, s in C.METRICHE.items() if s["cat"] == cat]
        mancanti = [C.METRICHE[n]["nome"] for n in attese if n not in metriche]
        if not voci:
            categorie[cat] = dict(punteggio=None, assoluto=None, peso=peso_cat,
                                  mancanti=mancanti, copertura=0.0)
            continue
        pw = sum(v["peso"] for v in voci)
        categorie[cat] = dict(
            punteggio=sum(v["punteggio"] * v["peso"] for v in voci) / pw,
            assoluto=sum(v["assoluto"] * v["peso"] for v in voci) / pw,
            peso=peso_cat, mancanti=mancanti,
            copertura=pw / sum(C.METRICHE[n]["peso"] for n in attese))
        peso_disponibile += peso_cat

    # Le categorie non misurabili non contano: il loro peso si ridistribuisce
    tot = sum(c["punteggio"] * c["peso"] for c in categorie.values()
              if c["punteggio"] is not None) / max(peso_disponibile, 1e-9)
    tot_abs = sum(c["assoluto"] * c["peso"] for c in categorie.values()
                  if c["assoluto"] is not None) / max(peso_disponibile, 1e-9)
    copertura = sum(c["peso"] * c["copertura"] for c in categorie.values()) / 100.0
    return dict(totale=round(tot), assoluto=round(tot_abs), livello=livello,
                fattore=fattore, categorie=categorie, dettaglio=dettaglio,
                copertura=copertura)
