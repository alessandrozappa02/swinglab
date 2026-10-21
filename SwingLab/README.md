# SwingLab – prototipo

Analisi dello swing di golf da 1 a 3 video del telefono: punteggio 0-100, stima del volo della palla
e report del maestro con esercizi. Gira tutto sul tuo PC, gratis, senza inviare i video a nessuno.

---

## Avvio su Windows (prima volta: ~10 minuti)

### 1. Installa Python 3.12
1. Vai su https://www.python.org/downloads/ e scarica **Python 3.12** (64 bit).
   Meglio la 3.12 della più recente: MediaPipe esce sempre con qualche mese di ritardo sulle nuove versioni.
2. Nella prima schermata dell'installazione **spunta "Add python.exe to PATH"**, poi "Install Now".

### 2. Estrai la cartella
Estrai lo zip `SwingLab.zip` dove preferisci, per esempio in `Documenti\SwingLab`.
Evita cartelle sincronizzate (OneDrive) se possibile: l'ambiente Python pesa qualche centinaio di MB.

### 3. Avvia
Fai **doppio clic su `avvia.bat`**. La prima volta:
- crea un ambiente Python nella cartella `.venv`;
- installa MediaPipe, OpenCV, Streamlit (qualche minuto);
- alla prima analisi di un video vero scarica il modello di posa (~9 MB) nella cartella `models`.

Poi si apre il browser su `http://localhost:8501`. Dalla seconda volta parte in pochi secondi.
Per chiudere l'app chiudi la finestra nera del terminale.

> Se Windows mostra "PC protetto da Windows": "Ulteriori informazioni" → "Esegui comunque".
> Il file `avvia.bat` è testo: puoi aprirlo con il Blocco note e leggere cosa fa.

### Avvio manuale (se Windows blocca `avvia.bat`)
Il "Controllo intelligente delle app" di Windows può bloccare i file `.bat` scaricati. In quel caso apri la
cartella, clicca sulla barra dell'indirizzo, scrivi `cmd` e premi Invio, poi:
```bat
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py --server.address localhost
```
Le volte successive basta l'ultimo comando.

---

## Come si usa
1. **Barra laterale**: mano, bastone, handicap (o principiante), statura, eventuali dati di un launch monitor.
2. Scheda **Come riprendere lo swing**: dove mettere il telefono per le viste A, B, C.
3. Scheda **Analizza**: carica da 1 a 3 video (mp4/mov, max 15 s, max 200 MB) e premi **Analizza lo swing**.
   Per vedere subito come funziona senza video: **Prova con uno swing dimostrativo**.
4. Il report appare sotto e si scarica come file HTML (si apre con qualsiasi browser, anche dal telefono).
5. Sopra il report c'è il **video commentato** (circa 25 s): lo swing al rallentatore con gli assi del corpo
   e le correzioni scritte sul video. Si scarica in MP4.

**Il report d'esempio** generato con lo swing dimostrativo è in `report_esempio.html`.

### Quanti video servono
Basta **uno**: l'app funziona con qualsiasi combinazione e avvisa che con meno video l'analisi è meno
precisa. Con un video solo, quello **da dietro (C)** dà le informazioni più utili su piano, postura e
direzione; quello **laterale (A)** su peso, sway e braccia. L'ideale è A + C.

### Consigli per i video
- Slow motion **120 o 240 fps**. Se il telefono esporta lo slow motion "rallentato" (il file dichiara 30 fps),
  l'app lo riconosce da sola e lo segnala nel report. Se la stima è sbagliata, scrivi il frame rate reale
  nel campo sotto il video.
- Telefono fermo, golfer intero, buona luce, 1-2 secondi prima e dopo lo swing.
- Con più angolazioni usa più telefoni sullo **stesso swing**: l'app allinea le viste sull'impatto.

### Usarlo dal telefono
Pubblica l'app online (sezione qui sotto) e apri il link dal telefono.

---

## Pubblicare online con Streamlit Community Cloud (gratis)
Serve un account GitHub (dove sta il codice) e l'accesso a Streamlit Community Cloud (che lo esegue).

**1. Metti il codice su GitHub**
1. Crea un account su https://github.com e accedi.
2. In alto a destra: **+** → **New repository**. Nome: `swinglab`. Scegli **Public** (con Private puoi
   comunque pubblicare, ma il piano gratuito ne permette solo una). Spunta nulla e clicca **Create repository**.
3. Nella pagina del repository vuoto clicca **uploading an existing file**.
4. Trascina la cartella **SwingLab** (quella con `app.py` dentro) e il file **packages.txt**, che deve
   stare nella cartella principale del repository, fuori da SwingLab. **Non** caricare `.venv`.
5. In basso clicca **Commit changes**.

**2. Pubblica**
1. Vai su https://share.streamlit.io e accedi con **Continue with GitHub** (autorizza l'accesso).
2. **Create app** → **Deploy a public app from GitHub** (o "Yup, I have an app").
3. Repository `tuo-nome/swinglab`, branch `main`, file principale `SwingLab/app.py`.
4. **App URL**: scegli un nome, per esempio `swinglab-tuonome`.
5. **Advanced settings** → Python **3.12** → Save.
6. **Deploy**. La prima volta installa tutto in 3-5 minuti, poi l'app è su
   `https://swinglab-tuonome.streamlit.app`.

**Da sapere**
- Il link è pubblico: chiunque lo abbia può usare l'app.
- Dopo alcuni giorni senza visite l'app va in pausa: alla visita successiva basta cliccare "wake up".
- Il server gratuito è lento: un video slow motion lungo richiede 1-3 minuti. Taglia il video intorno allo swing.
- Per aggiornare l'app: nella pagina principale del repository **Add file → Upload files**, trascina di nuovo
  la cartella SwingLab (sovrascrive i file vecchi) e fai Commit: l'app si aggiorna da sola.
- I video vengono caricati sul server per l'analisi e cancellati subito dopo (vedi la scheda Privacy dell'app).

---

## Controlli automatici
```bat
.venv\Scripts\python.exe tests\test_motore.py
```
Verifica fasi, punteggio, rilevamento dei difetti, modello di volo (tarato sulle medie TrackMan) e report,
usando uno swing sintetico 3D.

## Struttura
```
SwingLab/
├─ avvia.bat               avvio con doppio clic (Windows)
├─ app.py                  interfaccia web (Streamlit)
├─ requirements.txt
├─ .streamlit/config.toml  limite 200 MB, statistiche disattivate
├─ packages.txt            librerie di sistema per Streamlit Cloud
├─ models/                 modello MediaPipe (scaricato al primo uso)
├─ swinglab_core/
│  ├─ config.py            tabelle, fasce ideali, pesi del punteggio  ← qui si fa la taratura
│  ├─ video.py             validazione e controlli di qualità
│  ├─ pose.py              MediaPipe Pose Landmarker + filtraggio
│  ├─ phases.py            fasi P1-P10 e sincronizzazione sull'impatto
│  ├─ metrics.py           metriche biomeccaniche per vista
│  ├─ scoring.py           punteggi calibrati sul livello
│  ├─ ballflight.py        velocità, carry (modello fisico), direzione
│  ├─ coaching.py          difetti, drill, feel, piano di allenamento
│  ├─ annotate.py          fotogrammi annotati
│  ├─ report.py            report HTML autonomo
│  ├─ video_commento.py    video rallentato con assi e commento delle correzioni
│  ├─ demo.py              swing sintetico 3D e modello di riferimento
│  └─ pipeline.py          orchestrazione
├─ tests/test_motore.py
├─ ARCHITETTURA.md         architettura, limiti, MVP e roadmap
└─ report_esempio.html
```

## Problemi frequenti
| Messaggio | Cosa fare |
|---|---|
| `Python non trovato` | Reinstalla Python 3.12 spuntando "Add python.exe to PATH". |
| Errore installando `mediapipe` | Stai usando una versione di Python troppo nuova: installa la 3.12, cancella la cartella `.venv` e rilancia `avvia.bat`. |
| Errore nello scaricare il modello | Serve internet solo la prima volta. In alternativa scarica a mano `pose_landmarker_full.task` dalla pagina MediaPipe "Pose landmark detection" e mettilo in `models/`. |
| "Golfer non rilevato" | Inquadratura troppo stretta o buia: rigira il video seguendo la guida. |
| Le librerie sono cambiate | Cancella `.venv\installato.txt` e rilancia `avvia.bat` per reinstallarle. |
