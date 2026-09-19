<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.md">English</a> · <strong>Italiano</strong></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>Una vera centrale d'allarme per Home Assistant: aree che si inseriscono da sole, scenari definiti da te, zone che dichiarano cosa le fa scattare, un tastierino alla porta, e un registro che dice la verità.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?sort=semver&label=versione" alt="Ultima versione"></a>
  <img src="https://img.shields.io/badge/stato-beta-yellow" alt="Beta">
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 o successivo">
  <img src="https://img.shields.io/badge/HACS-repository%20personalizzato-41BDF5" alt="Repository personalizzato HACS">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licenza-Apache--2.0-blue" alt="Apache-2.0"></a>
</p>

> ### Stato: beta. Si inserisce dal muro, e il registro dice chi è stato.
>
> Può proteggere una casa, e lo sta facendo. Questa è **la prima beta**: agli
> utenti, ai codici per persona e ai permessi si aggiungono i dispositivi di
> inserimento fisici — tastierini Ring e Zigbee, tag NFC, badge e telecomandi —
> con il contratto dei servizi `foyer.*` e MQTT nelle due direzioni. Un
> tastierino riceve una risposta vera: distingue «codice sbagliato» da
> «bloccato dalla finestra della cucina», invece di fallire in silenzio. Fuori
> restano il simulatore, la prova di percorso e la scalata delle notifiche.

**Provalo se** hai già sensori di porta, finestra o movimento in Home
Assistant, vuoi una centrale con scenari di inserimento veri invece di una
cartella di automazioni, e vuoi inserire e disinserire da un tastierino, un tag
o un badge con un registro che dice chi è stato.

**Non ancora, se** vuoi verificare una configurazione di quaranta zone senza
farla scattare davvero, se ti serve che una notifica senza risposta salga da
push a SMS a telefonata, o se non vuoi far girare su casa tua una beta con
pochi mesi di vita: [Alarmo](https://github.com/nielsfaber/alarmo) ha anni di
installazioni alle spalle, e per un impianto che deve semplicemente funzionare
oggi è la scelta prudente.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-it.png" alt="Il pannello di Foyer: due aree inserite da un solo scenario, una in conto alla rovescia sul ritardo d'ingresso, le zone non pronte e gli ultimi eventi" width="900">
</p>

## Cosa fa

- **Aree che si inseriscono da sole.** Ognuna ha la sua entità
  `alarm_control_panel` e il suo stato; una centrale le aggrega. Il piano terra
  può restare inserito mentre tu sei al primo piano.
- **Scenari di inserimento definiti da te.** *Notte, solo piano terra*. *Solo
  garage*. *Cane in casa*. Quanti ne vuoi, non quattro modalità fisse.
- **Un codice per ogni persona.** Salvato come hash e verificato solo nel
  backend: una card è un tastierino che trasmette un codice, non qualcosa che
  decide. Quali operazioni lo chiedono lo decidi tu, un'area o uno scenario
  possono chiederne di più, e ogni riga del registro dice chi è stato. In più
  un codice di coercizione che disinserisce normalmente facendo scattare un
  allarme silenzioso, e il blocco dopo codici sbagliati ripetuti.
- **Inserimento da un tastierino alla porta.** Tastierini Ring e Zigbee, tag
  NFC, badge RFID e telecomandi. Foyer non parla con i singoli modelli: espone
  un contratto — i servizi `foyer.*` e MQTT nelle due direzioni, con topic
  configurabili — e risponde in modo strutturato, così un tastierino può dare
  due suoni diversi a «codice sbagliato» e a «non adesso, la finestra della
  cucina è aperta». Ogni riga del registro nomina la persona, il canale e il
  dispositivo.
- **Zone che dichiarano da sole cosa le fa scattare.** I contatti normalmente
  chiusi e normalmente aperti si comportano al contrario, quindi Foyer propone
  la condizione a partire dalla classe del dispositivo e poi ti chiede di
  confermarla sul sensore vero. Un errore qui è un allarme che non suona mai, e
  lo scopri durante l'effrazione.
- **Fumo, gas e acqua su un canale separato.** Attivo che la casa sia inserita
  o no, senza toccare mai `alarm_control_panel` — dove *triggered* significa
  «qualcuno è entrato» per HomeKit, Google e Alexa — e il disinserimento non lo
  azzera.
- **Un incidente solo, non un allarme per zona.** Un'effrazione vera fa scattare
  la finestra, poi il corridoio, poi le scale. Diventano un solo incidente con
  una sola presa in carico, invece di tre raffiche di notifiche nel momento
  peggiore possibile.
- **Un registro eventi in un archivio tutto suo**, che la cancellazione dopo
  dieci giorni del recorder non può toccare: cosa è successo, dove, attraverso
  quale canale, se ogni azione ha davvero funzionato, e chi ha cambiato cosa.

<details>
<summary><strong>Il resto di ciò che c'è già</strong></summary>

- **Otto preimpostazioni di zona** su proprietà modificabili: istantanea,
  ritardata, percorso (allarma solo se prima si è aperta una zona ritardata),
  24h, antimanomissione, tecnica, antirapina, e zone chiave che inseriscono o
  disinseriscono invece di allarmare.
- **Ritardi di uscita e di ingresso** — con la possibilità di saltare quello di
  uscita quando sei già fuori, scritta sulla riga di inserimento perché rende
  istantanea ogni zona ritardata — e quattro cose che una zona può fare se è
  aperta mentre inserisci: bloccare, escludersi, aspettare che la chiudi, o
  farsi ignorare.
- **Inserimento forzato** come comando distinto e registrato, ed esclusione
  manuale di una zona — con una durata, dopo la quale rientra e te lo dice,
  perché una zona esclusa e dimenticata è esattamente la finestra da cui
  qualcuno entra.
- **Tempo massimo di sirena con memoria d'allarme**: le sirene si fermano, il
  fatto che sia scattato no.
- **Gruppi di verifica**, N su M entro una finestra, con i membri che mantengono
  la propria risposta: un rivelatore notifica, due fanno suonare la sirena.
- **Profili di risposta**: dieci azioni — notifica, sirena, luce, telecamera,
  scena, interruttore, messaggio vocale, chiamata a qualunque servizio di Home
  Assistant, attesa — ciascuna con al massimo due condizioni, ereditate
  dall'area, poi dallo scenario, poi dal profilo predefinito.
- **Campanello** quando una zona si apre mentre la sua area non la sorveglia, su
  un altoparlante, una sirena o il telefono, con ore di silenzio per singolo
  destinatario.
- **Uno stato che sopravvive a un riavvio**, compresa un'attesa a metà e una
  sirena che sta suonando.
- **Permessi per persona**, applicati su ogni servizio e ogni comando
  WebSocket e non solo nell'interfaccia, con una finestra di validità per i
  codici ospite e un ambito limitato ad aree o scenari scelti.
- **Pannello in italiano e in inglese**, con aiuto contestuale in ogni pagina, e
  una card nelle disposizioni `full`, `compact`, `keypad` e `badge` — l'ultima
  è di solo stato colorato, senza niente da premere, perché un tocco
  involontario su una dashboard non disinserisca una casa.

</details>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-zone-it.png" alt="L'editor della zona chiede in quali stati la zona è in allarme, e pretende che tu li abbia verificati sul sensore vero" width="900">
</p>

## «Me le scrivo da solo, le automazioni»

Puoi farlo, e la prima versione funziona. Quello che costa i sei mesi
successivi è il resto: un ritardo d'ingresso che sopravvive a un riavvio di
Home Assistant a metà; un sensore diventato `unavailable` tre settimane fa e da
allora letto in silenzio come «chiuso»; le tre raffiche di notifiche separate
che produce un'effrazione vera, perché ogni zona ha fatto scattare la sua
automazione; e la sera in cui vuoi rispondere a *la cucina era davvero inserita
alle 02:14?* e il recorder l'ha cancellato dieci giorni fa.

Foyer è quelle parti. Le tue automazioni restano benvenute: emette un evento
per tutto ciò che registra, e può chiamare qualunque servizio tu voglia.

## Tastierini, tag e telecomandi

Foyer non parla con i tastierini: espone un contratto. I modelli cambiano ogni
sei mesi, il contratto no. Tutto ciò che sa chiamare un servizio di Home
Assistant o pubblicare su un broker MQTT può inserire e disinserire questa
casa. E qualunque strada prenda, il registro non scrive «disinserito»: scrive
chi, da quale canale, con quale dispositivo.

- **Un dispositivo va dichiarato prima di poter comandare qualcosa.** Lo
  aggiungi nella pagina *Dispositivi di inserimento*; un dispositivo che
  l'installazione non conosce viene rifiutato qualunque codice porti, e il
  rifiuto finisce nel registro e in una notifica. Non è pignoleria: il blocco
  dopo codici sbagliati conta per canale *e* per dispositivo, quindi chi è
  libero di inventarsi il nome di un dispositivo è qualcuno che non viene
  bloccato mai.
- **Il riscontro è strutturato, non un silenzio.** Ogni servizio che cambia
  stato risponde con l'esito, un motivo stabile — `bad_code`, `zone_open`,
  `locked_out`, `not_permitted`, e gli altri — e il nome delle zone che hanno
  bloccato l'inserimento. È quello che permette a un tastierino di distinguere
  *il codice è sbagliato* da *non adesso*: sono due problemi diversi, e una
  famiglia che sente lo stesso suono per entrambi ridigita un codice che non
  era il problema.
- **MQTT nelle due direzioni**, con topic configurabili, spento finché non lo
  accendi. Il dispositivo pubblica un comando e rilegge lo stato ritenuto
  (*retained*) per LED, segnali acustici e conto alla rovescia. Per
  impostazione predefinita quel messaggio dice il meno possibile: sta su un
  broker spesso condiviso, e quello che contiene viene raccontato a chiunque si
  colleghi dopo — compreso «casa inserita, non c'è nessuno». Tre livelli, e
  alzarlo è una scelta che fai sapendo cosa costa.
- **Tag NFC, badge e telecomandi in modo nativo.** Un'entità `tag.*` o
  `event.*`, la persona a cui appartiene, e cosa fa una scansione: nessuna
  automazione da scrivere, e il registro nomina quella persona — che è tutto il
  motivo per cui un tag vale come canale che identifica. Un tastierino
  condiviso è l'opposto: lì il codice *è* l'identità, e l'esenzione dal codice
  per persona non può valere. Un tag però non ha nessun codice da digitare:
  chi lo trova inserisce e disinserisce come chi lo possiede, quindi va
  trattato come una chiave.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-tag-it.png" alt="L'editor del tag: l'avvertenza che un tag rubato inserisce e disinserisce senza sapere nessun codice, sopra il campo che dice di chi è il tag" width="900">
</p>

- **Tre blueprint pronti**: Ring Alarm Keypad v2 su Z-Wave JS con l'anello LED
  e i conti alla rovescia di uscita e di ingresso, un tastierino Zigbee
  generico via Zigbee2MQTT, e tag e telecomandi per i casi che la
  configurazione nativa non copre apposta. Due avvertenze, perché servono: i
  valori degli indicatori LED del Ring sono mappature della comunità, non
  documentazione del produttore, e i cloni della famiglia Tuya cambiano nomi
  delle azioni e campi da una revisione di firmware all'altra, quindi il tuo
  tastierino va guardato una volta sul suo topic prima di fidartene. Quello che
  i blueprint fanno con Foyer funziona comunque: a sbagliare è solo ciò che il
  tastierino ti mostra.

Ogni blueprint si importa sul tuo Home Assistant con un pulsante, da
[docs/keypads.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/keypads.md),
che contiene anche il contratto completo — servizi, MQTT, cosa vale onestamente
ogni tipo di hardware e come scrivere il proprio adattatore (in inglese, come
tutta la documentazione tecnica).

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-devices-it.png" alt="Dispositivi di inserimento: due tastierini e un tag, ognuno dichiarato prima di poter comandare qualcosa, e il contratto MQTT con il messaggio che pubblicherà davvero" width="900">
</p>

## Cosa manca ancora, e conta

- **Nessun simulatore e nessuna prova di percorso.** Non puoi ancora chiedere
  «cosa succederebbe se la finestra della cucina si aprisse adesso, con questo
  scenario, a quest'ora?» senza aprirla. *Prossima versione.*
- **Nessun inserimento automatico.** Foyer non si inserisce da solo quando la
  casa si svuota. Arriva insieme alla scalata delle notifiche, non prima: il
  conto alla rovescia annullabile che serve a entrambe è lo stesso meccanismo,
  e scriverlo due volte sarebbe spreco. *Dopo.*
- **Nessuna rubrica dei contatti e nessuna scalata delle notifiche.** Vanno
  direttamente a un servizio
  `notify`; non salgono da push a SMS a telefonata finché qualcuno non
  risponde. *Dopo.*
L'ordine è fissato e scritto, con quello che ogni passo deve dimostrare prima
di contare come fatto:
[la tabella di marcia](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md#16-roadmap).

## Foyer e Alarmo

[Alarmo](https://github.com/nielsfaber/alarmo) è l'implementazione di
riferimento in questo campo, ed è fatta bene. Foyer è scritto da zero e non ne
copia il codice. Dove differiscono oggi:

| | Foyer | Alarmo |
|---|---|---|
| **Scenari di inserimento** | Quanti ne vuoi, ciascuno inserisce un insieme di aree scelto | Le quattro modalità fisse di Home Assistant |
| **Aree con stato indipendente** | Sì: un `alarm_control_panel` ciascuna, più una centrale | Una centrale sola, sensori raggruppati per modalità |
| **Fumo, gas, acqua** | Un canale separato, attivo a impianto disinserito, mai `triggered` su un'entità d'allarme | Sensori ordinari |
| **Un incidente per effrazione** | Sì, con una sola presa in carico | Un allarme per sensore |
| **Utenti, codici, permessi** | Sì: un codice a testa, politica per operazione, codice di coercizione, blocco | Sì, codici per utente |
| **Tastierini, MQTT** | Sì: contratto dei servizi e MQTT nelle due direzioni, dispositivi dichiarati, tre blueprint | Sì |
| **Tag NFC e telecomandi** | Nativi, legati a una persona, senza automazioni da scrivere | Tramite automazioni |
| **Maturità** | Beta. Un solo autore, pochi mesi di vita | Anni di utilizzo, moltissime installazioni |
| **Simulatore, prova di percorso** | Previsti, non scritti | — |
| **Interfaccia in italiano** | Completa: pannello, card e testi di aiuto | Solo in inglese |

Il tastierino non è più la riga che decide. Quella che resta è l'ultima: se
vuoi un impianto che sia già stato collaudato da molti altri prima che da te,
usa Alarmo.

## Come puoi verificarlo invece di fidarti

- **La parte che decide è una funzione pura.** «Questa zona si è aperta, questa
  area è inserita, e adesso?» viene deciso da codice che non può raggiungere
  Home Assistant, non ha un orologio suo e non può eseguire nessuna azione; è
  testato per conto proprio, e la CI rifiuta un commit che vi faccia entrare
  Home Assistant. È lo stesso vincolo che renderà veritiera, e non ottimistica,
  la risposta del simulatore.
- **Un buco nella copertura viene scritto.** Se Home Assistant è rimasto giù per
  due ore, il registro lo dice, con la durata. Non lascia mai credere che tu
  fossi protetto quando non lo eri.
- **Ogni azione dice se ha funzionato.** Una sirena che non ha suonato e una
  notifica che non è partita sono righe nel registro, marcate come non
  riuscite. Non silenzio.
- **Il changelog dice cosa è cambiato nel comportamento**, non «varie
  correzioni», perché è quello che serve per decidere se prendere un
  aggiornamento.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-log-it.png" alt="Il registro: inserimento, un allarme, un inserimento rifiutato con la zona che l'ha bloccato, il buco di riavvio, una modifica di configurazione con valore prima e dopo, e una notifica non riuscita" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-users-it.png" alt="Utenti e codici: due persone con i loro permessi, ambito e validità, e la tabella di quali operazioni chiedono un codice" width="900">
</p>

## Modello di sicurezza

I codici di Foyer proteggono da familiari, ospiti,
personale domestico, utenti non amministratori di Home Assistant e da chiunque
trovi un tablet a muro sbloccato. **Non** proteggono da un amministratore di
Home Assistant, che può leggere `.storage`, disattivare l'integrazione o
chiamare qualunque servizio. Per lo stesso motivo il registro eventi è *utile*
come traccia, non *inalterabile*.

**Foyer non è un impianto d'allarme certificato.** La conformità EN 50131 è
dichiaratamente fuori ambito: non soddisfa i requisiti CEI 79-3 / EN 50131 e
non sostituisce un impianto certificato dove una polizza assicurativa o un
capitolato lo richiedano.

**Foyer non è un sistema antincendio.** Un rivelatore di fumo collegato a Home
Assistant non sostituisce rivelatori certificati e interconnessi.

## Cosa ti serve

- Home Assistant 2025.1 o successivo. Sviluppato e testato su 2025.1 e sulla
  versione corrente.
- Almeno un sensore di porta, finestra o movimento già funzionante in Home
  Assistant.
- Un servizio `notify.*` che funzioni. Foyer orchestra le notifiche; non le
  implementa.
- Una sirena, un interruttore o una presa smart, se vuoi far rumore.
  Facoltativo.
- Un tastierino, un tag NFC, un badge o un telecomando, se vuoi inserire dal
  muro invece che dal telefono. Facoltativo, e
  [docs/keypads.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/keypads.md)
  dice cosa vale ogni tipo di hardware prima che tu lo compri.

Nient'altro: nessun account cloud e nessuna connessione verso l'esterno che
parta da Foyer. Un broker MQTT serve solo se colleghi un tastierino per quella
strada, e resta spento finché non lo accendi tu.

## I primi quindici minuti

1. Installa da HACS come repository personalizzato (qui sotto), riavvia e
   aggiungi l'integrazione. Ottieni un'area, uno scenario e una zona.
2. **Verifica la condizione di allarme sul sensore vero.** Apri la porta, passa
   davanti al rivelatore, guarda cambiare lo stato. È l'unico passo che vale la
   pena fare con calma.
3. **Crea il tuo utente con un codice.** Finché nessuno ne ha uno, nessuno
   viene chiesto, e il pannello lo dice dove non puoi non vederlo.
4. Manda la notifica di prova che la procedura guidata ti offre. Se non arriva,
   tutto il resto di Foyer non conta.
5. Inserisci, rientra, lascia scadere il ritardo d'ingresso e lascialo suonare:
   una volta, apposta, mentre sei lì. Poi apri il registro e leggi cosa dice
   degli ultimi due minuti, e a chi li attribuisce.

## Installazione

1. In HACS, apri il menu → *Repository personalizzati*, aggiungi l'URL di questo
   repository con categoria *Integrazione*.
2. Installa *Foyer Home Defender* e riavvia Home Assistant.
3. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Foyer Home
   Defender*. Dài un nome alla prima area e al primo scenario, scegli l'entità
   della prima zona, poi conferma gli stati in cui conta come «in allarme».
4. Nella barra laterale compare una voce **Foyer**, e una breve procedura
   guidata completa la configurazione.

<details>
<summary>HACS mostrava il codice di un commit invece del numero di versione</summary>

Fino alla alpha.13 ogni versione era pubblicata come *pre-release* su GitHub, e
HACS offre solo le release che non sono pre-release: per un repository che non
ne ha nessuna ripiega sul ramo predefinito e mostra il commit. Dalla
0.1.0-beta.1 le versioni sono pubblicate normalmente, quindi HACS le vede, le
mostra per nome e propone da solo gli aggiornamenti. Se a suo tempo avevi
abilitato l'entità *switch* «pre release» che HACS crea per questo repository,
ora puoi disattivarla.

</details>

<details>
<summary>La card non compare nel selettore, o «Custom element doesn't exist»</summary>

Ricarica la pagina una volta con Ctrl+Maiusc+R (Cmd+Maiusc+R su Mac). Home
Assistant scrive il tag script della card dentro la pagina che genera: una
pagina caricata prima che Foyer fosse installato — o prima che fosse aggiornato
— non ce l'ha, e la riconnessione dopo un riavvio non ne scarica una nuova.
Nell'app per smartphone azzera la cache dell'interfaccia dalle sue
impostazioni, oppure chiudi e riapri l'app. Per verificare che il file ci sia,
apri `https://<il-tuo-home-assistant>/foyer_static/foyer-card.js`: deve
mostrare del JavaScript.

</details>

### La card

Scegli *Foyer Home Defender* nel selettore delle card della dashboard, oppure
scrivila a mano:

```yaml
type: custom:foyer-card
entity: alarm_control_panel.foyer_master   # oppure alarm_control_panel.foyer_<area>
layout: full                               # full, compact, keypad o badge
```

Non serve aggiungere alcuna risorsa alla dashboard. La card non decide nulla da
sé: manda un comando e mostra la risposta, compreso il nome della zona che l'ha
rifiutato e la via per superarla.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-it.png" alt="La card nelle disposizioni completa e compatta" width="620">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-keypad-it.png" alt="La disposizione a tastierino per un tablet a muro, e lo stesso tastierino aperto dentro la disposizione completa" width="620">
</p>

## Domande che vengono fatte

<details>
<summary>Posso usare Foyer e Alarmo insieme?</summary>

Si possono installare entrambi, ma non puntarli sugli stessi sensori: avresti
due sistemi che decidono cosa significa una finestra aperta, e che si
inseriscono e disinseriscono l'uno all'insaputa dell'altro. Prova Foyer su
qualche zona, o su un'installazione di prova, e spostaci il resto quando se lo
sarà guadagnato.

</details>

<details>
<summary>Chi può disinserire?</summary>

Chi ha un codice, e solo per ciò che i suoi permessi consentono. Finché non
crei il primo utente non viene chiesto nulla a nessuno e chiunque abbia accesso
a Home Assistant può disinserire — il pannello lo dice apertamente finché dura.
Una persona può essere esentata dal digitare il codice sui canali che già sanno
chi è, come l'interfaccia di Home Assistant con il suo account; su un tastierino
condiviso il codice *è* l'identità, quindi lì l'esenzione non vale.

</details>

<details>
<summary>Funziona senza internet?</summary>

Sì. Foyer non apre nessuna connessione verso l'esterno, e non richiede né un
account cloud né un broker. Se sopravvivano le *notifiche* a una linea tagliata
è un'altra domanda, e la risposta onesta è che una notifica push no — ed è per
questo che la scalata su più canali è nella tabella di marcia, e per cui un
canale locale vale la pena di averlo.

</details>

<details>
<summary>La mia configurazione sopravvive a un aggiornamento?</summary>

Sì. La configurazione salvata è versionata e migrata un passo alla volta, e
ogni voce del changelog dice se lo schema si è mosso. Tornare *indietro*
attraverso un cambio di schema maggiore viene rifiutato apposta, invece di
essere letto a metà: una versione più vecchia che ignorasse in silenzio ciò che
non capisce potrebbe smettere in silenzio di proteggere qualcosa.

</details>

<details>
<summary>Cosa succede se rimuovo l'integrazione?</summary>

Se ne vanno la sua configurazione, lo stato dell'allarme salvato e le sue
entità. L'archivio del registro eventi resta apposta sul disco: se cancellare
trenta giorni di storia è una domanda che va fatta a te, e farla per bene è
nella tabella di marcia.

</details>

<details>
<summary>È disponibile nella mia lingua?</summary>

Oggi italiano e inglese, pannello, card e aiuto contestuale compresi.
Aggiungere una lingua non tocca il codice: si copiano due file JSON, si traduce
e si apre una pull request. La CI fallisce se gli insiemi di chiavi dei due
file non coincidono, quindi un pannello tradotto a metà non può essere
pubblicato.

</details>

## Se qualcosa va storto

Apri una [issue](https://github.com/foyer-labs/Foyer-Home-Defender/issues). Di'
quale versione di Foyer e di Home Assistant, cosa ti aspettavi, e cosa mostra
la pagina del registro: la riga di solito contiene già la risposta, quindi una
schermata vale più di una descrizione. In italiano o in inglese, come preferisci.

Per sapere quando esce una versione, metti il repository fra quelli che
segui: le versioni vengono annunciate lì, e il
[changelog](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CHANGELOG.md)
dice ogni volta cosa è cambiato nel comportamento.

## Sviluppo

```
custom_components/foyer/   l'integrazione (HACS installa questa cartella così com'è)
  core/                    motore decisionale puro: mai un import di Home Assistant
  runtime/ entity/ api/    gli strati che parlano con Home Assistant
  security/                codici bcrypt, e da chi arriva una richiesta
  store/                   persistenza in .storage, migrazioni di schema, il registro
  translations/            en.json, it.json (Home Assistant) e panel/ (interfaccia, aiuto)
  frontend/                bundle compilati di pannello e card, versionati
frontend/                  sorgenti TypeScript + Lit, compilati con Vite
blueprints/                adattatori per tastierini e tag (si copiano a mano)
docs/                      la specifica, il contratto dei tastierini, gli screenshot
tests/core, tests/repo     girano senza Home Assistant installato
tests/ha                   girano dentro l'ambiente di test di Home Assistant
```

```bash
pip install pytest ruff bcrypt
pytest                       # suite pura: motore, controllo di purezza, traduzioni
ruff check . && ruff format --check .
cd frontend && npm ci && npm run build   # ricompila custom_components/foyer/frontend
```

I test di integrazione richiedono Linux o WSL:

```bash
pip install pytest-homeassistant-custom-component
pytest -p pytest_homeassistant_custom_component -o asyncio_mode=auto tests/ha
```

`core/` non deve mai importare `homeassistant`. La CI lo verifica; se quel
controllo fallisce, si corregge il codice, mai il test.

Il progetto completo, comprese le ragioni dietro le decisioni che sembrano
arbitrarie finché non si sa perché, è in
[docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md)
(in inglese, come tutto il codice e la documentazione tecnica).

## Licenza

Apache-2.0. Vedi [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) e [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
