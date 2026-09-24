# Passare da Alarmo

[English](migrating-from-alarmo.md) · **Italiano**

Nessuno con quaranta sensori configurati li rimappa a mano per provare
qualcosa di nuovo, quindi Foyer può leggere una configurazione di
[Alarmo](https://github.com/nielsfaber/alarmo) già esistente e portarla
dentro. Questa pagina è per una casa in cui Alarmo gira già: cosa legge
l'importatore, cosa ne ricava, cosa lascia a te e cosa controllare prima di
fidarti del risultato. Leggila prima di premere qualunque cosa.

---

## Cos'è

**Uno strumento al meglio delle possibilità, che ti dice cosa non è riuscito a
convertire: non una migrazione garantita.** Legge `.storage/alarmo.storage`, il
file in cui Alarmo tiene la sua configurazione. Quel file è il formato interno
di Alarmo: il suo autore può cambiarlo in qualunque versione, senza preavviso e
senza colpa, perché non è mai stato offerto a nessuno come interfaccia. Per
questo l'importatore sta attento a cosa accetta, e dice tutto quello che non ha
fatto.

- **Legge solo le versioni di archiviazione su cui è stato verificato, e
  rifiuta tutte le altre dicendo quale.** Oggi sono i formati da 6.1 a 6.3,
  quelli che scrivono Alarmo dalla 1.9.5 alla 1.10.19. Il file non contiene il
  numero di versione di Alarmo, solo la sua versione di archiviazione, quindi è
  quella che un rifiuto nomina. Da un file rifiutato non viene importato niente.
- **Rifiuta un file che ha una forma sbagliata invece di portarne metà**, e
  dice in che punto del file si è fermato. Allo stesso modo rifiuta una sezione
  con più di 1.000 elementi, o un file più grande di 4 MB.
- **Un campo che non conosce è una riga del report, non un rifiuto**: quello
  che quel campo fa in Alarmo non è stato importato, e il report lo nomina.
- **Non si carica nessun file.** Il file viene letto dall'Home Assistant con
  cui sta parlando il pannello, quindi l'importatore guarda sempre e solo
  l'Alarmo di questa casa.

## Dov'è, e chi può usarlo

*Impostazioni* → la scheda *Importa da Alarmo*. Ha due pulsanti: *Leggi da
Alarmo* e, quando c'è qualcosa da applicare, *Applica*.

| Passo | Cosa richiede |
|---|---|
| *Leggi da Alarmo* (l'anteprima) | *Modificare la configurazione*. Non scrive niente, quindi non chiede nessun codice. |
| *Applica* | *Modificare la configurazione*, e il tuo codice quando Foyer ne chiede uno per cambiare la configurazione. Se l'importazione creerebbe delle persone, anche *Gestire utenti e codici*, perché portare dentro delle persone cambia chi può comandare la casa, in qualunque modo lo si faccia. |

Un amministratore di Home Assistant non viene mai respinto per mancanza di un
permesso, ma il codice vale anche per lui. Un *Applica* rifiutato per un
permesso mancante o un codice sbagliato lascia una riga nel registro, come
qualunque modifica rifiutata.

## Prima l'anteprima, poi applichi

*Leggi da Alarmo* mostra cosa farebbe l'importazione prima di scrivere
qualsiasi cosa:

- **Cosa verrebbe aggiunto**: le aree, gli scenari nuovi, gli scenari esistenti
  che inserirebbero anche ciò che viene importato, le persone (senza codice), i
  profili di risposta, e quante zone, disattivate finché non confermate.
- **Cosa sapere prima di applicare**: il report, una riga per ogni scelta che
  l'importatore ha fatto al posto tuo e per tutto quello che non ha potuto
  portare.
- Gli eventuali problemi che la configurazione avrebbe dopo l'importazione,
  con gli stessi controlli di ogni modifica. Finché ce n'è uno, *Applica*
  resta non disponibile.

*Applica* salva esattamente quello che l'anteprima ha mostrato, e niente di
diverso. Viene rifiutato, con un messaggio che ti chiede di rileggere, se da
allora è cambiato qualcosa da cui l'anteprima era stata calcolata: il file di
Alarmo, la configurazione di Foyer (una modifica fatta da un'altra scheda del
browser, per esempio), oppure il nome o la presenza di uno dei sensori elencati
nel file. Non viene mai rifiutato perché è cambiato lo *stato* di un sensore,
perché un sensore di movimento lo fa ogni volta che qualcuno gli passa davanti.

Un'importazione è una modifica della configurazione come le altre. Passa per
la stessa validazione, viene rifiutata finché un'area inserita o uno scenario
in corso dipende da qualcosa che cambierebbe, e lascia una riga nel registro.

### Aggiunge, non sostituisce

Tutto viene portato **accanto a quello che c'è già**. Niente di quello che hai
viene tolto o riscritto, con un'eccezione descritta più sotto (uno scenario
esistente può essere esteso per inserire anche le aree nuove).

- Un sensore che è già una zona di Foyer resta esattamente com'è.
- Una persona il cui nome è già in *Utenti* resta esattamente com'è.
- Un nome già usato da un'area, una zona o uno scenario riceve un numero, e il
  report lo dice.

## Cosa converte

| Alarmo | Foyer |
|---|---|
| **Un'area** | Un'area di Foyer, oppure più d'una, quando i suoi sensori erano sorvegliati in modalità diverse. In Foyer uno scenario inserisce aree intere, quindi «il sensore di movimento solo in Fuori casa, le porte in tutte le modalità» diventa due aree che lo scenario Fuori casa inserisce insieme e lo scenario In casa ne inserisce una. Il report nomina ogni divisione. |
| **Un sensore** | Una zona, nell'area che corrisponde alle sue modalità, con il nome che l'entità ha in Home Assistant. Un sensore `door`, `window`, `motion` o `other` diventa *Ritardata* se aveva un ritardo d'ingresso in almeno una delle sue modalità, *Istantanea* se no, oppure *24h* se era sempre attivo. Un sensore `environmental` diventa *Tecnica* e un sensore `tamper` *Manomissione*: tutte e due sorvegliano sempre, come quei tipi devono fare, e il report lo dice quando in Alarmo erano attivi solo in alcune modalità. |
| **Una modalità che avevi abilitato** | Uno scenario che inserisce ogni area sorvegliata in quella modalità, e riporta quella modalità a Home Assistant. Se hai già uno scenario che riporta la stessa modalità, viene esteso quello per inserire le aree nuove, così HomeKit e gli assistenti vocali continuano a funzionare: un secondo scenario farebbe rifiutare quella modalità a *Tutta la casa*. |
| **Ritardi d'uscita e d'ingresso, tempo della sirena** | Dovunque Alarmo avesse più valori e Foyer abbia posto per uno solo, il più lungo, perché un ritardo troppo corto chiude qualcuno fuori da casa sua con la sirena che suona. Un valore oltre il limite di Foyer prende il limite: 300 s per i ritardi d'uscita e d'ingresso, 900 s per la sirena. Anche una sirena che suonava finché qualcuno non disinseriva diventa 900 s. Ognuna di queste scelte è una riga del report. |
| **Cosa succede a un sensore aperto all'inserimento** | *Se aperta all'inserimento*: *Inserisci dopo la chiusura* per un sensore che inseriva la casa quando si chiudeva; *Ignora* per uno che poteva restare aperto; *Escludi automaticamente* per uno escluso automaticamente in tutte le modalità in cui era sorvegliato; *Blocca l'inserimento* negli altri casi, compreso un sensore escluso in alcune modalità e non in altre, perché Foyer ha una sola regola per zona e quella è la metà sicura. |
| **Una persona** | Un utente di Foyer, abilitato o no come lo era, **senza codice**. Poteva inserire: *Inserire* e *Cambiare scenario*. Poteva disinserire: *Disinserire*. Un codice di forzatura: *Inserimento forzato*. Limitata ad alcune aree: limitata alle aree in cui quelle si sono trasformate. |
| **Un'automazione d'azione che fa suonare una sirena o comanda un interruttore** | Un profilo di risposta per ogni area di Alarmo, che parte come copia del tuo profilo predefinito (così un'area importata avvisa ancora chi avvisava il predefinito) più quelle sirene e quegli interruttori. `armed`, `disarmed`, `triggered`, `untriggered`, `arm_failure` e `pending` di Alarmo diventano i momenti *Inserito*, *Disinserito*, *Allarme*, *Fine dell'allarme*, *Inserimento fallito* e *Ritardo d'ingresso avviato*. Una sirena viene importata solo quando suona all'allarme vero e proprio, senza un tono o una durata suoi; importata negli altri casi, diventerebbe la sirena piena per tutto il tempo. |

Gli scenari nuovi hanno un ritardo d'uscita e una durata della sirena propri,
presi dalle modalità di Alarmo da cui vengono. Uno scenario che è stato esteso
mantiene le sue impostazioni, che adesso valgono anche per le aree importate;
se ha un ritardo d'uscita o una durata della sirena propri, il report lo dice.
Se risponde con un profilo di risposta suo e a un'area importata ne è stato
dato uno, quell'area non eredita più quello dello scenario, e anche questo il
report lo dice.

## Cosa non converte

Ognuna di queste cose è una riga del report, non un tentativo di indovinare:

- **I codici.** Nessuno, mai: vedi [più sotto](#le-persone-arrivano-senza-codice).
- **Le notifiche.** Una notifica che arriva dove non dovrebbe è peggio di una
  che imposti di nuovo. In Foyer le notifiche vanno ai contatti, nella pagina
  *Contatti*; vedi [canali di notifica](notification-channels.md) (in inglese).
- **Le altre automazioni**: quelle disattivate in Alarmo; quelle che partono
  dallo stato di un'entità o dall'inizio dell'inserimento, per cui un profilo
  di risposta non ha un momento; quelle limitate ad alcune modalità, a meno
  che comprendano tutte le modalità importate, perché un profilo di Foyer
  risponde per un'area qualunque sia lo scenario; quelle per un'area che non
  è stata importata. Un'automazione che spegne una sirena non serve, perché
  Foyer spegne da sé le sue sirene quando disinserisci e quando finisce il
  tempo della sirena. Un'azione che non è una sirena né un interruttore viene
  tolta dall'automazione, e nominata.
- **I gruppi di sensori.** Un gruppo ha bisogno dei suoi membri attivi, e ogni
  zona importata parte disattivata. Crealo nella pagina *Gruppi di verifica*
  quando le zone saranno confermate; il report dà per ogni gruppo il numero, i
  membri e la finestra.
- **Le impostazioni di Alarmo**, quando erano attive: codice per inserire,
  codice per cambiare modalità, codice per disinserire, disinserisci quando
  finisce il tempo della sirena, reinserisci anche con sensori aperti, e MQTT.
  Le [impostazioni](settings.it.md) di Foyer restano come sono.
- **Un sensore che Foyer non può usare**: uno che non è un `binary_sensor`,
  `cover`, `lock`, `switch` o `input_boolean`; uno non sorvegliato in nessuna
  delle modalità abilitate nella sua area; uno in un'area che manca dal file.
  Un'area rimasta senza sensori, o senza nessuna modalità abilitata, non
  diventa un'area di Foyer.
- **Quello che una zona non può portare con sé.** Un sensore che faceva
  scattare l'allarme quando diventava non disponibile in Foyer è invece un
  guasto: blocca l'inserimento e viene segnalato, ma non fa suonare. Un
  sensore che doveva restare attivo per qualche secondo prima: Foyer
  interviene al primo scatto. Un sensore che interrompeva l'inserimento appena
  si apriva durante il ritardo d'uscita: Foyer lo controlla quando premi
  inserisci e quando il ritardo finisce. Un sensore con cui Alarmo ti lasciava
  inserire da aperto, purché si chiudesse prima della fine del ritardo
  d'uscita: con *Blocca l'inserimento* deve essere chiuso quando premi
  inserisci.

Un sensore nominato nel file che in questo momento non esiste in Home
Assistant diventa comunque una zona, e risulta in guasto finché l'entità non
torna. Anche un sensore che era disattivato in Alarmo viene importato, e il
report lo dice: confermarne il trigger non ti obbliga ad attivarlo.

## Ogni zona arriva disattivata

Alarmo legge `on`, `open` e `unlocked` come allarme per qualunque sensore, e
`unavailable` come quiete se non gli si dice altro. È un'unica lista per ogni
tipo di sensore, e un contatto normalmente chiuso (NC) si legge al contrario.
Foyer non si porta dietro questo presupposto: ogni zona arriva con **la
proposta di Foyer** per il suo trigger, ricavata dal tipo di sensore (la
stessa che fa la procedura guidata delle zone), **non confermata, e
disattivata**.

La pagina *Zone* segna una zona così come *Trigger da confermare*, e quando la
apri spiega perché. Non si può attivare finché qualcuno non ha provato il
sensore, corretto il trigger se è sbagliato e spuntato *Ho verificato questi
stati sul sensore reale*. Lo impone la validazione su ogni strada che salva una
configurazione (l'editor, un ripristino, una seconda importazione), non solo
la pagina. Un trigger sbagliato è una zona che non scatta mai, e lo scopri
durante un'effrazione; vedi [zone](zones.it.md).

In Foyer un sensore che diventa non disponibile è un guasto: blocca
l'inserimento e viene segnalato. Lo dice anche il report.

## Le persone arrivano senza codice

Alarmo conserva i codici come hash nel proprio formato, e Foyer non accetta
sulla fiducia una credenziale da un altro sistema: i codici del file vengono
letti solo per controllare che siano testo, e poi mai più. Chiunque sia stato
importato ha bisogno di un codice nuovo nella pagina *Utenti* prima di poter
disinserire con un codice.

**La prima riga del report lo dice**, ogni volta: anche quando non è stata
importata nessuna persona nuova, e allora dice che chi può disinserire è chi è
già in *Utenti*. Se l'accesso di una persona era limitato ad aree che non sono
state importate, per ora non ne può usare nessuna, finché non lo allarghi lì.
Se uno scenario esteso è limitato ad alcune persone, quelle importate non sono
fra queste finché non le aggiungi in *Scenari*.

## Cosa controllare dopo

Dopo *Applica*, la scheda dice cosa viene dopo. In ordine:

- [ ] **Conferma ogni zona sul suo sensore.** Aprilo, chiudilo o passagli
      davanti, guarda cambiare lo stato, correggi il trigger se è sbagliato,
      spunta la conferma e attiva la zona. La [diagnostica](simulator.md#diagnostics-am-i-looking-at-the-right-sensor)
      (in inglese) mostra lo stato grezzo accanto alla lettura che ne fa Foyer.
- [ ] **Dai un codice a ogni persona importata** in *Utenti*, e controlla i
      suoi permessi e le sue aree.
- [ ] **Rifai le notifiche** come contatti in *Contatti*, e controlla in
      *Profili di risposta* che ogni profilo importato avvisi chi deve; vedi
      [profili di risposta](response-profiles.it.md).
- [ ] **Ricrea i gruppi di sensori** in *Gruppi di verifica*, quando i loro
      membri sono confermati.
- [ ] **Rileggi ogni scenario** in *Scenari*: cosa inserisce, il suo ritardo
      d'uscita, la durata della sirena.
- [ ] **Fai il giro della casa** con un [walk test](simulator.md#walk-test--which-zones-never-saw-you),
      e guarda quali zone non si sono accorte di te.
- [ ] **Prova una notte nel [simulatore](simulator.md#the-simulator)** prima
      di inserire per davvero.

## Usarli tutti e due insieme

Si possono installare entrambi nello stesso momento, ma **non puntarli sugli
stessi sensori**: avresti due sistemi che decidono cosa significa una finestra
aperta, e che si inseriscono e disinseriscono l'uno all'insaputa dell'altro.
Prova Foyer su qualche zona, o su un impianto di prova, e spostaci il resto
quando se lo sarà guadagnato.

L'importatore è fatto proprio per questo. Porta le zone disattivate, quindi
niente viene sorvegliato due volte finché non lo decidi tu. Come dice la
scheda stessa: finché le zone di Foyer non sono confermate, lascia che Alarmo
sorvegli la casa — ma non inserire mai entrambi sugli stessi sensori.
