# SwingLab – architettura, limiti e MVP

## 1. Schema dei componenti e flusso dei dati

```
 Telefono (slow motion 120/240 fps)
        │  1-3 video mp4/mov, angolazione etichettata A / B / C
        ▼
┌──────────────────────── PC dell'utente (localhost) ─────────────────────────┐
│ app.py (Streamlit)                                                          │
│   profilo: mano, bastone, handicap, statura, launch monitor (facoltativo)   │
│        │ copia in cartella temporanea → cancellata a fine analisi           │
│        ▼                                                                    │
│ video.py      validazione (formato, 15 s, 200 MB, fps) + qualità (luce,     │
│               telefono fermo) → errori bloccanti / avvisi                   │
│        ▼                                                                    │
│ pose.py       MediaPipe Pose Landmarker (CPU): 33 punti 2D + 3D per frame   │
│               → interpolazione dei buchi + filtro Savitzky-Golay            │
│        ▼                                                                    │
│ phases.py     P1-P10 dalla traiettoria delle mani; impatto = riferimento    │
│               comune per sincronizzare le viste (tempi in secondi, quindi   │
│               fps diversi non vanno ricampionati)                           │
│        ▼                                                                    │
│ metrics.py    metriche per vista → unione (preferenza per la vista migliore,│
│               media tra viste per tempo e rotazioni)                        │
│        ├──────────────► scoring.py     punteggi metrica/categoria/totale    │
│        ├──────────────► ballflight.py  velocità → palla → carry → direzione │
│        └──────────────► coaching.py    difetti, drill, feel, piano          │
│        ▼                                                                    │
│ annotate.py + report.py → report HTML autonomo (scaricabile)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Tecnologie e motivazioni

| Parte | Scelta | Perché |
|---|---|---|
| Interfaccia | **Streamlit** | Solo Python, gira in locale nel browser, caricamento file e grafica senza scrivere frontend. Ideale per un prototipo da provare. |
| Stima della posa | **MediaPipe Pose Landmarker (full)** | Gratis, gira sulla CPU, dà anche coordinate 3D in metri (servono per rotazioni e sequenza), esiste per Android/iOS/web: lo stesso modello servirà nell'app mobile. **MoveNet** è più veloce ma solo 2D e 17 punti (niente dita, niente 3D). **RTMPose** è più preciso su movimenti rapidi ma richiede MMPose/ONNX e GPU per andare spedito: candidato per la v2. |
| Elaborazione segnali | NumPy, SciPy | Filtri e derivate stabili, nessuna dipendenza pesante. |
| Video | OpenCV | Lettura frame, metadati fps, controlli di qualità, disegno delle annotazioni. |
| Volo palla | Modello fisico proprio | Resistenza aerodinamica + Magnus con coefficienti tarati sulle medie TrackMan PGA/LPGA (errore ~3%). Più trasparente di una tabella e funziona a qualsiasi velocità. |
| Report | HTML autonomo | Un file solo, immagini incluse, si apre ovunque; poi si converte in PDF dal browser. |

## 3. Metriche e angolazioni

| Metrica | A face-on | B lato opposto | C da dietro | Note |
|---|:-:|:-:|:-:|---|
| Inclinazione del busto, flessione ginocchia, distanza dalla palla | | | ● | |
| Larghezza dei piedi, tilt della colonna (setup e impatto) | ● | ○ | | |
| Rotazione spalle e bacino, X-factor | ● | ● | ● | dai punti 3D: confidenza media/bassa |
| Sway, testa nel backswing | ● | ○ | | |
| Braccio guida al top, lag dei polsi | ● | ○ | | il lag è una stima a bassa confidenza |
| Over the top / piano in discesa | | | ● | percorso delle mani, non del bastone |
| Early extension, perdita di postura, testa verticale | | | ● | |
| Trasferimento del peso (impatto, finish) | ● | ○ | | bacino come approssimazione del baricentro |
| Sequenza cinematica | ● | ● | ● | bacino → busto → braccia |
| Tempo (rapporto, durata), equilibrio al finish | ● | ● | ● | |
| Velocità del bastone | ● | ○ | ○ | dalle mani, calibrata con la statura |
| Direzione e curva | | | ● | dal percorso stimato |

● vista principale · ○ ripiego con confidenza più bassa.
La vista B riprende il golfer dalla parte della schiena: MediaPipe a volte scambia destra e sinistra,
per questo vale come seconda scelta.

## 4. Punteggio
- Ogni metrica ha una **fascia ideale** e una **tolleranza** (in `config.py`): 100 punti dentro la fascia,
  poi un calo rapido e via via più graduale fino a 0.
- La tolleranza si allarga con il livello (×1,0 avanzato · ×1,2 hcp 6-15 · ×1,4 hcp 16-28 · ×1,6 hcp 29-54 ·
  ×1,7 principiante). Il report mostra sia il punteggio **per il tuo livello** sia il **punteggio assoluto**.
- Categorie: Setup 15, Backswing 20, Transizione 15, Impatto 25, Finish 10, Tempo 15. Se una categoria non è
  misurabile con le viste caricate, il suo peso si ridistribuisce e il report lo dice.
- I difetti si ordinano per: punti persi × peso della metrica × peso della categoria × confidenza ×
  impatto sul volo della palla (es. over the top ed early extension pesano di più).

## 5. Limiti realistici dell'analisi da video
1. **Bastone e palla non sono tracciati.** Faccia, percorso reale, angolo d'attacco e punto d'impatto
   non si vedono: velocità e direzione sono dedotte dal corpo e dalle mani.
2. **Motion blur.** A 30 fps le mani all'impatto si spostano di 20-30 cm tra un frame e l'altro:
   velocità e impatto diventano grossolani. A 240 fps l'errore cala di molto.
3. **3D da una sola telecamera.** Le rotazioni vengono da un modello che "immagina" la profondità:
   buone per il confronto tra i tuoi swing, meno come valori assoluti.
4. **Prospettiva.** Telefono inclinato o non perpendicolare altera angoli e distanze di qualche grado/cm.
5. **Vestiti larghi e occlusioni** (braccia davanti al corpo nella vista C) spostano i punti del corpo.
6. **Volo della palla**: con un buon video la velocità del bastone ha un errore tipico del ±10-15%;
   il carry del ±15-25%. Un launch monitor resta l'unico modo per misurare.

## 6. MVP: cosa c'è adesso e cosa viene dopo

**Nel prototipo (fatto)**
- Caricamento 1-3 video con etichetta, validazione e controlli di qualità, guida illustrata alle riprese.
- Posa MediaPipe, fasi P1-P10, sincronizzazione sull'impatto, 23 metriche, punteggio calibrato sul livello.
- Stima del volo con intervalli e confidenza, confronto con launch monitor.
- Report completo: riepilogo, volo, cosa va bene, priorità con fotogramma annotato, 1-2 drill e feel,
  piano 2 settimane × 3 sessioni, fasi, confronto con un modello di riferimento, metodo del punteggio.
- Swing dimostrativo sintetico per provare tutto senza video; test automatici.

**Rimandato (in ordine consigliato)**
1. Taratura su video reali: 20-30 swing di allievi con valori misurati (launch monitor + giudizio del maestro)
   per correggere fasce, pesi e il fattore mani→bastone.
2. Tracciamento del bastone (rilevatore leggero tipo YOLO addestrato sullo shaft) → piano reale del
   bastone, lag vero, percorso.
3. Video affiancati in movimento (ora: fotogrammi chiave affiancati), slow motion frame per frame con disegno.
4. Storico degli swing, grafico dei progressi, confronto tra due swing.
5. Esportazione PDF / condivisione; testo del report scritto da un modello multimodale.
6. App mobile.

## 7. Verso l'app iOS/Android
Python non gira in modo nativo nelle app mobili. Due strade:
- **Sul dispositivo** (privacy massima): app Flutter o React Native con MediaPipe Pose per Android/iOS;
  il motore di analisi (fasi, metriche, punteggio, volo) va riscritto in Dart/TypeScript, prendendo
  questo codice Python come specifica e i test come verifica.
- **Server** (sviluppo più rapido): il motore resta in Python dietro un'API (FastAPI) e il telefono
  invia i video. Richiede hosting, informativa privacy, consenso e cancellazione automatica.

## 8. Privacy (GDPR)
- **Prototipo**: tutto in locale. I video vengono copiati in una cartella temporanea del sistema e
  cancellati alla fine dell'analisi (anche in caso di errore). Nessun account, nessun cloud, statistiche
  d'uso di Streamlit disattivate, server in ascolto solo su `localhost`.
- Il **report** contiene fotogrammi del golfer: è un dato personale che resta all'utente.
- Con una versione su server o con account: base giuridica e informativa chiare, consenso esplicito
  (i video di minori richiedono il consenso dei genitori), cifratura, conservazione limitata (es. video
  cancellati dopo 30 giorni, metriche anonime conservate), diritto alla cancellazione ed export, fornitori
  con sede o garanzie UE.

## 9. Fonti dei valori di riferimento
- TrackMan, medie PGA Tour 2023-24 (driver 115 mph club, 171 mph palla, 282 yd carry; ferro 7: 92/123/176)
  e LPGA (driver 223 yd carry).
- TrackMan Combine: golfista medio hcp 14,5 → driver 94 mph, palla 133 mph.
- TrackMan Optimizer: driver a 94 mph → lancio 13,6°; PW a 72 mph → 26,7°, palla 86 mph.
- Drillis & Contini, proporzioni dei segmenti corporei (calibrazione con la statura).
- Fasce ideali biomeccaniche: valori didattici comunemente usati nell'insegnamento (es. rapporto di tempo
  ~3:1, rotazione spalle ~90°, bacino ~45°): da validare con il maestro sui propri allievi.
