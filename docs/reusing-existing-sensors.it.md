# Riusare i sensori di un antifurto esistente

[English](reusing-existing-sensors.md) · **Italiano**

Questa pagina è messa insieme dalla documentazione dei produttori e delle
integrazioni. Niente di quello che c'è scritto è stato provato su hardware da
questo progetto.

Molte case hanno già un antifurto: contatti sulle porte, PIR negli angoli,
una centrale in un armadio. Questa pagina è per chi vuole che Foyer legga
quei sensori invece di comprarne di nuovi. Descrive le strade con cui un
sensore che appartiene a un altro impianto può arrivare a Home Assistant,
quanto costa ciascuna, e come l'entità che ne esce diventa una zona di Foyer.
La scelta di sensori nuovi è un'altra pagina:
[scegliere i sensori](choosing-sensors.it.md).

Foyer legge entità di Home Assistant e nient'altro. Ogni strada qui sotto
finisce nello stesso posto — un'entità, di solito un `binary_sensor` — e la
domanda a cui risponde ciascuna è quanto quell'entità sia onesta sul sensore
che ha dietro.

---

## Quattro strade per entrare

| Strada | Cosa arriva a Home Assistant | Il rovescio |
|---|---|---|
| Un'integrazione nativa per la centrale | Ogni zona come la vede la centrale, attraverso il suo modulo di rete o il cloud del produttore | Solo quello che l'integrazione espone, e con la frequenza con cui interroga |
| Un'uscita programmabile collegata a un ingresso | Un contatto per uscita: «inserito», «allarme», «zona 3 aperta» | Un filo, un'informazione; scegli tu quali |
| Ascoltare il bus cablato | Tutto quello che passa sul bus | Rischio elettrico, e può far decadere un contratto di manutenzione |
| Ricevere la radio dei sensori stessi | Le trasmissioni di ogni sensore, ascoltate da un ricevitore tuo | Solo radio non cifrate, e nessuna supervisione |

### Un'integrazione nativa per la centrale

Alcune centrali hanno un'integrazione direttamente in Home Assistant. Ognuna
richiede il modulo di rete della centrale o un account cloud, e ognuna espone
le zone a modo suo. Queste esistono nell'elenco delle integrazioni di Home
Assistant; leggi la pagina della tua prima di comprare qualsiasi cosa, perché
il modulo e il firmware contano:

| Integrazione | Cosa richiede, secondo la sua documentazione |
|---|---|
| [Envisalink](https://www.home-assistant.io/integrations/envisalink/) | Una centrale DSC o Honeywell con una scheda EVL-3 o EVL-4; le zone diventano binary sensor |
| [Elk-M1](https://www.home-assistant.io/integrations/elkm1/) | Una centrale Elk M1, di solito attraverso la sua scheda Ethernet; le zone diventano binary sensor una volta impostata la centrale perché trasmetta i cambi di zona |
| [Risco](https://www.home-assistant.io/integrations/risco/) | Una centrale Risco, via cloud o con una connessione locale; come appare ogni zona dipende da quale delle due |
| [Satel Integra](https://www.home-assistant.io/integrations/satel_integra/) | Una centrale Integra con un modulo ETHM-1 Plus; zone e uscite diventano binary sensor |
| [Total Connect](https://www.home-assistant.io/integrations/totalconnect/) | Una centrale Resideo/Honeywell su Total Connect 2.0; solo cloud, interrogata ogni 30 secondi |
| [Verisure](https://www.home-assistant.io/integrations/verisure/) | Un account Verisure; interrogazione via cloud; i sensori di porte e finestre diventano binary sensor |

Due cose da leggere sulla pagina dell'integrazione prima di affidarle una
zona:

- **Locale o cloud.** Un'integrazione cloud viene a sapere di una porta alla
  prossima interrogazione, e smette di sentire qualsiasi cosa quando cade
  internet. Un rilevamento che arriva con trenta secondi di ritardo arriva
  con trenta secondi di intruso già dentro casa.
- **Cosa succede quando la connessione cade.** In Foyer un'entità
  `unavailable` o `unknown` è un guasto, mai «tutto tranquillo»: blocca
  l'inserimento a meno che la zona non lo consenta, genera `zone_fault` e
  compare nella pagina *Test e diagnostica*. Di solito una sola integrazione
  porta tutte le zone, quindi una connessione persa le manda in guasto tutte
  insieme, ed è la risposta onesta.

Se la tua centrale non è in quell'elenco, per lei potrebbero esistere
progetti della community. Sono fuori da quello di cui questa pagina può
rispondere.

### Un'uscita programmabile collegata a un ingresso

La maggior parte delle centrali cablate ha uscite programmabili (spesso
chiamate PGM) che commutano quando succede qualcosa: la centrale è inserita,
un allarme sta suonando, una zona è aperta. Collegane una a un ingresso che
Home Assistant sa leggere — un modulo di ingressi a contatto pulito, o un pin
GPIO di una scheda con ESPHome
([GPIO binary sensor](https://esphome.io/components/binary_sensor/gpio/)) —
e l'uscita diventa un `binary_sensor`.

È la strada meno invasiva: la centrale continua a funzionare esattamente come
prima, e Home Assistant si limita a guardare un contatto che la centrale è
stata progettata per pilotare. Quello che non può fare è darti tutte le zone:
un'uscita è un'informazione, e le centrali ne hanno poche. Il manuale di
installazione della centrale dice che tipo di uscita è ciascuna e cosa può
pilotare; collegati seguendo quello, non a intuito.

### Ascoltare il bus cablato

I tastierini di una centrale cablata le parlano attraverso un bus, e gli
stati delle zone passano su quel bus. Una scheda collegata al bus può
leggerli. Si può fare, e comporta tre rischi da soppesare prima di tirare
fuori il cacciavite:

- **Elettrico.** Il bus porta l'alimentazione della centrale. Un collegamento
  sbagliato può danneggiare la centrale, la scheda o entrambe.
- **La centrale potrebbe accorgersene.** Un dispositivo sul bus che la
  centrale non ha registrato può caricare il bus o essere segnalato come
  guasto o manomissione.
- **Il contratto.** Se la centrale è sorvegliata o mantenuta da un'azienda,
  metterci le mani può far decadere il contratto. Leggilo, o chiedi, prima.

### Ricevere la radio dei sensori stessi

Molti sensori wireless economici trasmettono a 433 MHz senza cifratura, e un
ricevitore tuo può sentirli bene quanto la centrale:

- [rtl_433](https://github.com/merbanan/rtl_433) trasforma una radio SDR
  (software-defined radio) economica in un ricevitore per le bande ISM a
  433,92 MHz, 868 MHz e altre, con decodificatori per molti dispositivi, tra
  cui sensori di porte e finestre. Può pubblicare su MQTT quello che
  decodifica, e un
  [MQTT binary sensor](https://www.home-assistant.io/integrations/binary_sensor.mqtt/)
  trasforma un messaggio in un'entità.
- Un **bridge RF** — una scheda con un ricevitore a 433 MHz, per esempio una
  con ESPHome e il suo componente
  [remote_receiver](https://esphome.io/components/remote_receiver/) —
  decodifica i protocolli più semplici a codice fisso ed espone ogni codice
  come binary sensor.

Due dettagli dell'MQTT binary sensor decidono quanto sia onesta l'entità, ed
entrambi sono nella sua documentazione:

- **Un sensore che manda solo «aperto».** Alcuni contatti trasmettono un
  codice quando si aprono e niente quando si chiudono. `off_delay` riporta
  l'entità a `off` dopo un tempo fissato, così la zona vede un impulso. Una
  finestra lasciata aperta, passato quel tempo, risulta chiusa, e
  l'inserimento non si ferma per lei.
- **`expire_after`** rende l'entità `unavailable` quando non arriva niente
  per un tempo fissato. Foyer lo legge come un guasto. Su un sensore che
  trasmette solo quando cambia, manderebbe in guasto una porta che resta
  chiusa; lascialo spento lì, per lo stesso motivo per cui si lascia spento
  il limite di silenzio più sotto.

#### Perché i sistemi cifrati non si possono leggere così

Alcuni antifurti wireless cifrano la loro radio. Ajax, per esempio, dichiara
che la sua radio Jeweller lavora a 868 MHz e che ogni trasmissione è
[cifrata con un algoritmo proprietario basato su AES](https://ajax.systems/jeweller/).
Un ricevitore esterno a un sistema così non ha nessun decodificatore da far
girare: leggere quei sensori vorrebbe dire violare la cifratura di un
antifurto, non ascoltare un sensore. Per sistemi come questi la strada è
l'integrazione nativa, dove esiste, o un'uscita programmabile.

---

## Tre cose che la via radio perde

**I sensori wireless dormono dopo un rilevamento.** Un PIR a batteria di
solito ignora il movimento per un po' dopo averne segnalato uno, per
risparmiare la pila, e il manuale dice per quanto. Una seconda trasmissione
in quel tempo non arriva. [Scegliere i sensori](choosing-sensors.it.md) dice
cosa comporta per *Attivazioni necessarie*.

**La ricezione passiva perde la supervisione.** Una centrale che registra i
suoi sensori di solito si aspetta da ciascuno un segnale periodico di
presenza e tratta come guasto quello che manca. Un ricevitore tuo sente il
sensore solo quando trasmette, e un sensore che trasmette solo quando cambia
non dice niente mentre funziona — e niente quando ha la batteria scarica o
quando qualcuno l'ha staccato dal muro. Da Home Assistant i due casi sono
identici.

**Un sensore a 433 MHz disturbato non diventa `unavailable`.** Il controllo
di Foyer sulle
[interferenze radio](system-health.md#radio-interference) (in inglese)
conta le zone di una stessa radio che diventano non disponibili insieme.
Un'entità MQTT alimentata da un ricevitore mantiene il suo ultimo stato
quando i messaggi smettono di arrivare, quindi disturbare questa banda non
lascia niente da contare a quel controllo.

---

## Da quello che ottieni a una zona di Foyer

Qualunque sia la strada, la zona si crea allo stesso modo, nella pagina
*Zone*. I dettagli sono in [zone](zones.it.md); quello che conta per un
sensore preso in prestito è qui sotto.

| Impostazione | Cosa scegliere |
|---|---|
| *Entità* | Il `binary_sensor` prodotto dalla strada scelta. Una zona può anche osservare un `sensor`, `cover`, `lock`, `switch`, `input_boolean`, `event` e pochi altri |
| *Trigger* | Lo stato che vuol dire aperto o rilevato, verificato sul sensore reale. La zona di una centrale, un ingresso PGM e un codice RF non sono d'accordo su `on` = aperto: un ingresso normalmente chiuso (NC) si legge al contrario di uno normalmente aperto (NA). Apri la porta, guarda lo stato, poi spunta *Ho verificato questi stati sul sensore reale* |
| *Tipo* | In base a dove si trova il sensore: *Ritardata* per la porta da cui entri, *Istantanea* o *Percorso* per il resto |
| *Limite di silenzio (secondi)* | Vedi sotto |
| *Entità della batteria* | Se la strada ne fornisce una: per la diagnostica e per l'[avviso di batteria](simulator.md#batteries) (in inglese) |

### La manomissione come zona a sé

Se la strada espone la manomissione del sensore — un'integrazione della
centrale che la riporta come entità a sé, o un decodificatore che la riporta
nel messaggio — creala come seconda zona di tipo *Manomissione*. Foyer
propone quel tipo per un `binary_sensor` con device class `tamper`. Una zona
di manomissione è sempre attiva, non si può escludere, e va in allarme anche
a impianto disinserito, che è proprio il punto: un sensore aperto a forza è
un allarme chiunque sia in casa.

### Supervisione

Il *Limite di silenzio (secondi)* è spento di default. Quando è impostato,
una zona la cui entità non riporta niente per più del limite è in guasto.
Conta qualsiasi segnalazione, anche una che non cambia nulla: Foyer legge il
`last_reported` di Home Assistant, che la
[documentazione dello state object](https://www.home-assistant.io/docs/configuration/state_object/)
descrive come aggiornato ogni volta che lo stato viene scritto, che sia
cambiato o no. Il limite si può impostare da 60 secondi a 7 giorni.

- **Un contatto a 433 MHz che segnala solo quando cambia: lascialo spento.**
  Una porta che resta chiusa per una settimana non manda niente per una
  settimana, e un limite la manderebbe in guasto.
- **Un sensore che dà segni di vita a intervalli regolari:** imposta il
  limite più lungo di quell'intervallo, sensore per sensore. Con il sensore
  binario MQTT, un segno di vita che ripete lo stesso stato arriva a Home
  Assistant solo con `force_update: true`; senza, l'entità non viene scritta
  e il limite manderebbe in guasto un sensore sano — usa invece
  l'`expire_after` del sensore stesso, più lungo dell'intervallo dei segni di
  vita.
- **Un'integrazione della centrale:** se riscrive uno stato invariato a ogni
  interrogazione dipende dall'integrazione. Imposta un limite generoso e
  guarda per un giorno la colonna *Salute* in *Test e diagnostica*. Se la
  zona mostra *Guasto: muta da troppo tempo* mentre il sensore sta bene,
  l'integrazione non riporta gli stati invariati, e il limite va spento.

Poi controlla il tutto senza far scattare niente: la
[tabella di diagnostica e il simulatore](simulator.md) (in inglese), e un
walk test per trovare il sensore che non ti ha mai visto.

---

## Non ancora trattato qui

- Istruzioni passo passo per una centrale, un ricevitore o un bridge in
  particolare.
- Quali sensori a 433 MHz decodifica rtl_433, e se riportano manomissione,
  batteria o un segnale periodico di presenza.
- Centrali senza integrazione in Home Assistant, e i progetti della community
  per loro.
- Se una data integrazione di centrale riscrive gli stati invariati a ogni
  interrogazione.
- Tenere inseriti allo stesso tempo la centrale esistente e Foyer.
- Schemi di collegamento per uscite e ingressi programmabili.
