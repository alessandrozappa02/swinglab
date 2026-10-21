"""Video commentato: lo swing a rallentatore con gli assi del corpo e il
commento delle correzioni, lungo circa 25 secondi.

Struttura del video:
- breve titolo sul primo fotogramma;
- riproduzione rallentata dallo setup al finish, con scheletro, assi
  (colonna, spalle, bacino) e riferimenti della posizione di partenza;
- avvisi "live" quando testa o bacino escono dai riferimenti;
- pause sulle fasi dove c'è una correzione (o un punto di forza), con il
  commento del maestro;
- riepilogo finale.
Il file è un mp4 H.264 (si apre in qualsiasi browser e telefono).
"""
from __future__ import annotations

import os
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import config as C
from .metrics import lati, medio
from .phases import NOMI_FASI

FPS_OUT = 30
DURATA_TARGET_S = 25.0
LARGHEZZA_OUT = 720

# colori RGB (il disegno avviene in RGB con Pillow)
GIALLO = (242, 201, 76)
ARANCIO = (240, 140, 60)
AZZURRO = (90, 190, 230)
VERDE = (110, 210, 140)
BIANCO = (245, 245, 240)
ROSSO = (235, 80, 70)
FONDO = (15, 43, 30)

# frase breve da dire "a voce" sul video, per ogni difetto
FRASI = {
    "early_extension": "Il bacino va verso la palla: resta seduto, sedere indietro",
    "abbassamento": "La testa scende in discesa: mantieni la tua altezza",
    "sway": "Il bacino scivola indietro: ruota sul posto, non spostarti",
    "reverse_pivot": "Al top il peso va verso il bersaglio: caricalo sul piede dietro",
    "over_the_top": "Discesa dall'esterno: lascia cadere il gomito verso il fianco",
    "troppo_dentro": "Discesa troppo da dentro: il bastone esce verso destra",
    "sequenza": "Partono prima le spalle: inizia la discesa con il bacino",
    "casting": "Rilasci i polsi troppo presto: trascina il grip verso la palla",
    "peso_dietro": "All'impatto il peso è ancora dietro: porta la fibbia avanti",
    "slide": "Il bacino scivola verso il bersaglio: ruota, non spingere",
    "spalle_livellate": "Spalla dietro troppo alta all'impatto: lasciala scendere",
    "tilt_setup": "Spalle troppo livellate al setup: spalla dietro un po' più bassa",
    "rotazione_corta": "Rotazione delle spalle corta: gira la schiena verso il bersaglio",
    "overswing": "Backswing troppo lungo: fermati prima",
    "bacino_eccessivo": "Il bacino gira troppo: tieni flesso il ginocchio dietro",
    "braccio_piegato": "Braccio guida piegato al top: allunga l'arco",
    "tempo_veloce": "Ritmo affrettato: conta uno-due-tre nel backswing, quattro all'impatto",
    "tempo_lento": "Ritmo troppo lento: un movimento unico e fluido",
    "finish": "Finish instabile: chiudi in equilibrio sul piede avanti",
    "postura_eretta": "Postura troppo dritta: piegati dalle anche",
    "postura_curva": "Postura troppo curva: schiena lunga",
    "postura_seduta": "Ginocchia troppo piegate: gambe morbide, non sedute",
    "lontano_palla": "Troppo lontano dalla palla: braccia sotto le spalle",
    "vicino_palla": "Troppo vicino alla palla: lascia spazio alle braccia",
    "stance": "Larghezza dei piedi da sistemare",
}

_FONT_CACHE = {}


def _font(size, grassetto=False):
    chiave = (size, grassetto)
    if chiave not in _FONT_CACHE:
        f = None
        for nome in (("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf") if grassetto
                     else ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf")):
            try:
                f = ImageFont.truetype(nome, size)
                break
            except OSError:
                continue
        _FONT_CACHE[chiave] = f or ImageFont.load_default(size=size)
    return _FONT_CACHE[chiave]


def _a_capo(draw, testo, font, larghezza):
    righe, riga = [], ""
    for parola in testo.split():
        prova = (riga + " " + parola).strip()
        if draw.textlength(prova, font=font) <= larghezza:
            riga = prova
        else:
            if riga:
                righe.append(riga)
            riga = parola
    if riga:
        righe.append(riga)
    return righe


def _linea_tratteggiata(draw, a, b, col, w=2, passo=12):
    a, b = np.array(a, float), np.array(b, float)
    n = max(1, int(np.linalg.norm(b - a) / passo))
    for k in range(0, n, 2):
        p, q = a + (b - a) * k / n, a + (b - a) * min(k + 1, n) / n
        draw.line([tuple(p), tuple(q)], fill=col, width=w)


def _estendi(a, b, f):
    """Segmento a→b allungato di un fattore f su entrambi i lati."""
    m, d = (a + b) / 2, (b - a) / 2
    return m - d * f, m + d * f


class _Disegno:
    def __init__(self, tr, F, mancino, ppm, scala):
        self.tr, self.F, self.mancino, self.ppm, self.s = tr, F, mancino, ppm, scala
        self.g, self.d = lati(mancino)
        p1 = F["fasi"]["P1"]
        k0 = tr.kp[p1] * scala
        self.testa0 = k0[C.NASO].copy()
        self.bacino0 = medio(k0, C.ANCA_SX, C.ANCA_DX)
        self.spalle0 = medio(k0, C.SPALLA_SX, C.SPALLA_DX)
        self.raggio_testa = max(18.0, 0.55 * np.linalg.norm(k0[C.SPALLA_SX] - k0[C.SPALLA_DX]) / 2)
        self.cm_px = 100.0 / (ppm * scala)          # cm per pixel nell'immagine di uscita
        mani = (tr.kp[:, C.POLSO_SX] + tr.kp[:, C.POLSO_DX]) / 2 * scala
        self.verso_palla = np.sign(mani[p1, 0] - self.bacino0[0]) or 1.0
        self.verso_bersaglio = np.sign(k0[self.g["spalla"], 0] - k0[self.d["spalla"], 0]) or 1.0

    def avvisi_live(self, i):
        """Controlli fotogramma per fotogramma: restituisce le parti da evidenziare."""
        k = self.tr.kp[i] * self.s
        f = self.F["fasi"]
        out = {}
        dt = k[C.NASO] - self.testa0
        soglia_testa = 6.0
        if self.tr.tipo == "DTL":
            if dt[1] * self.cm_px > soglia_testa and f["P4"] <= i <= f["P7"] + 2:
                out["testa"] = "La testa scende"
            elif abs(dt[0]) * self.cm_px > 8:
                out["testa"] = "La testa si muove"
            bac = medio(k, C.ANCA_SX, C.ANCA_DX)
            if f["P5"] <= i <= f["P8"] and (bac[0] - self.bacino0[0]) * self.verso_palla * self.cm_px > 5:
                out["bacino"] = "Il bacino va verso la palla"
        else:
            if abs(dt[0]) * self.cm_px > 7 and i <= f["P7"]:
                out["testa"] = "La testa si sposta"
            bac = medio(k, C.ANCA_SX, C.ANCA_DX)
            spost = (bac[0] - self.bacino0[0]) * self.verso_bersaglio * self.cm_px
            if f["P2"] <= i <= f["P4"] and spost < -6:
                out["bacino"] = "Il bacino scivola indietro"
        return out

    def disegna(self, img, i, live):
        k = self.tr.kp[i] * self.s
        d = ImageDraw.Draw(img)
        h = img.height
        w_l = max(2, int(h / 380))
        # riferimenti della posizione di partenza
        _linea_tratteggiata(d, (self.bacino0[0], self.spalle0[1] - 0.15 * h),
                            (self.bacino0[0], self.bacino0[1] + 0.32 * h), BIANCO, w_l)
        col_testa = ROSSO if "testa" in live else BIANCO
        r = self.raggio_testa
        d.ellipse([self.testa0[0] - r, self.testa0[1] - r, self.testa0[0] + r, self.testa0[1] + r],
                  outline=col_testa, width=w_l + (1 if "testa" in live else 0))
        # scheletro
        for a, b in C.SCHELETRO:
            d.line([tuple(k[a]), tuple(k[b])], fill=VERDE, width=w_l + 1)
        for j in (0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28):
            x, y = k[j]
            d.ellipse([x - w_l - 1, y - w_l - 1, x + w_l + 1, y + w_l + 1], fill=BIANCO)
        # assi del corpo
        sp, bc = medio(k, C.SPALLA_SX, C.SPALLA_DX), medio(k, C.ANCA_SX, C.ANCA_DX)
        a, b = _estendi(k[C.SPALLA_SX], k[C.SPALLA_DX], 1.45)
        d.line([tuple(a), tuple(b)], fill=ARANCIO, width=w_l + 2)
        col_bac = ROSSO if "bacino" in live else AZZURRO
        a, b = _estendi(k[C.ANCA_SX], k[C.ANCA_DX], 1.6)
        d.line([tuple(a), tuple(b)], fill=col_bac, width=w_l + 2)
        asse = sp - bc
        d.line([tuple(bc - 0.25 * asse), tuple(sp + 0.55 * asse)], fill=GIALLO, width=w_l + 2)

    def legenda(self, img):
        d = ImageDraw.Draw(img, "RGBA")
        f = _font(max(13, img.height // 72))
        voci = ((GIALLO, "colonna"), (ARANCIO, "spalle"), (AZZURRO, "bacino"), (BIANCO, "partenza"))
        larg = max(d.textlength(t, font=f) for _, t in voci) + 46
        x, y = img.width - 14 - larg, 80
        d.rounded_rectangle([x, y, img.width - 14, y + len(voci) * (f.size + 8) + 12], radius=10,
                            fill=FONDO + (190,))
        y += 8
        for col, testo in voci:
            d.line([(x + 10, y + f.size // 2 + 1), (x + 30, y + f.size // 2 + 1)], fill=col, width=4)
            d.text((x + 38, y), testo, fill=BIANCO, font=f)
            y += f.size + 8


def _riquadro(img, testo, titolo=None, colore=ROSSO, in_alto=False):
    """Fascia di commento in basso (o in alto) con sfondo semitrasparente."""
    W, H = img.size
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    ft = _font(max(22, H // 40), grassetto=True)
    fs = _font(max(18, H // 50))
    margine = 22
    righe = _a_capo(d, testo, fs, W - 2 * margine - 10)
    alt = (ft.size + 10 if titolo else 0) + len(righe) * (fs.size + 8) + 2 * margine
    y0 = 70 if in_alto else H - alt - 40
    d.rounded_rectangle([14, y0, W - 14, y0 + alt], radius=18, fill=FONDO + (225,))
    d.rectangle([14, y0 + 16, 22, y0 + alt - 16], fill=colore + (255,))
    y = y0 + margine
    if titolo:
        d.text((margine + 16, y), titolo, fill=colore + (255,), font=ft)
        y += ft.size + 10
    for r in righe:
        d.text((margine + 16, y), r, fill=BIANCO + (255,), font=fs)
        y += fs.size + 8
    img.paste(Image.alpha_composite(img.convert("RGBA"), over).convert("RGB"))


def _testata(img, fase, rallentamento, avanzamento, tacche):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    f = _font(max(16, H // 56), grassetto=True)
    fs = _font(max(14, H // 64))
    d.rounded_rectangle([14, 14, W - 14, 58], radius=14, fill=FONDO + (210,))
    d.text((28, 24), f"SwingLab · {fase}", fill=BIANCO, font=f)
    t = f"rallentato ×{rallentamento:.0f}" if rallentamento >= 1.5 else "velocità reale"
    d.text((W - 28 - d.textlength(t, font=fs), 27), t, fill=GIALLO, font=fs)
    # barra di avanzamento con le tacche delle fasi
    y = 62
    d.rectangle([14, y, W - 14, y + 4], fill=(255, 255, 255, 60))
    d.rectangle([14, y, 14 + (W - 28) * avanzamento, y + 4], fill=GIALLO + (255,))
    for pos in tacche:
        x = 14 + (W - 28) * pos
        d.rectangle([x - 1, y - 3, x + 1, y + 7], fill=BIANCO + (220,))


def _etichetta_live(img, avvisi):
    if not avvisi:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = _font(max(17, img.height // 52), grassetto=True)
    y = 84
    for testo in avvisi.values():
        w = d.textlength(testo, font=f)
        d.rounded_rectangle([14, y, 14 + w + 28, y + f.size + 16], radius=12, fill=ROSSO + (230,))
        d.text((28, y + 7), testo, fill=BIANCO, font=f)
        y += f.size + 24


class _Scrittore:
    """Scrive i fotogrammi man mano (niente video intero in memoria).
    mp4 H.264 tramite ffmpeg (imageio-ffmpeg); ripiego su OpenCV."""

    def __init__(self, percorso, w, h, fps=FPS_OUT):
        self.gen = self.vw = None
        try:
            import imageio_ffmpeg
            self.gen = imageio_ffmpeg.write_frames(
                percorso, (w, h), fps=fps, codec="libx264", pix_fmt_out="yuv420p", quality=7,
                output_params=["-movflags", "+faststart"], macro_block_size=8)
            self.gen.send(None)
        except Exception:
            self.gen = None
            self.vw = cv2.VideoWriter(percorso, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    def scrivi(self, frame_rgb, volte=1):
        frame_rgb = np.ascontiguousarray(frame_rgb)
        for _ in range(volte):
            if self.gen is not None:
                self.gen.send(frame_rgb)
            else:
                self.vw.write(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))

    def chiudi(self):
        if self.gen is not None:
            self.gen.close()
        else:
            self.vw.release()


def scegli_vista(ris):
    if ris["difetti"]:
        v = ris["difetti"][0]["vista"]
        if v in ris["tracce"]:
            return v
    for pref in ("C", "A", "B"):
        if pref in ris["tracce"]:
            return pref
    return next(iter(ris["tracce"]))


def genera(ris, vista=None, durata=DURATA_TARGET_S, progress=None) -> bytes:
    """Restituisce i byte del video mp4 commentato."""
    vista = vista or scegli_vista(ris)
    tr, F = ris["tracce"][vista], ris["fasi"][vista]
    mancino = ris["profilo"].mancino
    ppm = ris["per_vista"][vista]["ppm"]
    f = F["fasi"]
    fps = tr.fps
    s0 = max(0, f["P1"] - int(0.25 * fps))
    s1 = min(tr.T - 1, f["P10"] + int(0.25 * fps))

    # dimensioni di uscita (lati pari per H.264)
    scala = LARGHEZZA_OUT / tr.larghezza
    W = LARGHEZZA_OUT // 2 * 2
    H = int(round(tr.altezza * scala)) // 2 * 2
    dis = _Disegno(tr, F, mancino, ppm, scala)

    # eventi: correzioni e punti di forza visibili in questa vista
    eventi = []
    for n, dif in enumerate(ris["difetti"], 1):
        if dif["vista"] != vista and dif["id"] not in ("tempo_veloce", "tempo_lento", "sequenza"):
            continue
        frase = FRASI.get(dif["id"], dif["titolo"])
        eventi.append(dict(i=f.get(dif["fase"], f["P4"]), titolo=f"Correzione {n}", testo=frase,
                           colore=ROSSO, pausa=2.6))
    for forza in ris["forze"][:2]:
        if forza["vista"] == vista:
            eventi.append(dict(i=f.get(forza["fase"], f["P1"]), titolo="Bene", testo=forza["testo"],
                               colore=VERDE, pausa=1.6))
    eventi.sort(key=lambda e: e["i"])
    # se due eventi cadono sullo stesso fotogramma, si mostrano uno dopo l'altro

    intro_s, outro_s = 2.0, 3.0
    pause_s = sum(e["pausa"] for e in eventi)
    play_s = max(7.0, durata - intro_s - outro_s - pause_s)
    n_play = int(play_s * FPS_OUT)
    reale_s = (s1 - s0) / fps
    rallentamento = play_s / max(reale_s, 1e-3)
    tacche = [(f[p] - s0) / max(1, s1 - s0) for p in ("P1", "P4", "P7", "P10")]

    cache = {}

    def base(i):
        if i not in cache:
            fr = tr.frame(i)
            if fr is None:
                fr = np.full((tr.altezza, tr.larghezza, 3), 40, np.uint8)
            fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
            cache[i] = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
            if len(cache) > 40:
                cache.pop(next(iter(cache)))
        return cache[i]

    def fase_di(i):
        nome = "Setup"
        for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"):
            if i >= f[p]:
                nome = f"{p} {NOMI_FASI[p]}"
        return nome

    def fotogramma(i, live=True, riquadro=None, avanz=None, titolo_rallent=None):
        img = Image.fromarray(base(i))
        av = dis.avvisi_live(i) if live else {}
        dis.disegna(img, i, av)
        dis.legenda(img)
        _testata(img, fase_di(i), titolo_rallent if titolo_rallent is not None else rallentamento,
                 avanz if avanz is not None else (i - s0) / max(1, s1 - s0), tacche)
        if riquadro:
            _riquadro(img, **riquadro)
        else:
            _etichetta_live(img, av)
        return np.asarray(img)

    fd, percorso = tempfile.mkstemp(suffix=".mp4", prefix="swinglab_")
    os.close(fd)
    out = _Scrittore(percorso, W, H)
    try:
        # intro
        out.scrivi(fotogramma(s0, live=False, riquadro=dict(
            titolo="Il tuo swing al rallentatore",
            testo=f"Vista {vista} · {C.VISTE[vista]['breve']}. Linee bianche: dove eri al setup. "
                  f"Rosso: dove va corretto.", colore=GIALLO)), int(intro_s * FPS_OUT))

        # riproduzione con pause
        prossimo = 0
        for k in range(n_play):
            i = int(round(s0 + k * (s1 - s0) / max(1, n_play - 1)))
            while prossimo < len(eventi) and i >= eventi[prossimo]["i"]:
                e = eventi[prossimo]
                out.scrivi(fotogramma(e["i"], riquadro=dict(titolo=e["titolo"], testo=e["testo"],
                                                            colore=e["colore"])), int(e["pausa"] * FPS_OUT))
                prossimo += 1
            out.scrivi(fotogramma(i))
            if progress and k % 30 == 0:
                progress(f"Preparo il video commentato… {int(100 * k / n_play)}%", k / n_play)

        # riepilogo finale sul finish
        if ris["difetti"]:
            testo = "Da allenare: " + "; ".join(d["titolo"].split(":")[0].lower()
                                                for d in ris["difetti"][:3]) + "."
        else:
            testo = "Nessuna correzione importante: lavora su costanza e ritmo."
        out.scrivi(fotogramma(s1, live=False, riquadro=dict(
            titolo=f"Punteggio {ris['punteggi']['totale']}/100", testo=testo, colore=GIALLO)),
            int(outro_s * FPS_OUT))
        out.chiudi()
        with open(percorso, "rb") as fh:
            return fh.read()
    finally:
        if os.path.exists(percorso):
            os.remove(percorso)
