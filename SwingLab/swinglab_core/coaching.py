"""Libreria del maestro: difetti, esercizi (drill), feel, punti di forza e
piano di allenamento. {G} = lato guida, {D} = lato dietro."""
from __future__ import annotations

# metrica → (difetto se sotto la banda, difetto se sopra la banda)
MAPPA = {
    "inclinazione_busto": ("postura_eretta", "postura_curva"),
    "flessione_ginocchia": ("postura_eretta", "postura_seduta"),
    "distanza_palla": ("vicino_palla", "lontano_palla"),
    "larghezza_stance": ("stance", "stance"),
    "tilt_setup": ("tilt_setup", None),
    "rotazione_spalle": ("rotazione_corta", "overswing"),
    "rotazione_bacino": (None, "bacino_eccessivo"),
    "x_factor": ("bacino_eccessivo", None),
    "sway": ("reverse_pivot", "sway"),
    "testa_backswing": ("reverse_pivot", "sway"),
    "braccio_guida_top": ("braccio_piegato", None),
    "over_the_top": ("troppo_dentro", "over_the_top"),
    "sequenza": ("sequenza", None),
    "lag": ("casting", None),
    "early_extension": (None, "early_extension"),
    "perdita_postura": ("early_extension", "abbassamento"),
    "testa_verticale": ("abbassamento", "early_extension"),
    "peso_impatto": ("peso_dietro", "slide"),
    "tilt_impatto": ("spalle_livellate", "peso_dietro"),
    "peso_finish": ("finish", None),
    "equilibrio": (None, "finish"),
    "rapporto_tempo": ("tempo_veloce", "tempo_lento"),
    "durata_backswing": ("tempo_veloce", "tempo_lento"),
}

# Quanto il difetto pesa sul volo della palla (moltiplica la priorità)
IMPATTO_PALLA = {
    "over_the_top": 1.5, "early_extension": 1.4, "peso_dietro": 1.4, "casting": 1.3,
    "sway": 1.2, "sequenza": 1.2, "reverse_pivot": 1.3, "spalle_livellate": 1.1,
}

DIFETTI = {
    "sway": dict(
        titolo="Sway: il bacino scivola indietro nel backswing",
        descrizione="Nel backswing il bacino e la testa si spostano lateralmente verso il "
                    "lato {D} invece di ruotare.",
        perche="Spesso nasce dal tentativo di \"caricare il peso\" spostandosi, oppure da un "
               "ginocchio {D} che si raddrizza e cede verso l'esterno.",
        palla="Per colpire devi riportare tutto indietro con precisione: contatto incostante, "
              "zolle dietro la palla (colpi grassi) o colpi sottili.",
        drill=[("Bastone fuori dal piede {D}", [
            "Pianta un bastone (o un'asta di allineamento) in verticale a filo dell'esterno del piede {D}.",
            "Fai backswing lenti fino al top: l'anca {D} non deve toccare il bastone.",
            "10 ripetizioni senza palla, poi 10 colpi a mezza velocità."]),
            ("Palla sotto l'esterno del piede {D}", [
            "Metti una palla o un piccolo spessore sotto il bordo esterno della scarpa {D}.",
            "Il piede resta inclinato verso l'interno e ti impedisce di scivolare fuori.",
            "Colpisci 15 palle con un ferro 7 mantenendo la pressione all'interno del piede."])],
        feel="Senti la pressione all'interno del piede {D}, come se ruotassi dentro un barile."),
    "reverse_pivot": dict(
        titolo="Reverse pivot: al top il peso va verso il bersaglio",
        descrizione="Al top testa e bacino si spostano verso il bersaglio: il peso finisce sul "
                    "piede {G} proprio quando dovrebbe stare sul {D}.",
        perche="Di solito si cerca di \"stare sopra la palla\" bloccando la rotazione, oppure si "
               "alzano le braccia senza girare il busto.",
        palla="In discesa il peso torna indietro: colpi alti e deboli, top e slice.",
        drill=[("Pausa al top", [
            "Porta il bastone al top lentamente e fermati 2 secondi.",
            "Controlla che la testa sia sopra o leggermente dietro la palla e che il peso sia sul tallone {D}.",
            "Solo allora scendi e colpisci. 3 serie da 8 palle."]),
            ("Piede {G} sollevato", [
            "Fai il backswing alzando leggermente il tallone {G}: ti obbliga a caricare il lato {D}.",
            "Riappoggia il tallone per iniziare la discesa."])],
        feel="Al top senti il peso sul tallone {D} e la schiena che guarda il bersaglio."),
    "early_extension": dict(
        titolo="Early extension: perdi la postura in discesa",
        descrizione="In discesa il bacino va verso la palla e il busto si alza: perdi gli angoli "
                    "costruiti al setup.",
        perche="È il difetto più comune negli amatori: compensa una discesa dall'esterno, una "
               "mobilità limitata delle anche o una sequenza che parte dalle braccia.",
        palla="Le mani non hanno spazio: colpi di punta o di tacco (shank), push, hook di "
              "compensazione o slice, contatto incostante.",
        drill=[("Glutei al muro", [
            "Mettiti in postura con i glutei che toccano appena un muro (o lo schienale di una sedia).",
            "Fai lo swing senza bastone, con le braccia incrociate sul petto.",
            "Al top deve toccare il gluteo {D}, all'impatto il gluteo {G}: il sedere non si stacca mai.",
            "3 serie da 10, poi 10 colpi cercando la stessa sensazione."]),
            ("Asta dietro i glutei", [
            "Pianta un'asta in diagonale dietro di te, a contatto con i glutei al setup.",
            "Colpisci palle a mezza velocità mantenendo il contatto fino a dopo l'impatto."])],
        feel="Il sedere resta indietro e il petto resta rivolto verso la palla fino all'impatto."),
    "abbassamento": dict(
        titolo="Ti abbassi in discesa",
        descrizione="Testa e busto scendono verso la palla durante la discesa.",
        perche="Spesso è un tentativo di \"colpire la palla\" con forza o di aiutarla ad alzarsi.",
        palla="Colpi grassi e zolle profonde, soprattutto con i ferri.",
        drill=[("Cappellino contro l'asta", [
            "Chiedi a qualcuno di tenere un'asta appoggiata sulla visiera del tuo cappellino al setup.",
            "Fai swing lenti senza spingere la testa contro l'asta."])],
        feel="Altezza costante: sei alto quanto al setup, come se fossi appeso a un filo."),
    "over_the_top": dict(
        titolo="Over the top: la discesa parte dall'esterno",
        descrizione="Dall'alto le mani e il bastone si spostano verso la palla, sopra il piano "
                    "del backswing, e il bastone arriva all'impatto dall'esterno.",
        perche="La discesa parte con spalle e braccia invece che con il bacino; spesso è "
               "aggravata da un grip debole e dalla voglia di colpire forte.",
        palla="Percorso dall'esterno all'interno: slice (con faccia aperta) o pull a sinistra.",
        drill=[("Headcover fuori dalla palla", [
            "Metti un headcover (o una scatola di palline) 15 cm fuori dalla palla e 15 cm dietro.",
            "Colpisci senza toccarlo: se scendi dall'esterno lo colpisci.",
            "Inizia a mezza velocità con un ferro 7, 3 serie da 8."]),
            ("Pump drill", [
            "Sali al top, poi scendi lentamente finché le mani sono all'altezza dell'anca {D}, "
            "con il gomito {D} vicino al fianco.",
            "Torna al top e ripeti due volte, alla terza colpisci la palla."])],
        feel="La discesa la inizia il bacino; il gomito {D} cade verso la tasca {D}."),
    "troppo_dentro": dict(
        titolo="Discesa troppo dall'interno",
        descrizione="In discesa le mani scendono molto sotto e dietro il piano del backswing.",
        perche="Spesso le mani restano indietro rispetto alla rotazione del corpo o il bacino "
               "scivola verso il bersaglio.",
        palla="Percorso molto dall'interno: push a destra o hook (palla che gira forte).",
        drill=[("Gate con due tee", [
            "Pianta due tee a 5 cm davanti alla palla, distanziati quanto la testa del bastone.",
            "Fai passare il bastone tra i tee dopo l'impatto, mandandolo verso il bersaglio."])],
        feel="Dopo l'impatto il bastone esce a {G} del bersaglio, con il petto che continua a girare."),
    "sequenza": dict(
        titolo="Sequenza: in discesa partono prima le parti alte",
        descrizione="In discesa busto o braccia raggiungono il picco di velocità prima del bacino.",
        perche="Il corpo non usa l'ordine naturale bacino → busto → braccia → bastone, che "
               "moltiplica la velocità come una frusta.",
        palla="Velocità persa e percorso spesso dall'esterno: meno distanza, più slice.",
        drill=[("Step drill", [
            "Mettiti con i piedi uniti.",
            "Inizia il backswing; quando le mani arrivano all'altezza delle spalle fai un passo verso il bersaglio con il piede {G}.",
            "Appena il piede tocca terra, scendi e colpisci. 3 serie da 8 a mezza velocità."]),
            ("Pausa al top e bacino", [
            "Fermati al top 1 secondo.",
            "Fai partire solo il bacino (fibbia della cintura verso il bersaglio) e lascia che le braccia seguano."])],
        feel="Il bottone dei pantaloni guarda il bersaglio prima che le mani arrivino alla palla."),
    "casting": dict(
        titolo="Rilascio anticipato (casting)",
        descrizione="L'angolo tra braccio e bastone si apre troppo presto in discesa (stima dal "
                    "video, da confermare).",
        perche="La testa del bastone viene \"lanciata\" dall'alto per cercare velocità o per "
               "aiutare la palla ad alzarsi.",
        palla="Velocità persa all'impatto, colpi deboli e alti, contatto grasso o sottile.",
        drill=[("L-to-L", [
            "Fai mezzi swing: braccio {G} e bastone formano una L a fine backswing e un'altra L dopo l'impatto.",
            "Mantieni l'angolo dei polsi finché le mani sono all'altezza dell'anca, poi rilascia.",
            "20 palle con ferro 8 o 9."]),
            ("Swing con la sola mano {G}", [
            "Impugna corto un ferro 9 con la sola mano {G} e fai mezzi swing tirando il grip verso la palla."])],
        feel="Trascini il grip verso la palla: la testa del bastone arriva per ultima."),
    "peso_dietro": dict(
        titolo="Il peso resta sul piede {D} all'impatto",
        descrizione="All'impatto il bacino è ancora vicino al piede {D}: il trasferimento verso "
                    "il bersaglio è incompleto.",
        perche="Spesso si cerca di alzare la palla \"da sotto\", o il backswing è già sbilanciato.",
        palla="Il punto più basso dello swing finisce dietro la palla: colpi grassi, sottili e "
              "poca compressione.",
        drill=[("Asciugamano dietro la palla", [
            "Metti un asciugamano piegato 10 cm dietro la palla.",
            "Colpisci la palla senza toccare l'asciugamano: ci riesci solo spostando il peso avanti.",
            "3 serie da 8 con ferro 7."]),
            ("Finish sul piede {G}", [
            "Colpisci e tieni il finish 3 secondi con il piede {D} in punta.",
            "Se non resti in equilibrio, rallenta finché ci riesci."])],
        feel="All'impatto la fibbia della cintura è già davanti alla palla."),
    "slide": dict(
        titolo="Slide: il bacino scivola troppo verso il bersaglio",
        descrizione="In discesa il bacino scivola lateralmente oltre il piede {G} invece di ruotare.",
        perche="Trasferimento del peso fatto spostandosi anziché ruotando.",
        palla="Il bastone resta indietro: push e blocchi a destra, o hook di compensazione.",
        drill=[("Asta fuori dal piede {G}", [
            "Pianta un'asta in verticale a filo dell'esterno del piede {G}.",
            "In discesa l'anca {G} può avvicinarsi ma non deve spingerla: deve girare indietro."])],
        feel="Il bacino ruota sul posto, l'anca {G} va indietro verso il tallone."),
    "spalle_livellate": dict(
        titolo="Spalle troppo livellate all'impatto",
        descrizione="All'impatto la colonna è quasi verticale invece di inclinarsi via dal bersaglio.",
        perche="Spesso accompagna la discesa dall'esterno: la spalla {D} va avanti invece di scendere.",
        palla="Colpi in discesa ripidi, slice e pull.",
        drill=[("Spalla {D} sotto", [
            "Fai mezzi swing sentendo la spalla {D} che scende sotto il mento all'impatto.",
            "Controlla allo specchio: la spalla {D} è più bassa della {G}."])],
        feel="All'impatto la spalla {D} è bassa e la testa resta dietro la palla."),
    "rotazione_corta": dict(
        titolo="Rotazione delle spalle corta",
        descrizione="Al top le spalle non completano la rotazione.",
        perche="Mobilità limitata, o un backswing fatto solo con le braccia.",
        palla="Meno velocità e discesa dall'esterno: distanza persa e slice.",
        drill=[("Bastone sulle spalle", [
            "Appoggia un bastone sulle spalle tenendolo con le braccia incrociate.",
            "In postura ruota finché la punta del bastone indica la palla (o oltre).",
            "15 ripetizioni lente prima di ogni sessione."]),
            ("Tallone {G} libero", [
            "Concediti di sollevare un po' il tallone {G} nel backswing per aiutare la rotazione."])],
        feel="Al top la schiena guarda il bersaglio."),
    "overswing": dict(
        titolo="Backswing troppo lungo",
        descrizione="Al top le spalle ruotano oltre il necessario e lo swing perde struttura.",
        perche="Spesso il braccio {G} si piega e i polsi cedono per allungare.",
        palla="Contatto incostante e tempo difficile da ripetere.",
        drill=[("Backswing a 3/4", [
            "Fai swing fermando il backswing con il braccio {G} parallelo al terreno.",
            "Scopri quanta distanza perdi: di solito quasi niente, con molto più controllo."])],
        feel="Compatto in alto, potente in basso."),
    "bacino_eccessivo": dict(
        titolo="Il bacino gira troppo nel backswing",
        descrizione="Il bacino ruota quasi quanto le spalle: si perde la differenza (X-factor) che "
                    "accumula energia.",
        perche="Il ginocchio {D} si raddrizza e lascia girare tutto insieme.",
        palla="Meno velocità e più difficoltà a iniziare la discesa con il bacino.",
        drill=[("Ginocchio {D} stabile", [
            "Stringi un pallone o un asciugamano arrotolato tra le ginocchia.",
            "Fai backswing mantenendo la flessione del ginocchio {D}."])],
        feel="Il ginocchio {D} resta flesso: le spalle girano, il bacino resiste."),
    "braccio_piegato": dict(
        titolo="Braccio {G} piegato al top",
        descrizione="Al top il gomito {G} si piega molto e lo swing perde ampiezza.",
        perche="Si cerca un backswing più lungo con le braccia invece che con la rotazione.",
        palla="Arco più corto e meno velocità; contatto meno ripetibile.",
        drill=[("Ampiezza nel takeaway", [
            "Nei primi 50 cm del backswing spingi le mani lontano dal petto.",
            "Fermati al top quando il gomito {G} inizia a piegarsi: quella è la tua lunghezza."])],
        feel="Braccio {G} lungo ma non rigido, come se allungassi l'arco."),
    "tempo_veloce": dict(
        titolo="Tempo affrettato",
        descrizione="Il rapporto tra backswing e discesa è più basso del 3:1 dei giocatori migliori: "
                    "la discesa parte prima che il backswing sia finito.",
        perche="Fretta di colpire, ansia o voglia di forzare.",
        palla="Sequenza disordinata, colpi dall'esterno e contatto incostante.",
        drill=[("Conteggio 1-2-3-QUATTRO", [
            "Conta \"uno-due-tre\" nel backswing e colpisci sul \"quattro\".",
            "Usa un metronomo gratuito: ogni battito una fase, ritmo 3:1.",
            "20 palle con ferro 7 a 70% di velocità."])],
        feel="Il top è un istante di pausa: il bastone si posa prima di ripartire."),
    "tempo_lento": dict(
        titolo="Tempo troppo lento",
        descrizione="Il backswing è molto lento rispetto alla discesa.",
        perche="Tensione o troppa attenzione ai dettagli durante il movimento.",
        palla="Perdita di ritmo e di velocità.",
        drill=[("Swing continui", [
            "Fai 5 swing consecutivi avanti e indietro senza fermarti, con un ferro 7.",
            "Poi colpisci una palla cercando lo stesso ritmo fluido."])],
        feel="Un unico movimento fluido, come un'altalena."),
    "finish": dict(
        titolo="Finish poco stabile",
        descrizione="Al finish non sei in equilibrio sul piede {G}.",
        perche="Il trasferimento del peso è incompleto o lo swing è troppo forzato.",
        palla="Uno swing che non finisce in equilibrio raramente ha un impatto solido.",
        drill=[("Finish di 3 secondi", [
            "Dopo ogni colpo tieni il finish 3 secondi: petto al bersaglio, piede {D} in punta.",
            "Se cadi, rallenta lo swing al 70%."]),
            ("Piedi uniti", [
            "Colpisci 10 palle con i piedi uniti a mezza velocità: allena equilibrio e ritmo."])],
        feel="Posa per la foto: petto al bersaglio, peso tutto sul piede {G}."),
    "postura_eretta": dict(
        titolo="Postura troppo eretta al setup",
        descrizione="Al setup il busto è poco piegato dalle anche o le gambe sono rigide.",
        perche="Spesso si sta lontani dalla palla in piedi, \"come per parlare\".",
        palla="Piano dello swing piatto e tendenza a colpire la palla sottile.",
        drill=[("Setup con il bastone sulla schiena", [
            "Appoggia un bastone lungo la schiena: testa, scapole e osso sacro a contatto.",
            "Piegati dalle anche finché le braccia pendono sotto le spalle, poi fletti un po' le ginocchia.",
            "Ripeti 10 volte allo specchio prima di giocare."])],
        feel="Postura atletica, peso sull'avampiede, come un difensore di basket."),
    "postura_curva": dict(
        titolo="Postura troppo piegata al setup",
        descrizione="Al setup il busto è molto inclinato verso la palla.",
        perche="Si è troppo vicini alla palla o si incurva la schiena.",
        palla="Piano ripido e difficoltà a ruotare: colpi grassi e pull.",
        drill=[("Setup con il bastone sulla schiena", [
            "Appoggia un bastone lungo la schiena: testa, scapole e osso sacro a contatto.",
            "Piegati dalle anche solo finché le braccia pendono libere."])],
        feel="Schiena lunga, petto sopra la palla, non dentro la palla."),
    "postura_seduta": dict(
        titolo="Ginocchia troppo piegate",
        descrizione="Al setup le ginocchia sono molto flesse, come seduti.",
        perche="Si cerca stabilità abbassandosi.",
        palla="Difficile ruotare e mantenere l'altezza: contatto incostante.",
        drill=[("Flessione leggera", [
            "Parti con le gambe dritte, piegati dalle anche, poi \"sblocca\" appena le ginocchia."])],
        feel="Ginocchia morbide, non piegate."),
    "lontano_palla": dict(
        titolo="Troppo lontano dalla palla",
        descrizione="Al setup le mani sono molto più avanti delle spalle: le braccia si allungano.",
        perche="Si cerca un arco ampio allungando le braccia.",
        palla="Peso sulle punte, perdita di equilibrio e colpi di punta.",
        drill=[("Un palmo dalle cosce", [
            "Lascia pendere le braccia sotto le spalle e appoggia il bastone a terra.",
            "Tra il grip e la coscia ci deve stare circa un palmo."])],
        feel="Le braccia pendono libere sotto le spalle."),
    "vicino_palla": dict(
        titolo="Troppo vicino alla palla",
        descrizione="Al setup le mani sono indietro rispetto alle spalle.",
        perche="Spesso con un bastone troppo lungo o una postura troppo eretta.",
        palla="Poco spazio per le braccia: colpi di tacco e piano ripido.",
        drill=[("Un palmo dalle cosce", [
            "Lascia pendere le braccia sotto le spalle e appoggia il bastone a terra.",
            "Tra il grip e la coscia ci deve stare circa un palmo."])],
        feel="Spazio per le braccia: le mani non sfiorano le cosce."),
    "stance": dict(
        titolo="Larghezza dei piedi da sistemare",
        descrizione="La distanza tra i piedi non è adatta al bastone.",
        perche="Abitudine o mancanza di un riferimento al setup.",
        palla="Base troppo stretta: equilibrio precario. Troppo larga: rotazione bloccata.",
        drill=[("Riferimento a terra", [
            "Appoggia un bastone a terra lungo la linea dei piedi.",
            "Ferri: interno dei talloni sotto l'esterno delle spalle. Driver: un po' più largo."])],
        feel="Base stabile ma libera di ruotare."),
    "tilt_setup": dict(
        titolo="Spalle livellate al setup",
        descrizione="Al setup la colonna non è inclinata via dal bersaglio.",
        perche="Le mani impugnano il bastone a quote diverse: la spalla {D} dovrebbe stare un po' più bassa.",
        palla="Favorisce una discesa dall'esterno e colpi ripidi.",
        drill=[("Mano {D} sul ginocchio", [
            "Al setup fai scorrere la mano {D} fino al ginocchio {D}, poi riportala sul grip.",
            "La spalla {D} resta più bassa e la testa leggermente dietro la palla."])],
        feel="Spalla {D} più bassa, testa dietro la palla."),
}

FORZE = {
    "inclinazione_busto": "Postura al setup solida: busto piegato dalle anche nell'angolo giusto.",
    "flessione_ginocchia": "Gambe atletiche al setup.",
    "distanza_palla": "Distanza dalla palla corretta: le braccia pendono libere.",
    "larghezza_stance": "Base dei piedi adatta al bastone.",
    "rotazione_spalle": "Rotazione delle spalle completa al top.",
    "x_factor": "Buona separazione tra spalle e bacino al top: carichi energia.",
    "sway": "Bacino stabile nel backswing: ruoti senza scivolare.",
    "testa_backswing": "Testa ferma nel backswing.",
    "braccio_guida_top": "Braccio {G} esteso al top: arco ampio.",
    "over_the_top": "Discesa sul piano: le mani scendono dall'interno.",
    "sequenza": "Sequenza cinematica corretta: bacino, busto, braccia, bastone.",
    "early_extension": "Mantieni la postura fino all'impatto.",
    "peso_impatto": "Buon trasferimento del peso all'impatto.",
    "peso_finish": "Finish completo sul piede {G}.",
    "equilibrio": "Finish in equilibrio.",
    "rapporto_tempo": "Ritmo da giocatore esperto, vicino al 3:1.",
}


def _lati(mancino):
    return ("destro", "sinistro") if mancino else ("sinistro", "destro")


def _fmt(testo, mancino):
    g, d = _lati(mancino)
    return testo.replace("{G}", g).replace("{D}", d)


def _fmt_rec(obj, mancino):
    if isinstance(obj, str):
        return _fmt(obj, mancino)
    if isinstance(obj, (list, tuple)):
        return type(obj)(_fmt_rec(o, mancino) for o in obj)
    if isinstance(obj, dict):
        return {k: _fmt_rec(v, mancino) for k, v in obj.items()}
    return obj


def diagnosi(punteggi: dict, mancino: bool, n_max: int = 4):
    det = punteggi["dettaglio"]
    cat_peso = {k: v["peso"] for k, v in punteggi["categorie"].items()}
    gruppi = {}
    for nome, d in det.items():
        if d["punteggio"] >= 80 or nome not in MAPPA:
            continue
        lo, hi = d["ideale"]
        chiave = MAPPA[nome][0] if d["valore"] < lo else MAPPA[nome][1]
        if not chiave:
            continue
        conf = {"alta": 1.0, "media": 0.85, "bassa": 0.6}[d["conf"]]
        prio = (100 - d["punteggio"]) * d["peso"] * cat_peso[d["cat"]] / 100 * conf
        prio *= IMPATTO_PALLA.get(chiave, 1.0)
        g = gruppi.setdefault(chiave, dict(priorita=0, metriche=[]))
        g["priorita"] += prio
        g["metriche"].append(nome)
    ordinati = sorted(gruppi.items(), key=lambda kv: -kv[1]["priorita"])[:n_max]
    out = []
    for chiave, g in ordinati:
        voce = _fmt_rec(dict(DIFETTI[chiave]), mancino)
        principale = max(g["metriche"], key=lambda n: (100 - det[n]["punteggio"]) * det[n]["peso"])
        voce.update(id=chiave, priorita=g["priorita"], metriche=g["metriche"],
                    metrica=principale, fase=det[principale]["fase"],
                    vista=det[principale]["vista"].split("+")[0])
        out.append(voce)
    return out


def punti_di_forza(punteggi: dict, mancino: bool, n_max: int = 4):
    det = punteggi["dettaglio"]
    cand = [(n, d) for n, d in det.items() if d["assoluto"] >= 95 and n in FORZE]
    cand.sort(key=lambda nd: (-nd[1]["peso"], nd[1]["conf"] != "media"))
    return [dict(id=n, testo=_fmt(FORZE[n], mancino), fase=d["fase"],
                 vista=d["vista"].split("+")[0], metrica=n) for n, d in cand[:n_max]]


def piano(difetti: list, settimane: int = 2, sessioni: int = 3):
    """Piano progressivo: settimana 1 movimento lento, settimana 2 velocità e campo."""
    if not difetti:
        return []
    p = difetti[:3]
    piano = []
    for s in range(1, settimane + 1):
        for k in range(1, sessioni + 1):
            focus = p[(k - 1) % len(p)] if s == 1 else p[0]
            secondo = p[(k) % len(p)] if len(p) > 1 else None
            blocchi = [("10'", "Riscaldamento: mobilità di anche e spalle, 10 swing senza palla.")]
            d1 = focus["drill"][0]
            if s == 1:
                blocchi.append(("20'", f"{d1[0]} — senza palla e poi a mezza velocità (30-40 palle). "
                                       f"Obiettivo: {focus['titolo'].lower()}."))
                if secondo and secondo is not focus:
                    blocchi.append(("15'", f"{secondo['drill'][0][0]} — 20 palle."))
                blocchi.append(("10'", "Colpi normali con ferro 7 cercando il feel: "
                                       f"\"{focus['feel']}\""))
            else:
                velocita = "70%" if k == 1 else ("80%" if k == 2 else "100%")
                blocchi.append(("15'", f"{d1[0]} al {velocita} di velocità (25 palle)."))
                if secondo:
                    blocchi.append(("15'", f"{secondo['drill'][0][0]} — 20 palle, poi alterna: "
                                           "un colpo di drill e uno normale."))
                blocchi.append(("15'", "Simulazione di campo: cambia bastone e bersaglio a ogni colpo, "
                                       "routine completa."))
                if k == sessioni:
                    blocchi.append(("5'", "Rigira i video con le stesse angolazioni e confronta il report."))
            piano.append(dict(settimana=s, sessione=k, blocchi=blocchi))
    return piano
