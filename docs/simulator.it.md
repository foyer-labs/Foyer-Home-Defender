# Il simulatore, e come leggere una traccia della decisione

[English](simulator.md) · **Italiano**

Il senso di un allarme configurato da te è che puoi verificarlo prima di
fidarti. Questa pagina parla delle due schede di **Test e diagnostica** che
fanno la verifica senza far scattare niente: la tabella delle zone in tempo
reale, e il simulatore.

Tutte e due si limitano a leggere. Nessuna delle due può cambiare cosa è
inserito, e nessuna può eseguire un'azione. Serve il permesso di leggere il
registro e niente di più — se puoi vedere chi ha disinserito alle 03:14, puoi
di certo vedere che la finestra della cucina è una zona ritardata con trenta
secondi di ritardo d'ingresso.

---

<a id="diagnostics-am-i-looking-at-the-right-sensor"></a>

## Diagnostica: sto guardando il sensore giusto?

È la prima domanda dopo un'installazione, ed è quella a cui è più difficile
rispondere dalle pagine di configurazione, perché mostrano quello che
*intendevi*. La tabella mostra quello che c'è davvero, una riga per ogni zona
mappata.

| Colonna | A cosa risponde |
|---|---|
| **Entità** | Quale entità di Home Assistant c'è dietro questa zona. Una zona la cui entità è stata rinominata non mostra nessuno stato, e l'entità viene elencata a parte sopra la tabella — è di gran lunga il guasto silenzioso più comune |
| **Stato** | Cosa dice quell'entità in questo momento, così com'è |
| **Valutazione del trigger** | Se Foyer lo conterebbe come *scattata*, letto attraverso il trigger di questa zona |
| **Ultima variazione** | Quando lo stato è cambiato l'ultima volta — non quando il sensore si è fatto sentire l'ultima volta |
| **Salute** | Raggiungibile, oppure il motivo per cui non lo è |
| **Batteria** | Il livello riportato dalla sua entità batteria, e se conta come scarica |
| **Segnale** | La qualità della radio, dove l'integrazione la espone |
| **Limite di silenzio** | L'intervallo entro cui questo sensore deve riportare qualcosa |
| **Inserimento** | Se questa zona impedirebbe l'inserimento della sua area, e per quale dei due motivi |

<a id="why-trigger-evaluation-is-a-separate-column-from-state"></a>

### Perché la «valutazione del trigger» è una colonna separata dallo «stato»

Perché `on` non vuol dire allarme. Un contatto magnetico normalmente chiuso
legge `off` quando la porta è *aperta*, e una zona configurata per quel
contatto va in allarme su `off`. Una tabella che mostrasse solo lo stato
grezzo sembrerebbe tranquilla mentre la zona scatta, e una tabella che desse
per scontato `on` sbaglierebbe su metà dei contatti che la gente possiede.

Quindi la colonna è la lettura del motore stesso, attraverso il trigger che
hai confermato nell'editor della zona. Se dice *Non scatterebbe* mentre sei
davanti a una porta aperta, il trigger è sbagliato — ed è proprio il bug che
sei venuto a cercare qui, invece di uno che scopri durante un furto.

<a id="why-arming-is-a-separate-column-from-health"></a>

### Perché l'«inserimento» è una colonna separata dalla «salute»

Una zona può stare benissimo e impedire comunque l'inserimento della casa: è
aperta e la sua regola all'inserimento è *Blocca l'inserimento*. E una zona
può essere in guasto — irraggiungibile, o muta oltre il suo limite di
silenzio — e allora blocca per un motivo diverso, che chiede un rimedio
diverso. La colonna dice quale dei due, così la risposta è «chiudi la porta
del terrazzo» o «il sensore del garage è uscito dalla rete», non «qualcosa non
va».

Questa colonna è la stessa funzione che il motore usa quando rifiuta un
inserimento per un guasto o per una zona aperta, quindi non può dire *pronta*
dove una zona bloccherebbe; un codice, un permesso o un walk test in corso
possono comunque rifiutare la richiesta.

<a id="batteries"></a>

### Batterie

Una zona può indicare l'entità che riporta la sua batteria. A quel punto
possono andare storte due cose diverse, e vengono trattate diversamente di
proposito:

- **Una batteria scarica avvisa e non blocca mai.** Un contatto che riporta il
  15 % vede ancora la porta. Una casa con quaranta zone a batteria che non si
  può inserire la mattina in cui una di loro scende è un allarme che finisce
  spento — quindi il momento viene invece segnalato una volta sola, mentre la
  batteria scende, e *ogni* tentativo d'inserimento dice quali zone sono
  andate sotto guardia con una pila che si sta esaurendo. Se di una preferisci
  non fidarti, escludila da quell'inserimento: è una normale esclusione
  manuale e finisce quando disinserisci.
- **Un'entità batteria che non si riesce proprio a leggere è un guasto, e
  blocca.** Un sensore di batteria che è diventato muto è una radio che è
  diventata muta, e il contatto accanto è la prossima cosa che smetterà di
  riportare.

Cosa conta come scarica è un'impostazione unica per l'impianto, a pagina 11,
20 % di default. Un `binary_sensor` di batteria viene invece letto secondo la
convenzione di Home Assistant, in cui `on` vuol dire scarica.

<a id="arming-devices"></a>

### Dispositivi di inserimento

Tastierini, tag e telecomandi hanno una tabella tutta loro sotto le zone. Un
tastierino non può bloccare l'inserimento, quindi non ha niente da fare in una
colonna sull'inserimento; e un tastierino che parla solo via MQTT non ha
nessuna entità, cosa che la tabella dice invece di mostrarlo come sano. Un tag
la cui entità è diventata non disponibile è esattamente il genere di cosa che
questa pagina esiste per far emergere.

---

<a id="the-simulator"></a>

## Il simulatore

> **Qui non viene eseguito nulla.** Il simulatore chiama lo stesso motore
> decisionale che chiama l'allarme, con un mondo e un orologio inventati, e poi
> semplicemente non consegna mai il risultato alla parte che farebbe suonare
> le sirene.

Quella frase è una garanzia strutturale, non una promessa. Il motore è una
funzione pura — non esegue nessuna azione, non raggiunge nessuno stato di Home
Assistant e non legge nessun orologio che non gli sia stato passato — quindi
«eseguilo e butta via la risposta» è tutta l'implementazione. Un test verifica
che il simulatore e l'impianto vero arrivino a una decisione identica da input
identici; se quel test fallisce, il bug è un secondo percorso di valutazione da
qualche parte, mai la traccia.

<a id="what-you-set"></a>

### Cosa imposti

- **Uno scenario**, o nessuno. *Nessuno — casa disinserita* è anche quella una
  domanda vera: una zona 24h, una manomissione e un rilevatore di fumo
  rispondono tutti a casa disinserita.
- **Una data e un'ora.** È ciò su cui si legge una condizione oraria. La
  stessa configurazione alle 19:32 e alle 23:32 dà due risposte diverse, e il
  campo è il modo di verificarle entrambe.
- **Zone forzate in uno stato**, ognuna a un numero di secondi a tua scelta
  **da quando la casa ha finito di inserirsi** — non dall'inizio della corsa,
  perché la corsa comincia inserendo, e un tempo contato dall'inizio
  metterebbe la zona dentro il ritardo d'uscita. Zero vuol dire quindi quello
  che intendi: inserita, e poi succede questo. Il tempo esiste perché un
  gruppo di verifica che arriva a due su due, o una seconda zona che si
  unisce a un incidente, accadono *in sequenza*, e due zone forzate nello
  stesso istante non possono mostrare né l'una né l'altra cosa.
- **Le entità usate nelle condizioni, e le persone che una regola automatica
  osserva.** Solo quelle che la tua configurazione legge davvero — «solo se
  non c'è nessuno in casa» si può provare in tutti e due i sensi, e così
  «sono usciti tutti». Lasciane una vuota per usare quello che dice davvero
  adesso.

**Se il tuo impianto chiede un codice per inserire**, lo chiede anche il
simulatore. La premessa è un inserimento vero, fatto passare dal motore vero,
e il §8.2 non prevede eccezioni per una prova — inventarne una sarebbe un
secondo percorso di autorizzazione, che è esattamente ciò che questa funzione
è costruita per evitare. La traccia lo dice alla prima riga e la pagina offre
il campo. In ogni caso non viene eseguito nulla. Un codice digitato lì è un
codice vero, controllato e contato come qualunque altro: un codice
di coercizione solleva il suo `duress` silenzioso per la richiesta, e la
prova procede poi come farebbe il codice normale, così la traccia non lo
mostra mai.

La casa parte disinserita qualunque cosa stia facendo davvero, con le letture
attuali reali dei tuoi sensori sotto le tue forzature. Se una finestra è
davvero aperta, il simulatore ti dirà che l'inserimento verrebbe rifiutato, ed
è una risposta utile più che un ostacolo: forzala chiusa e chiedi di nuovo.

Due cose della casa **non** sono ipotetiche e arrivano con la corsa:
l'interruttore generale delle regole automatiche, e qualunque sospensione in
vigore. Così «si inserirebbe domattina, con il tecnico della caldaia
atteso?» è una domanda a cui il simulatore sa rispondere — e una regola che
scatta alle 23:00 nei giorni feriali si può provare alle undici di un lunedì
mattina portando l'orologio a quell'ora. Quello che la traccia dice di una
regola, compreso il controllo di sicurezza che la bloccherebbe, viene letto
dalla stessa decisione su cui agirebbe l'impianto vero (§9.4).

<a id="reading-the-trace"></a>

### Leggere la traccia

Un esempio svolto, del caso su cui è più difficile ragionare:

```
21:32:00  Area «Ground floor»: Disinserito → In inserimento · ritardo d'uscita fino alle 21:32:05
21:32:05  Area «Ground floor»: In inserimento → Inserito
          Profilo «Full», ereditato dall'area
21:33:00  Zona «Open plan PIR 1» → on
          Area «Ground floor»: Inserito → In allarme · sirena fino alle 21:36:00
          Gruppo «Open plan»: 1 su 2 entro 60 s → non soddisfatto
          Incidente aperto 20260914-193300-1
            Profilo «Silent», ereditato dalla zona
            ✓ Notify Luca
          ⏱ fine della sirena alle 21:36:00
21:33:30  Zona «Open plan PIR 2» → on
          Gruppo «Open plan»: 2 su 2 entro 60 s → SODDISFATTO
          Zona aggiunta all'incidente 20260914-193300-1
            Profilo «Full», ereditato dal gruppo
            ✓ Indoor siren
            ✗ Hall lights — condizione non soddisfatta: orario 22:00-07:00
            ✗ Push to the NAS — condizione non soddisfatta: binary_sensor.nobody_home è on
            ✗ Landing lights — trattenuta da un ritardo precedente nella sequenza
            ✓ passo di escalation 0 → Luca (Push)
          ⏱ passo di escalation 1 a +60s → Luca (SMS)
          ⏱ passo di escalation 2 a +120s → Partner (Push)
21:36:00  Area «Ground floor»: In allarme → Inserito
          Fine della sirena
```

Quattro tipi di riga, e ognuno è lì per un motivo.

**Cosa è successo.** La zona che si è mossa, l'area che ha cambiato stato, e
quale timer ora è in corso e fino a quando. Il timer è quello del motore — se
la riga dice che la sirena si ferma alle 21:36, quello è il timer della sirena,
non un numero calcolato per la visualizzazione.

**Lo stato del gruppo, non solo la zona.** Un gruppo è lo strumento più forte
che ci sia contro i falsi allarmi, ed è anche quello il cui comportamento si
vede di meno: un sensore fa una cosa, due sensori ne fanno un'altra. La
traccia mostra il conto a ogni attivazione — *1 su 2 entro 60 s* — così vedi
la finestra che si riempie e la vedi scadere.

**Quale profilo ha risposto, e da dove viene.** È la riga che spiega una
risposta che altrimenti sembra arbitraria. Il profilo di una zona risponde al
suo allarme; un gruppo soddisfatto risponde con quello del gruppo; tutto il
resto risponde dall'area, poi dallo scenario, poi dal profilo predefinito
globale. Nell'esempio sopra, un PIR da solo è *Silent* (il profilo della zona)
e due entro la finestra sono *Full* (quello del gruppo) — che è una risposta
graduata, e la vedi accadere.

**Ogni azione, comprese quelle che non sono partite.** Una spunta vuol dire
che è partita. Una croce vuol dire che non è partita, con il motivo:

| Motivo | Cosa vuol dire |
|---|---|
| **condizione non soddisfatta: …** | Quale condizione è fallita, scritta per intero. Una fascia oraria è mostrata con le sue ore; una condizione su un'entità con l'entità e lo stato che voleva |
| **trattenuta da un ritardo precedente nella sequenza** | Non saltata — partirà, e la riga ⏱ dice quando |
| **già in corso per questo incidente, non riavviata** | Una sirena che sta già suonando non viene riavviata quando si aggiunge una seconda zona (§5.6) |
| **ogni contatto indicato è nelle sue ore di silenzio** | La notifica indicava dei contatti e la fascia li ha trattenuti tutti. Nessuno sarebbe stato avvisato, quindi non è stato inviato niente |
| **questa zona è silenziosa e la sopprime** | La zona è segnata come silenziosa, e questa azione è di un tipo che una zona silenziosa non esegue |
| **non è configurato nulla per questo momento** | Il profilo ha risposto, e non ha azioni per questo momento. Viene mostrato solo dove è questa la scoperta — un gruppo soddisfatto con un profilo vuoto è il motivo per cui la sirena è rimasta zitta |

**Chi viene avvisato, e chi è il prossimo.** Una notifica dice quali contatti
ha raggiunto e attraverso quale canale, e le righe ⏱ di escalation dicono chi
viene dopo e quando. Sono lette dalla decisione prodotta dal motore, non
ricalcolate per la visualizzazione: quello che la traccia mostra è il
calendario che la casa seguirebbe davvero, e si ferma alla prima presa d'atto
esattamente come quello vero. Anche un contatto nelle sue ore di silenzio
viene nominato, come trattenuto e non come raggiunto.

**Cosa deve ancora venire.** Le righe ⏱: la fine di una sirena, il resto di
una sequenza trattenuta da un ritardo, i passi di escalation ancora da fare.
Ognuna viene annunciata una volta sola, nel momento in cui viene programmata,
invece di essere ripetuta sotto ogni passo successivo.

<a id="things-worth-rehearsing-before-you-trust-a-configuration"></a>

### Cose da provare prima di fidarti di una configurazione

- **Il rientro a casa.** Forza la zona ritardata da cui passa il tuo percorso,
  poi la zona percorso che viene dopo. La zona percorso deve ereditare la
  finestra d'ingresso in corso, non far partire un allarme. Se va dritta in
  allarme, la sua lista `follows` è sbagliata — e lo scopri adesso invece che
  alla porta di casa.
- **Un'azione con una condizione, a tutte e due le ore.** Eseguila alle 19:00
  e alle 23:00. È tutto il senso del campo dell'orologio.
- **Un gruppo.** Forza un membro, poi l'altro trenta secondi dopo, poi riprova
  con novanta secondi fra i due e guarda la finestra scadere.
- **Lo scenario che usi davvero di notte.** La risposta più utile che il
  simulatore dà è spesso la prima riga: *non si può inserire, zona in guasto*.

<a id="every-run-is-logged"></a>

### Ogni corsa viene registrata

Sotto `system`, con i suoi input — lo scenario, l'orologio, le zone che hai
forzato e quando. Sei mesi dopo, «perché l'ingresso ha un profilo diverso?» ha
una risposta che include la corsa che ha giustificato il cambiamento.

<a id="limits-stated-plainly"></a>

### I limiti, detti chiaramente

- **Una corsa ha un limite.** Quindici minuti di tempo simulato dal momento in
  cui la casa è inserita, di default, e un
  tetto al numero di decisioni che può prendere per arrivarci. Quando si ferma
  con qualcosa di suo ancora in corso — un'area in conto alla rovescia, una
  sequenza trattenuta da un ritardo — lo dice, invece di finire come se la casa
  fosse tornata tranquilla.
- **Prova la decisione, non il trasporto.** Ti dice che una notifica verrebbe
  inviata a un certo destinatario; non ti dice che il destinatario funziona. A
  quello serve la vera prova delle azioni — la scheda accanto a questa.
- **Non sostituisce un walk test.** Forzare una zona in uno stato dimostra
  cosa ne fa il motore. Non dimostra niente sul fatto che il PIR del corridoio
  sia puntato sul corridoio. Quella è la scheda successiva.

<a id="the-two-tabs-that-act"></a>

## Le due schede che agiscono

Il simulatore e la tabella della diagnostica si limitano a guardare. Le altre
due schede della pagina 9 fanno qualcosa, e sono il modo di rispondere alle
due domande a cui una prova non sa rispondere.

<a id="walk-test--which-zones-never-saw-you"></a>

### Walk test — quali zone non ti hanno mai visto

Ogni area che può inserirsi viene inserita davvero, ogni sensore viene letto
davvero, e la risposta viene trattenuta. Fai il giro della casa; la tabella si
riempie.

Leggila dall'alto. Le zone elencate per prime sono quelle che **non** hanno
reagito, e sono loro la scoperta: una porta che nessuno ha aperto e un PIR
puntato sul muro sbagliato lì sembrano identici, quindi ripassa da quelle che
ti aspettavi scattassero prima di concludere qualcosa. Una zona in guasto è
segnata come tale nella stessa riga, perché non avrebbe potuto reagire.

Sei cose da sapere prima di avviarne uno:

- **Le zone 24h, di manomissione, tecniche e di panico restano completamente
  attive**, allarme compreso. Un walk test non silenzia mai un rilevatore di
  fumo. Sono anche lasciate fuori dalla tabella: sono attive, non sotto test,
  e nessuno fa scattare il rilevatore di fumo per dimostrare che funziona.
- **Un rilevamento non muove niente.** Nessun allarme, nessun incidente,
  nessuna memoria d'allarme, e niente dice a HomeKit, Google o Alexa che
  qualcuno è entrato con effrazione. Altrimenti quaranta zone percorse
  lascerebbero quaranta allarmi nel registro.
- **Finisce da solo, e non puoi impedirgli di finire.** Il tempo massimo
  decorre dall'ultimo rilevamento, così una casa grande si può percorrere in
  un solo giro, e un tetto assoluto lo chiude comunque vada. Mentre è in
  corso, un'intrusione vera non produce niente — ed è per questo che il banner
  compare su ogni schermata, che il suo inizio e la sua fine vengono annunciati
  (dal profilo, o da una notifica di Home Assistant che Foyer crea da sé
  quando nessuna azione del profilo ne invia una), e che l'ingresso e l'uscita
  sono tutti e due nel registro con il tuo nome.
- **Un'area che non può inserirsi resta fuori**, e la pagina nomina le zone
  che l'hanno tenuta fuori. Le sue altre zone vengono comunque registrate
  quando ti rilevano; la zona che tiene aperta l'area non può cambiare finché
  non viene chiusa, quindi chiudi la finestra e rifallo invece di leggere
  quella riga come un sensore morto.
- **Lo stesso vale per un'area che ha ancora la memoria d'allarme.** Il test
  inserisce per un giro, non per una sorveglianza, quindi non è l'inserimento
  che azzera la memoria, e l'area la conserva dopo il test. Le sue zone
  vengono comunque registrate quando ti rilevano. Disinserisci prima l'area
  se vuoi percorrerla inserita.
- **Copre tutta la casa, chiunque lo avvii.** Ogni area disinserita che può
  inserirsi viene inserita, comprese le aree che non sono tue, e un'area
  inserita da qualcun altro resta inserita ma smette anche lei di rispondere
  finché il test non finisce. Il permesso `walk_test` può quindi tenere zitta
  una casa inserita senza `disarm` — quindici minuti dopo l'ultimo
  rilevamento di default, mai più di tre ore per test, e niente impedisce di
  riavviarlo appena finisce — quindi si concede come si concede `disarm`, e
  di default chiede un codice. La pagina Utenti lo dice accanto al permesso.

<a id="action-test--press-the-button-before-the-night-you-need-it"></a>

### Prova azioni — premi il pulsante prima della notte in cui ti serve

Un pulsante di prova accanto a ogni azione, e la esegue davvero: la sirena
suona davvero — per tre secondi, dopo i quali Foyer la spegne, che accetti una
durata o che sia comandata da uno switch — e la notifica parte davvero.
Chiede prima conferma, richiede il permesso `test_actions` e un codice, e ogni
esecuzione lascia nel registro una riga segnata come prova.

Vale il rumore per un motivo solo. Il modo peggiore di scoprire che un
servizio di notifica è stato rinominato, o che il telefono che doveva essere
chiamato non fa più parte della famiglia, è nel momento in cui l'allarme sta
cercando di usarlo.

Lo stesso pulsante si trova accanto a ogni azione nella pagina 5, dove hai
appena finito di configurarla e ti stai chiedendo se arriva.
