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

### Avvio manuale (alternativa, dal terminale)
```bat
cd percorso\di\SwingLab
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

---

## Come si usa
1. **Barra laterale**: mano, bastone, handicap (o principiante), statura, eventuali dati di un launch monitor.
2. Scheda **Come riprendere lo swing**: dove mettere il telefono per le viste A, B, C.
3. Scheda **Analizza**: carica da 1 a 3 video (mp4/mov, max 15 s, max 200 MB) e premi **Analizza lo swing**.
   Per vedere subito come funziona senza video: **Prova con uno swing dimostrativo**.
4. Il report appare sotto e si scarica come file HTML (si apre con qualsiasi browser, anche dal telefono).

**Il report d'esempio** generato con lo swing dimostrativo è in `report_esempio.html`.

### Consigli per i video
- Slow motion **120 o 240 fps**. Se l'app legge 30 fps su un video slow motion (succede quando il
  telefono lo esporta "rallentato"), scrivi il frame rate reale nel campo sotto il video.
- Telefono fermo, golfer intero, buona luce, 1-2 secondi prima e dopo lo swing.
- Con più angolazioni usa più telefoni sullo **stesso swing**: l'app allinea le viste sull'impatto.

### Usarlo dal telefono
Il prototipo gira sul PC. Per caricare video direttamente dal telefono sulla stessa rete Wi-Fi:
nel file `.streamlit\config.toml` cambia `address = "localhost"` in `address = "0.0.0.0"`, riavvia e apri
dal telefono `http://IP-DEL-PC:8501`. Lasciarlo su `localhost` è più sicuro.

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
├─ .streamlit/config.toml  localhost, limite 200 MB, statistiche disattivate
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
