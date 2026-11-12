"""Video commentato: lo swing al rallentatore con gli assi del corpo,
diviso in 4 segmenti con fermo immagine (circa 20 secondi).

    Start → Stop/Start · Back → Stop/Back · Impatto → Stop/Impatto · Finish → Stop/Finish

- Gli assi (colonna, spalle, bacino) e il cerchio della testa cambiano
  colore in base a quanto è marcato l'errore in quell'istante:
  verde = va bene, giallo = errore lieve, rosso = errore marcato.
- La linea arancione tratteggiata è la posizione di partenza (setup).
- A ogni fermo immagine: punteggio della fase e una breve correzione.
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
DURATA_TARGET_S = 20.0
LARGHEZZA_OUT = 720

# colori RGB (il disegno avviene in RGB con Pillow)
GIALLO = (242, 201, 76)
ARANCIO = (240, 140, 60)
AZZURRO = (90, 190, 230)
VERDE = (110, 210, 140)
GRIGIO = (215, 222, 214)
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



# ---------------------------------------------------------------------------
# Gravità degli errori → colore
# ---------------------------------------------------------------------------
FASI_VIDEO = (("Start", "P1"), ("Back", "P4"), ("Impatto", "P7"), ("Finish", "P10"))


def colore_gravita(g):
    """0 = verde (va bene), 0,5 = giallo (lieve), 1 = rosso (marcato)."""
    g = float(np.clip(g, 0, 1))
    if g <= 0.5:
        a, b, t = VERDE, GIALLO, g / 0.5
    else:
        a, b, t = GIALLO, ROSSO, (g - 0.5) / 0.5
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _rampa(x, ok, marcato):
    """0 fino a 'ok', 1 da 'marcato' in su, lineare in mezzo."""
    return float(np.clip((x - ok) / max(marcato - ok, 1e-6), 0, 1))


class _Disegno:
    def __init__(self, tr, F, mancino, ppm, scala, dettaglio):
        self.tr, self.F, self.s = tr, F, scala
        self.det = dettaglio
        self.g, self.d = lati(mancino)
        p1 = F["fasi"]["P1"]
        k0 = tr.kp[p1] * scala
        self.testa0 = k0[C.NASO].copy()
        self.bacino0 = medio(k0, C.ANCA_SX, C.ANCA_DX)
        self.spalle0 = medio(k0, C.SPALLA_SX, C.SPALLA_DX)
        self.raggio_testa = max(18.0, 0.55 * np.linalg.norm(k0[C.SPALLA_SX] - k0[C.SPALLA_DX]) / 2)
        self.cm_px = 100.0 / (ppm * scala)
        mani = (tr.kp[:, C.POLSO_SX] + tr.kp[:, C.POLSO_DX]) / 2 * scala
        self.verso_palla = np.sign(mani[p1, 0] - self.bacino0[0]) or 1.0
        self.verso_bersaglio = np.sign(k0[self.g["spalla"], 0] - k0[self.d["spalla"], 0]) or 1.0
        self.busto0 = self._busto(k0)

    @staticmethod
    def _busto(k):
        s = medio(k, C.SPALLA_SX, C.SPALLA_DX) - medio(k, C.ANCA_SX, C.ANCA_DX)
        return float(np.degrees(np.arctan2(abs(s[0]), -s[1])))

    def _metrica(self, nome):
        """Gravità di una metrica dell'analisi (0 = nella fascia ideale)."""
        d = self.det.get(nome)
        return 0.0 if d is None else float(np.clip((100 - d["punteggio"]) / 60, 0, 1))

    def gravita(self, i):
        """Gravità di ogni parte del corpo nel fotogramma i, più gli avvisi da scrivere."""
        k = self.tr.kp[i] * self.s
        f = self.F["fasi"]
        dtl = self.tr.tipo == "DTL"
        g = dict(colonna=0.0, spalle=0.0, bacino=0.0, testa=0.0)
        avvisi = {}
        bac = medio(k, C.ANCA_SX, C.ANCA_DX)
        dt = (k[C.NASO] - self.testa0) * self.cm_px

        # testa
        if dtl:
            scende = dt[1] if f["P4"] <= i <= f["P7"] + 2 else 0.0
            g["testa"] = max(_rampa(scende, 3, 9), _rampa(abs(dt[0]), 5, 12) if i <= f["P7"] else 0)
            if g["testa"] >= 0.5:
                avvisi["testa"] = "La testa scende" if scende > abs(dt[0]) else "La testa si muove"
        elif i <= f["P7"]:
            g["testa"] = _rampa(abs(dt[0]), 4, 10)
            if g["testa"] >= 0.5:
                avvisi["testa"] = "La testa si sposta"

        # bacino
        if dtl:
            if f["P5"] <= i <= f["P8"]:
                verso = (bac[0] - self.bacino0[0]) * self.verso_palla * self.cm_px
                g["bacino"] = _rampa(verso, 2, 7)
                if g["bacino"] >= 0.5:
                    avvisi["bacino"] = "Il bacino va verso la palla"
        else:
            spost = (bac[0] - self.bacino0[0]) * self.verso_bersaglio * self.cm_px
            if f["P2"] <= i <= f["P4"]:
                g["bacino"] = _rampa(-spost, 2, 7)
                if g["bacino"] >= 0.5:
                    avvisi["bacino"] = "Il bacino scivola indietro"
            elif f["P5"] <= i <= f["P7"]:
                g["bacino"] = max(self._metrica("peso_impatto"), _rampa(spost, 14, 22))
        if f["P3"] <= i <= f["P5"]:
            g["bacino"] = max(g["bacino"], 0.7 * self._metrica("rotazione_bacino"))

        # colonna
        if dtl and f["P2"] <= i <= f["P8"]:
            g["colonna"] = _rampa(abs(self._busto(k) - self.busto0), 4, 11)
            if g["colonna"] >= 0.5:
                avvisi["colonna"] = "Perdi l'inclinazione del busto"
        elif not dtl:
            if i <= f["P2"]:
                g["colonna"] = self._metrica("tilt_setup")
            elif f["P6"] <= i <= f["P8"]:
                g["colonna"] = self._metrica("tilt_impatto")
        if i <= f["P2"]:
            g["colonna"] = max(g["colonna"], self._metrica("inclinazione_busto"))

        # spalle
        if f["P3"] <= i <= f["P5"]:
            g["spalle"] = max(self._metrica("rotazione_spalle"), 0.6 * self._metrica("x_factor"))
            if g["spalle"] >= 0.5 and f["P4"] - 3 <= i <= f["P4"] + 3:
                avvisi["spalle"] = "Rotazione delle spalle corta"
        elif f["P5"] < i <= f["P7"]:
            g["spalle"] = max(self._metrica("over_the_top"), self._metrica("tilt_impatto"))
        return g, avvisi

    def disegna(self, img, i, g):
        k = self.tr.kp[i] * self.s
        d = ImageDraw.Draw(img)
        h = img.height
        w_l = max(2, int(h / 380))
        fl = _font(max(13, h // 78), grassetto=True)
        # posizione di partenza (arancione tratteggiato): verticale del bacino e linea della testa
        _linea_tratteggiata(d, (self.bacino0[0], self.spalle0[1] - 0.15 * h),
                            (self.bacino0[0], self.bacino0[1] + 0.32 * h), ARANCIO, w_l + 1)
        _linea_tratteggiata(d, (self.testa0[0] - 2.2 * self.raggio_testa, self.testa0[1]),
                            (self.testa0[0] + 2.2 * self.raggio_testa, self.testa0[1]), ARANCIO, w_l)
        # cerchio della testa al setup, colorato per gravità
        r = self.raggio_testa
        d.ellipse([self.testa0[0] - r, self.testa0[1] - r, self.testa0[0] + r, self.testa0[1] + r],
                  outline=colore_gravita(g["testa"]), width=w_l + 1)
        # scheletro discreto
        for a, b in C.SCHELETRO:
            d.line([tuple(k[a]), tuple(k[b])], fill=GRIGIO, width=max(1, w_l - 1))
        for j in (0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28):
            x, y = k[j]
            d.ellipse([x - w_l, y - w_l, x + w_l, y + w_l], fill=BIANCO)
        # assi colorati per gravità, con il loro nome
        sp, bc = medio(k, C.SPALLA_SX, C.SPALLA_DX), medio(k, C.ANCA_SX, C.ANCA_DX)

        def asse(p, q, nome, gr):
            col = colore_gravita(gr)
            d.line([tuple(p), tuple(q)], fill=FONDO, width=w_l + 6)
            d.line([tuple(p), tuple(q)], fill=col, width=w_l + 3)
            fine = q if q[0] >= p[0] else p
            d.text((fine[0] + 6, fine[1] - fl.size / 2), nome, fill=col, font=fl,
                   stroke_width=2, stroke_fill=FONDO)

        a, b = _estendi(k[C.SPALLA_SX], k[C.SPALLA_DX], 1.45)
        asse(a, b, "spalle", g["spalle"])
        a, b = _estendi(k[C.ANCA_SX], k[C.ANCA_DX], 1.6)
        asse(a, b, "bacino", g["bacino"])
        v = sp - bc
        asse(bc - 0.25 * v, sp + 0.55 * v, "colonna", g["colonna"])

    def legenda(self, img):
        d = ImageDraw.Draw(img, "RGBA")
        f = _font(max(13, img.height // 74))
        voci = ((VERDE, "va bene", False), (GIALLO, "errore lieve", False),
                (ROSSO, "errore marcato", False), (ARANCIO, "partenza", True))
        larg = max(d.textlength(t, font=f) for _, t, _ in voci) + 46
        x, y = img.width - 14 - larg, 80
        d.rounded_rectangle([x, y, img.width - 14, y + len(voci) * (f.size + 8) + 12], radius=10,
                            fill=FONDO + (195,))
        y += 8
        for col, testo, tratt in voci:
            ym = y + f.size // 2 + 1
            if tratt:
                for xx in range(int(x + 10), int(x + 30), 8):
                    d.line([(xx, ym), (min(xx + 4, x + 30), ym)], fill=col, width=4)
            else:
                d.line([(x + 10, ym), (x + 30, ym)], fill=col, width=4)
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
    y = 62
    d.rectangle([14, y, W - 14, y + 4], fill=(255, 255, 255, 60))
    d.rectangle([14, y, 14 + (W - 28) * float(np.clip(avanzamento, 0, 1)), y + 4], fill=GIALLO + (255,))
    for pos in tacche:
        x = 14 + (W - 28) * pos
        d.rectangle([x - 1, y - 3, x + 1, y + 7], fill=BIANCO + (220,))


def _etichetta_live(img, avvisi, gravita):
    if not avvisi:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = _font(max(17, img.height // 52), grassetto=True)
    y = 84
    for parte, testo in avvisi.items():
        col = colore_gravita(gravita.get(parte, 1.0))
        w = d.textlength(testo, font=f)
        d.rounded_rectangle([14, y, 14 + w + 28, y + f.size + 16], radius=12, fill=col + (235,))
        d.text((28, y + 7), testo, fill=FONDO, font=f)
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


def _correzione_fase(ris, fase):
    """La correzione più importante della fase (o un punto di forza)."""
    det = ris["punteggi"]["dettaglio"]
    for dif in ris["difetti"]:
        if det.get(dif["metrica"], {}).get("cat") == fase:
            return FRASI.get(dif["id"], dif["titolo"]), True
    for forza in ris["forze"]:
        if det.get(forza["metrica"], {}).get("cat") == fase:
            return "Bene: " + forza["testo"], False
    return "Nessuna correzione importante in questa fase.", False


def _colore_punteggio(p):
    if p is None:
        return BIANCO
    return VERDE if p >= 85 else (GIALLO if p >= 65 else ROSSO)


def genera(ris, vista=None, durata=DURATA_TARGET_S, progress=None) -> bytes:
    """Restituisce i byte del video mp4 commentato."""
    vista = vista or scegli_vista(ris)
    tr, F = ris["tracce"][vista], ris["fasi"][vista]
    ppm = ris["per_vista"][vista]["ppm"]
    f = F["fasi"]
    fps = tr.fps
    s0 = max(0, f["P1"] - int(0.3 * fps))
    s1 = min(tr.T - 1, f["P10"] + int(0.2 * fps))

    scala = LARGHEZZA_OUT / tr.larghezza
    W = LARGHEZZA_OUT // 2 * 2
    H = int(round(tr.altezza * scala)) // 2 * 2
    dis = _Disegno(tr, F, ris["profilo"].mancino, ppm, scala, ris["punteggi"]["dettaglio"])
    cat = ris["punteggi"]["categorie"]

    # segmenti: [inizio → Start], [Start → Back], [Back → Impatto], [Impatto → Finish]
    fermi = [f[p] for _, p in FASI_VIDEO]
    inizi = [s0] + fermi[:3]
    intro_s, pausa_s = 1.0, 2.2
    play_s = max(6.0, durata - intro_s - 4 * pausa_s)
    reali = [max(1, b - a) / fps for a, b in zip(inizi, fermi)]
    minimi = [0.6, 1.2, 1.2, 1.2]
    pesi = np.maximum(np.array(reali) / sum(reali) * play_s, minimi)
    pesi = pesi * play_s / pesi.sum()
    tacche = [(x - s0) / max(1, s1 - s0) for x in fermi]

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

    def fotogramma(i, etichetta, rallent, riquadro=None):
        img = Image.fromarray(base(i))
        gr, avvisi = dis.gravita(i)
        dis.disegna(img, i, gr)
        dis.legenda(img)
        _testata(img, etichetta, rallent, (i - s0) / max(1, s1 - s0), tacche)
        if riquadro:
            _riquadro(img, **riquadro)
        else:
            _etichetta_live(img, avvisi, gr)
        return np.asarray(img)

    fd, percorso = tempfile.mkstemp(suffix=".mp4", prefix="swinglab_")
    os.close(fd)
    out = _Scrittore(percorso, W, H)
    try:
        out.scrivi(fotogramma(s0, "Il tuo swing", 1, riquadro=dict(
            titolo="Il tuo swing al rallentatore",
            testo=f"Vista {vista} · {C.VISTE[vista]['breve']}. Gli assi diventano gialli o rossi "
                  "quando l'errore è lieve o marcato.", colore=GIALLO)), int(intro_s * FPS_OUT))
        totale = sum(int(p * FPS_OUT) for p in pesi)
        fatti = 0
        for n, ((nome, _), a, b, sec) in enumerate(zip(FASI_VIDEO, inizi, fermi, pesi)):
            n_out = max(2, int(sec * FPS_OUT))
            rallent = sec / max((b - a) / fps, 1e-3)
            for k in range(n_out):
                i = int(round(a + k * (b - a) / max(1, n_out - 1)))
                out.scrivi(fotogramma(i, nome, rallent))
                fatti += 1
                if progress and fatti % 30 == 0:
                    progress(f"Preparo il video commentato… {int(100 * fatti / totale)}%", fatti / totale)
            p = cat.get(nome, {}).get("punteggio")
            testo, _ = _correzione_fase(ris, nome)
            titolo = f"Stop · {nome}" + (f" · {p:.0f}/100" if p is not None else "")
            out.scrivi(fotogramma(b, nome, rallent, riquadro=dict(
                titolo=titolo, testo=testo, colore=_colore_punteggio(p))), int(pausa_s * FPS_OUT))
        out.chiudi()
        with open(percorso, "rb") as fh:
            return fh.read()
    finally:
        if os.path.exists(percorso):
            os.remove(percorso)
