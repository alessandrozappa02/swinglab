"""Report HTML autonomo (un solo file, immagini incluse)."""
from __future__ import annotations

import datetime as dt
import html

import numpy as np

from . import config as C
from .annotate import a_base64, annota
from .phases import NOMI_FASI

E = html.escape
CONF_TXT = {"alta": "Confidenza alta", "media": "Confidenza media", "bassa": "Confidenza bassa"}


def _chip(conf):
    if not conf:
        return ""
    return f'<span class="chip c-{conf}">{CONF_TXT[conf]}</span>'


def _fmt_val(v, unita):
    if unita in ("", "× spalle"):
        return f"{v:.2f}{(' ' + unita) if unita else ''}"
    if unita == ":1":
        return f"{v:.1f}:1"
    if unita in ("/2",):
        return f"{v:.0f}{unita}"
    if unita == "s":
        return f"{v:.2f} s"
    return f"{v:.0f} {unita}".replace(" °", "°")


def _ideale(spec):
    lo, hi = spec["ideale"]
    u = spec["unita"]
    if lo == hi:
        return _fmt_val(lo, u)
    return f"{_fmt_val(lo, u)} – {_fmt_val(hi, u)}"


def _colore_punteggio(s):
    if s is None:
        return "var(--muted)"
    if s >= 85:
        return "var(--ok)"
    if s >= 65:
        return "var(--warn)"
    return "var(--bad)"


# ---------------------------------------------------------------------------
# Grafici SVG
# ---------------------------------------------------------------------------

def svg_traiettoria(volo):
    pts = volo["traiettoria"]
    xmax = max(volo["carry"]["hi"], pts[-1][0]) * 1.08
    ymax = max(p[1] for p in pts) * 1.6 + 2
    W, H, ml, mb, mt = 640, 220, 44, 34, 14
    sx = lambda x: ml + x / xmax * (W - ml - 12)
    sy = lambda y: H - mb - y / ymax * (H - mb - mt)
    path = " ".join(f"{'M' if i == 0 else 'L'}{sx(x):.1f},{sy(y):.1f}" for i, (x, y) in enumerate(pts))
    lo, hi = volo["carry"]["lo"], volo["carry"]["hi"]
    griglia = ""
    passo = 25 if xmax < 160 else 50
    for x in range(0, int(xmax) + 1, passo):
        griglia += (f'<line x1="{sx(x):.1f}" y1="{mt}" x2="{sx(x):.1f}" y2="{H - mb}" class="grid"/>'
                    f'<text x="{sx(x):.1f}" y="{H - mb + 18}" class="ax" text-anchor="middle">{x}</text>')
    car = volo["carry"]["m"]
    return f"""
<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Traiettoria stimata della palla">
  {griglia}
  <line x1="{ml}" y1="{H - mb}" x2="{W - 12}" y2="{H - mb}" class="axis"/>
  <rect x="{sx(lo):.1f}" y="{H - mb - 10}" width="{sx(hi) - sx(lo):.1f}" height="10" rx="4" class="band">
    <title>Intervallo probabile del carry: {lo:.0f}–{hi:.0f} m</title></rect>
  <path d="{path}" class="traj"/>
  <circle cx="{sx(car):.1f}" cy="{H - mb}" r="5" class="dot"><title>Carry stimato {car:.0f} m</title></circle>
  <text x="{sx(car):.1f}" y="{H - mb - 16}" class="lbl" text-anchor="middle">{car:.0f} m</text>
  <text x="{ml}" y="{H - 4}" class="ax">metri</text>
  <text x="{sx(pts[len(pts)//2][0]):.1f}" y="{sy(max(p[1] for p in pts)) - 8:.1f}" class="lbl2" text-anchor="middle">apice ≈ {volo['carry']['apice']:.0f} m</text>
</svg>"""


def svg_sequenza(serie, F, fps, picchi):
    if not serie or "bacino" not in serie:
        return ""
    a = F["fasi"]["P4"]
    b = min(len(serie["bacino"]) - 1, F["indici"]["impatto"] + max(2, int(0.03 * fps)))
    imp = F["indici"]["impatto"]
    W, H, ml, mb, mt = 640, 230, 40, 30, 16
    nomi = [("bacino", "Bacino", "s1"), ("busto", "Busto", "s2"), ("braccia", "Braccia", "s3")]
    vals = {k: np.clip(np.asarray(serie[k][a:b + 1]), 0, None) for k, _, _ in nomi}
    norm = {k: v / (v.max() + 1e-9) for k, v in vals.items()}
    n = b - a
    sx = lambda i: ml + i / max(n, 1) * (W - ml - 70)
    sy = lambda y: H - mb - y * (H - mb - mt)
    out = []
    for k, etichetta, cls in nomi:
        y = norm[k]
        d = " ".join(f"{'M' if i == 0 else 'L'}{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(y))
        ip = int(round(picchi[k] * fps)) + imp - a
        ip = min(max(ip, 0), len(y) - 1)
        t_ms = picchi[k] * 1000
        out.append(f'<path d="{d}" class="ln {cls}"/>'
                   f'<circle cx="{sx(ip):.1f}" cy="{sy(y[ip]):.1f}" r="5" class="pk {cls}">'
                   f'<title>{etichetta}: picco a {t_ms:+.0f} ms dall\'impatto</title></circle>'
                   f'<text x="{sx(len(y) - 1) + 6:.1f}" y="{sy(y[-1]) + 4:.1f}" class="lbl">{etichetta}</text>')
    xi = sx(imp - a)
    return f"""
<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Sequenza cinematica in discesa">
  <line x1="{ml}" y1="{H - mb}" x2="{W - 70}" y2="{H - mb}" class="axis"/>
  <line x1="{xi:.1f}" y1="{mt}" x2="{xi:.1f}" y2="{H - mb}" class="grid strong"/>
  <text x="{xi:.1f}" y="{H - mb + 18}" class="ax" text-anchor="middle">impatto</text>
  <text x="{ml}" y="{H - mb + 18}" class="ax">top</text>
  {''.join(out)}
</svg>"""


# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#f6f4ee;--card:#fffdf8;--ink:#1d2420;--ink2:#4b5550;--muted:#8a918c;--line:#e3dfd3;
--brand:#1f5c3d;--brand2:#e9f1ea;--ok:#2f8a4f;--warn:#c98500;--bad:#c4423b;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--band:#2a78d633}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141816;--card:#1c211e;--ink:#eef0ec;
--ink2:#c3c8c2;--muted:#8d948e;--line:#2d3430;--brand:#7cc79a;--brand2:#22302a;--ok:#5cbf7d;--warn:#e0a52a;
--bad:#e66767;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--band:#3987e540}}
:root[data-theme="dark"]{--bg:#141816;--card:#1c211e;--ink:#eef0ec;--ink2:#c3c8c2;--muted:#8d948e;--line:#2d3430;
--brand:#7cc79a;--brand2:#22302a;--ok:#5cbf7d;--warn:#e0a52a;--bad:#e66767;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--band:#3987e540}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:28px 16px 60px}
h1{font:700 30px/1.15 Georgia,"Times New Roman",serif;margin:0 0 4px;letter-spacing:-.01em}
h2{font:700 21px/1.2 Georgia,serif;margin:42px 0 14px;padding-top:10px;border-top:1px solid var(--line)}
h3{font-size:17px;margin:0 0 6px}
.sub{color:var(--ink2);margin:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
.hero{display:grid;grid-template-columns:200px 1fr;gap:18px;align-items:center;margin-top:20px}
.score{width:180px;height:180px;border-radius:50%;display:grid;place-items:center;margin:auto;
background:conic-gradient(var(--brand) calc(var(--v)*1%),var(--line) 0)}
.score>div{width:146px;height:146px;border-radius:50%;background:var(--card);display:grid;place-items:center;text-align:center}
.score b{font:700 52px/1 Georgia,serif;display:block}.score span{font-size:13px;color:var(--ink2)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:10px 0 0}
.kv dt{color:var(--ink2)}.kv dd{margin:0;font-weight:600}
.cats{display:grid;gap:8px;margin-top:14px}
.cat{display:grid;grid-template-columns:110px 1fr 46px;gap:10px;align-items:center;font-size:14px}
.bar{height:10px;background:var(--line);border-radius:5px;overflow:hidden}
.bar i{display:block;height:100%;border-radius:5px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.stat{padding:14px}.stat .t{font-size:13px;color:var(--ink2)}.stat .v{font:700 26px/1.2 Georgia,serif;margin:4px 0}
.stat .r{font-size:13px;color:var(--ink2)}
.chip{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;border:1px solid var(--line);margin-top:6px}
.c-alta{color:var(--ok);border-color:var(--ok)}.c-media{color:var(--warn);border-color:var(--warn)}.c-bassa{color:var(--bad);border-color:var(--bad)}
.note{background:var(--brand2);border-radius:12px;padding:14px 16px;font-size:14px}
.fault{display:grid;grid-template-columns:260px 1fr;gap:18px;margin-bottom:16px}
.fault img,.good img{width:100%;border-radius:10px;display:block}
.num{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--brand);color:var(--card);font-weight:700;margin-right:8px}
.lab{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:12px 0 2px}
.drill{border-left:3px solid var(--brand);padding:6px 0 6px 12px;margin:8px 0}
.drill ol{margin:4px 0 0;padding-left:20px}
.feel{font-style:italic;background:var(--brand2);padding:8px 12px;border-radius:8px;margin-top:10px}
.good{display:grid;grid-template-columns:120px 1fr;gap:12px;align-items:center}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px}
.strip figure{margin:0}.strip img{width:100%;border-radius:8px}.strip figcaption{font-size:12px;color:var(--ink2);text-align:center}
.vs{display:grid;grid-template-columns:repeat(8,1fr);gap:6px}
.vs figure{margin:0}.vs img{width:100%;border-radius:8px}.vs figcaption{font-size:12px;text-align:center;color:var(--ink2)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--ink2);font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums}
.chart{width:100%;height:auto}.chart .grid{stroke:var(--line);stroke-width:1}.chart .grid.strong{stroke:var(--muted);stroke-dasharray:4 4}
.chart .axis{stroke:var(--muted)}.chart .ax{fill:var(--ink2);font-size:12px}.chart .lbl{fill:var(--ink);font-size:13px;font-weight:600}
.chart .lbl2{fill:var(--ink2);font-size:12px}.chart .traj{fill:none;stroke:var(--s1);stroke-width:2.5}
.chart .band{fill:var(--band)}.chart .dot{fill:var(--s1);stroke:var(--card);stroke-width:2}
.chart .ln{fill:none;stroke-width:2}.chart .ln.s1{stroke:var(--s1)}.chart .ln.s2{stroke:var(--s2)}.chart .ln.s3{stroke:var(--s3)}
.chart .pk{stroke:var(--card);stroke-width:2}.chart .pk.s1{fill:var(--s1)}.chart .pk.s2{fill:var(--s2)}.chart .pk.s3{fill:var(--s3)}
.legend{display:flex;gap:16px;font-size:13px;color:var(--ink2);margin-top:6px}.legend i{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px}
.week{margin-bottom:12px}.sess{border-top:1px solid var(--line);padding:8px 0}.sess:first-of-type{border-top:0}
.sess ul{margin:4px 0;padding-left:18px}
.warn{color:var(--bad)}
.banner{background:#fff3d6;color:#5a4300;border:1px solid #f0d58a;border-radius:10px;padding:10px 14px;font-size:14px;margin-top:14px}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .banner{background:#3a3014;color:#f2dfa5;border-color:#6b5a22}}
@media (max-width:700px){.hero{grid-template-columns:1fr}.fault{grid-template-columns:1fr}.vs{grid-template-columns:repeat(4,1fr)}
.cat{grid-template-columns:90px 1fr 40px}}
"""


def genera(r, titolo="Report SwingLab", dimostrativo=False) -> str:
    p = r["profilo"]
    pt = r["punteggi"]
    volo = r["volo"]
    tracce, fasi = r["tracce"], r["fasi"]
    oggi = dt.date.today().strftime("%d/%m/%Y")
    viste = list(tracce.keys())

    def img_metrica(nome, fase, vista, larg=360):
        v = vista if vista in tracce else viste[0]
        val = r["metriche"].get(nome, {}).get("valore")
        im = annota(tracce[v], fasi[v], nome, fase, p.mancino, val)
        return a_base64(im, larg), v

    # ---- riepilogo -------------------------------------------------------
    forza = r["forze"][0]["testo"] if r["forze"] else "Struttura generale dello swing."
    prio = r["difetti"][0]["titolo"] if r["difetti"] else "Nessun difetto rilevante: lavora su costanza e ritmo."
    cat_html = ""
    for cat, c in pt["categorie"].items():
        s = c["punteggio"]
        if s is None:
            cat_html += (f'<div class="cat"><span>{cat}</span><div class="bar"></div>'
                         f'<span style="color:var(--muted)">n.d.</span></div>')
        else:
            cat_html += (f'<div class="cat"><span>{cat}</span><div class="bar"><i style="width:{s:.0f}%;'
                         f'background:{_colore_punteggio(s)}"></i></div><b>{s:.0f}</b></div>')

    hcp = "principiante (senza handicap)" if p.handicap is None else f"handicap {p.handicap:g}"
    banner = ('<div class="banner"><b>Report dimostrativo.</b> Generato con uno swing sintetico '
              '(golfer 3D simulato con difetti tipici di un amatore), non con un video reale.</div>'
              if dimostrativo else "")
    if r.get("precisione"):
        banner += f'<div class="banner"><b>Precisione dell\'analisi.</b> {E(r["precisione"])}</div>'
    copertura = pt["copertura"]
    cop_txt = ("" if copertura > 0.95 else
               f'<p class="sub" style="margin-top:8px">Copertura dell\'analisi: {copertura*100:.0f}% delle '
               f'metriche (alcune richiedono un\'altra angolazione).</p>')

    riepilogo = f"""
<div class="card hero">
  <div class="score" style="--v:{pt['totale']}"><div><div><b>{pt['totale']}</b><span>su 100</span></div></div></div>
  <div>
    <dl class="kv">
      <dt>Punto di forza</dt><dd>{E(forza)}</dd>
      <dt>Priorità n. 1</dt><dd>{E(prio)}</dd>
      <dt>Livello di riferimento</dt><dd>{E(pt['livello'])} · punteggio assoluto {pt['assoluto']}/100</dd>
    </dl>
    <div class="cats">{cat_html}</div>
    {cop_txt}
  </div>
</div>"""

    # ---- volo della palla ------------------------------------------------
    c, b = volo["club"], volo["palla"]
    kmh = 1.609344
    def stat(t, v, rng, conf, extra=""):
        return (f'<div class="card stat"><div class="t">{t}</div><div class="v">{v}</div>'
                f'<div class="r">{rng}</div>{extra}{_chip(conf)}</div>')
    cards = "".join([
        stat("Velocità testa del bastone", f"{c['mph']*kmh:.0f} km/h",
             f"{c['lo']*kmh:.0f}–{c['hi']*kmh:.0f} km/h · {c['mph']:.0f} mph", c["conf"]),
        stat("Velocità della palla", f"{b['mph']*kmh:.0f} km/h",
             f"{b['lo']*kmh:.0f}–{b['hi']*kmh:.0f} km/h · smash {b['smash']:.2f}", b["conf"]),
        stat("Angolo di lancio", f"{volo['lancio']['deg']:.0f}°",
             f"{volo['lancio']['lo']:.0f}–{volo['lancio']['hi']:.0f}° (tipico del bastone)", "bassa"),
        stat("Spin indicativo", f"{volo['spin']['rpm']:.0f} rpm",
             f"{volo['spin']['lo']:.0f}–{volo['spin']['hi']:.0f} rpm", "bassa"),
        stat("Carry", f"{volo['carry']['m']:.0f} m",
             f"{volo['carry']['lo']:.0f}–{volo['carry']['hi']:.0f} m · {volo['carry']['m']/0.9144:.0f} yd",
             volo["carry"]["conf"]),
        stat("Distanza totale", f"{volo['totale']['m']:.0f} m",
             f"{volo['totale']['lo']:.0f}–{volo['totale']['hi']:.0f} m · {volo['totale']['m']/0.9144:.0f} yd", "bassa"),
    ])
    dirz = volo["direzione"]
    perc = (f" Percorso stimato del bastone: {dirz['percorso']:+.0f}° "
            f"({'dall’interno' if dirz['percorso'] > 0 else 'dall’esterno'})." if dirz["percorso"] is not None else "")
    lm = p.launch_monitor or {}
    lm_html = ""
    if lm:
        righe = []
        if lm.get("club_mph"):
            righe.append(("Velocità bastone (mph)", lm["club_mph"], None))
        if lm.get("ball_mph"):
            righe.append(("Velocità palla (mph)", lm["ball_mph"], None))
        if lm.get("carry_m"):
            righe.append(("Carry (m)", lm["carry_m"], volo["carry"]["m"]))
        lm_html = ('<h3 style="margin-top:16px">Confronto con il launch monitor</h3><table><tr><th>Dato</th>'
                   '<th class="n">Launch monitor</th><th class="n">Stima app</th></tr>' +
                   "".join(f'<tr><td>{a}</td><td class="n">{x:.0f}</td><td class="n">'
                           f'{"—" if y is None else f"{y:.0f}"}</td></tr>' for a, x, y in righe) +
                   "</table><p class='sub'>I dati misurati sostituiscono le stime nei calcoli.</p>")

    volo_html = f"""
<p class="sub">Bastone: <b>{E(volo['bastone'])}</b> · fonte della velocità: {E(volo['fonte'])}
(vista {E(volo['vista_velocita'])}).</p>
<div class="grid2" style="margin-top:12px">{cards}</div>
<div class="card" style="margin-top:12px">
  <h3>Traiettoria stimata (vista laterale)</h3>
  {svg_traiettoria(volo)}
  <p class="sub" style="font-size:13px">Linea: volo centrale. Banda sull'asse: intervallo probabile del carry (80%).</p>
</div>
<div class="card" style="margin-top:12px"><h3>Direzione e curva probabili {_chip(dirz['conf'])}</h3>
<p style="margin:0">{E(dirz['testo'])}{E(perc)}</p></div>
{lm_html}
<div class="note" style="margin-top:12px"><b>Sono stime, non misure.</b> Da un video del telefono non si vedono
la faccia del bastone, il punto d'impatto e il volo reale. La velocità viene ricavata dal movimento delle mani e
combinata con i valori tipici del tuo livello; lancio e spin sono quelli tipici del bastone.
{' '.join(E(n) for n in volo['note'])}<br><b>Per essere più precisi:</b> slow motion a 120–240 fps, telefono su
treppiede a 3–4 m, statura inserita, video da dietro per la direzione e, se puoi, qualche colpo con un launch
monitor per tarare le stime.</div>"""

    # ---- cosa va bene ----------------------------------------------------
    bene = ""
    for f_ in r["forze"]:
        src, v = img_metrica(f_["metrica"], f_["fase"], f_["vista"], 240)
        d = pt["dettaglio"][f_["metrica"]]
        bene += (f'<div class="card good" style="margin-bottom:10px"><img src="{src}" alt="">'
                 f'<div><b>{E(f_["testo"])}</b><p class="sub">{E(d["nome"])}: '
                 f'{_fmt_val(d["valore"], d["unita"])} (ideale {_ideale(C.METRICHE[f_["metrica"]])}) · '
                 f'{NOMI_FASI[f_["fase"]]} ({f_["fase"]}), vista {E(v)}</p></div></div>')
    if not bene:
        bene = '<p class="sub">Nessuna metrica è ancora nella fascia ideale: è normale all\'inizio.</p>'

    # ---- cosa migliorare ---------------------------------------------------
    migl = ""
    for n, f_ in enumerate(r["difetti"], 1):
        src, v = img_metrica(f_["metrica"], f_["fase"], f_["vista"], 260)
        det = [pt["dettaglio"][m] for m in f_["metriche"]]
        misure = "; ".join(f'{d["nome"]}: {_fmt_val(d["valore"], d["unita"])} '
                           f'(ideale {_ideale(C.METRICHE[m])})' for d, m in zip(det, f_["metriche"]))
        drills = "".join(f'<div class="drill"><b>{E(t)}</b><ol>' +
                         "".join(f"<li>{E(s)}</li>" for s in passi) + "</ol></div>"
                         for t, passi in f_["drill"][:2])
        conf = min((d["conf"] for d in det), key=lambda c_: {"alta": 2, "media": 1, "bassa": 0}[c_])
        migl += f"""
<div class="card fault">
  <div><img src="{src}" alt=""><p class="sub" style="font-size:13px;margin-top:6px">
  {NOMI_FASI[f_['fase']]} ({f_['fase']}), vista {E(v)}. Linee tratteggiate: posizione al setup;
  arancio: posizione attuale.</p></div>
  <div>
    <h3><span class="num">{n}</span>{E(f_['titolo'])}</h3>{_chip(conf)}
    <div class="lab">Cosa succede</div><p style="margin:0">{E(f_['descrizione'])}</p>
    <p class="sub" style="font-size:14px;margin:4px 0 0">{E(misure)}</p>
    <div class="lab">Perché succede</div><p style="margin:0">{E(f_['perche'])}</p>
    <div class="lab">Effetto sulla palla</div><p style="margin:0">{E(f_['palla'])}</p>
    <div class="lab">Esercizi</div>{drills}
    <div class="feel"><b>Feel:</b> {E(f_['feel'])}</div>
  </div>
</div>"""
    if not migl:
        migl = '<p>Nessun difetto sopra la soglia per il tuo livello. Continua a lavorare su costanza e ritmo.</p>'

    # ---- piano -------------------------------------------------------------
    piano_html = ""
    for s in sorted({x["settimana"] for x in r["piano"]}):
        sess = [x for x in r["piano"] if x["settimana"] == s]
        titolo_s = "movimento e sensazioni, a bassa velocità" if s == 1 else "velocità e trasferimento al gioco"
        piano_html += f'<div class="card week"><h3>Settimana {s}: {titolo_s}</h3>'
        for x in sess:
            piano_html += (f'<div class="sess"><b>Sessione {x["sessione"]}</b> (circa '
                           f'{sum(int(b_[0][:-1]) for b_ in x["blocchi"])} minuti)<ul>' +
                           "".join(f"<li><b>{E(b_[0])}</b> {E(b_[1])}</li>" for b_ in x["blocchi"]) +
                           "</ul></div>")
        piano_html += "</div>"

    # ---- fotogrammi chiave e confronto ------------------------------------
    strip = ""
    for v in viste:
        figs = ""
        for ph in ("P1", "P2", "P4", "P6", "P7", "P10"):
            im = tracce[v].frame(fasi[v]["fasi"][ph])
            if im is None:
                continue
            from .annotate import scheletro
            scheletro(im, tracce[v].kp[fasi[v]["fasi"][ph]])
            figs += f'<figure><img src="{a_base64(im, 180, 75)}" alt=""><figcaption>{ph} · {NOMI_FASI[ph]}</figcaption></figure>'
        strip += f'<h3 style="margin-top:14px">Vista {v} – {E(C.VISTE[v]["nome"])}</h3><div class="strip">{figs}</div>'

    confronto = ""
    from . import demo, phases as PH
    from .annotate import scheletro as _sk
    for v in viste:
        rif = demo.riferimento(v)
        Fr = PH.rileva_fasi(rif.kp, rif.fps)
        figs = ""
        for ph in ("P1", "P4", "P7", "P10"):
            a_ = tracce[v].frame(fasi[v]["fasi"][ph])
            b_ = rif.frame(Fr["fasi"][ph])
            if a_ is None:
                continue
            _sk(a_, tracce[v].kp[fasi[v]["fasi"][ph]])
            _sk(b_, rif.kp[Fr["fasi"][ph]])
            figs += (f'<figure><img src="{a_base64(a_, 200, 75)}" alt=""><figcaption>Tu · {NOMI_FASI[ph]}</figcaption></figure>'
                     f'<figure><img src="{a_base64(b_, 200, 75)}" alt=""><figcaption>Modello · {NOMI_FASI[ph]}</figcaption></figure>')
        confronto += f'<h3 style="margin-top:14px">Vista {v}</h3><div class="vs">{figs}</div>'

    # ---- sequenza ----------------------------------------------------------
    v_seq = next((v for v in viste if "bacino" in r["per_vista"][v]["serie"]), None)
    seq_html = ""
    if v_seq:
        seq = pt["dettaglio"].get("sequenza")
        seq_html = f"""
<div class="card"><h3>Sequenza cinematica in discesa (vista {v_seq})</h3>
{svg_sequenza(r['per_vista'][v_seq]['serie'], fasi[v_seq], tracce[v_seq].fps, r['per_vista'][v_seq]['metriche']['sequenza']['picchi'])}
<div class="legend"><span><i style="background:var(--s1)"></i>Bacino</span><span><i style="background:var(--s2)"></i>Busto</span>
<span><i style="background:var(--s3)"></i>Braccia</span></div>
<p class="sub" style="font-size:14px">Velocità di rotazione normalizzate (picco = 1). Nell'ordine ideale i picchi
arrivano da sinistra a destra: bacino, poi busto, poi braccia. Il punto segna il picco di ciascun segmento
(passaci sopra per il tempo in millisecondi).
{f"Il tuo swing: {seq['valore']:.0f} passaggi su 2 nell'ordine giusto." if seq else ""} Stima di confidenza bassa.</p></div>"""

    # ---- tabella metodo ----------------------------------------------------
    righe = ""
    for cat, cc in pt["categorie"].items():
        voci = [(n_, d) for n_, d in pt["dettaglio"].items() if d["cat"] == cat]
        tot = sum(d["peso"] for _, d in voci) or 1
        sc_txt = "n.d." if cc["punteggio"] is None else "%.0f/100" % cc["punteggio"]
        righe += (f'<tr><th colspan="6" style="padding-top:14px">{cat} · peso {cc["peso"]}% · '
                  f'{sc_txt}</th></tr>')
        for n_, d in voci:
            righe += (f'<tr><td>{E(d["nome"])}</td><td class="n">{_fmt_val(d["valore"], d["unita"])}</td>'
                      f'<td class="n">{_ideale(C.METRICHE[n_])}</td><td class="n">{d["punteggio"]:.0f}</td>'
                      f'<td class="n">{d["peso"] / tot * 100:.0f}%</td><td>{E(d["vista"])} · {d["conf"]}</td></tr>')
        if cc["mancanti"]:
            righe += (f'<tr><td colspan="6" class="sub" style="font-size:13px">Non calcolate: '
                      f'{E(", ".join(cc["mancanti"]))}</td></tr>')
    metodo = f"""
<p>Ogni metrica riceve 100 punti se cade nella fascia ideale; fuori dalla fascia il punteggio scende in base
alla distanza, con una tolleranza che si allarga per il tuo livello ({E(pt['livello'])}: tolleranza ×{pt['fattore']:.1f}).
Il punteggio di categoria è la media pesata delle sue metriche; il totale è la media pesata delle categorie
(Setup 15, Backswing 20, Transizione 15, Impatto 25, Finish 10, Tempo 15). Le categorie che non si possono
misurare con i video caricati non contano e il loro peso viene ridistribuito. Il <b>punteggio assoluto</b>
usa le tolleranze di un giocatore avanzato: è il numero da confrontare tra giocatori diversi.</p>
<div class="card" style="overflow-x:auto"><table><tr><th>Metrica</th><th class="n">Valore</th><th class="n">Ideale</th>
<th class="n">Punti</th><th class="n">Peso</th><th>Vista · confidenza</th></tr>{righe}</table></div>"""

    # ---- qualità e limiti --------------------------------------------------
    qual = ""
    for v in viste:
        av = r["avvisi"].get(v, [])
        fps = tracce[v].fps
        qual += (f'<li><b>Vista {v}</b> ({E(C.VISTE[v]["nome"])}), {fps:.0f} fps, '
                 f'tempi allineati sull\'impatto: ' +
                 (", ".join(E(a) for a in av) if av else "nessun problema rilevato") + "</li>")
    manc = "".join(f"<li><b>{E(a)}</b> mancante: non sono disponibili {E(b_.lower())}.</li>"
                   for a, b_ in r["mancanti"])

    lato = "mancino" if p.mancino else "destro"
    alt = f"{p.altezza_cm:.0f} cm" if p.altezza_cm else "non indicata (usati 175 cm)"
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(titolo)}</title>
<style>{CSS}</style></head><body><div class="wrap">
<p class="sub" style="font-weight:600;color:var(--brand);letter-spacing:.04em">SWINGLAB</p>
<h1>Analisi del tuo swing</h1>
<p class="sub">{oggi} · golfer {lato}, {E(hcp)} · statura {E(alt)} · bastone {E(p.bastone)} · viste {", ".join(viste)}</p>
{banner}
{riepilogo}
<h2>Dati di volo stimati</h2>{volo_html}
<h2>Cosa va bene</h2>{bene}
<h2>Cosa migliorare, in ordine di priorità</h2>{migl}
<h2>Piano di allenamento: 2 settimane, 3 sessioni a settimana</h2>{piano_html}
<h2>Fasi dello swing (P1–P10)</h2>{strip}
<h2>Il tuo swing e il modello di riferimento</h2>
<p class="sub">Fotogrammi allineati sulle stesse fasi. Il modello è un golfer sintetico con valori ideali
per ogni metrica.</p>{confronto}
<h2>Transizione</h2>{seq_html}
<h2>Come è stato calcolato il punteggio</h2>{metodo}
<h2>Qualità dei video e limiti</h2>
<ul>{qual}{manc}</ul>
<p class="sub" style="font-size:13px">I video sono stati elaborati in una cartella temporanea e cancellati
alla fine dell'analisi: non vengono conservati. Fonti dei valori di
riferimento: medie TrackMan PGA/LPGA Tour e TrackMan Combine (velocità, smash, lancio, spin, carry);
proporzioni antropometriche di Drillis & Contini per la calibrazione con la statura.</p>
</div></body></html>"""
