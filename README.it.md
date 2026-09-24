<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.md">English</a> · <strong>Italiano</strong></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>Una centrale d'allarme per i sensori che hai già. Aree con uno stato ciascuna, scenari di inserimento definiti da te, zone che dichiarano cosa le fa scattare — e un simulatore che ti dice cosa succederebbe, prima che tu lo scopra nel modo peggiore.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?sort=semver&include_prereleases&label=versione" alt="Ultima versione"></a>
  <img src="https://img.shields.io/badge/stato-beta-yellow" alt="Beta">
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 o successivo">
  <img src="https://img.shields.io/badge/HACS-repository%20personalizzato-41BDF5" alt="Repository personalizzato HACS">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licenza-Apache--2.0-blue" alt="Apache-2.0"></a>
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml"><img src="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
</p>

> ### Stato: beta. Funziona, protegge la casa di chi lo scrive, e puoi chiedergli cosa farebbe prima di fidartene.
>
> A quella domanda rispondono tre strumenti. Il **simulatore** prova una
> decisione senza che succeda niente. Il **walk test** inserisce l'impianto
> per davvero, trattiene ogni risposta e ti dice quali zone non ti hanno mai
> visto passare. La **prova delle azioni** fa suonare la sirena sul serio,
> così un canale d'emergenza configurato male lo scopri un martedì pomeriggio
> e non alle tre di notte. (Un walk test non silenzia mai un rilevatore di
> fumo: le zone 24h, manomissione, tecniche e panico restano completamente
> attive.)
>
> Il resto — utenti e codici, tastierini e tag, l'escalation finché qualcuno non
> risponde, e la casa che si inserisce da sola quando esce l'ultima persona —
> è nel
> [changelog](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CHANGELOG.md).

**Provalo se** hai già sensori di porta, finestra o movimento in Home
Assistant, vuoi una centrale con scenari di inserimento veri invece di una
cartella di automazioni, preferisci controllare una configurazione invece di
sperare che sia giusta, e vuoi inserire e disinserire da un tastierino, un tag
o un badge con un registro che dice chi è stato, e sei disposto a far girare
una beta su una casa che ha anche altre serrature.

**Non ancora, se** non vuoi far girare su casa tua una beta con
pochi mesi di vita: [Alarmo](https://github.com/nielsfaber/alarmo) ha anni di
installazioni alle spalle, e per un impianto che deve semplicemente funzionare
oggi è la scelta prudente.

**Cosa ti serve:** Home Assistant 2025.1, un sensore che già funziona e un
servizio `notify.*`. Nessun account cloud, nessun broker se non lo chiedi tu,
e nessuna connessione verso l'esterno che parta da Foyer.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-it.png" alt="Il pannello di Foyer: due aree inserite da un solo scenario, una in conto alla rovescia sul ritardo d'ingresso, le zone non pronte e gli ultimi eventi" width="900">
</p>

## Da dove nasce

Quasi tutti quelli che arrivano qui hanno già l'hardware e non lo sanno.

Hai messo un contatto sulla porta d'ingresso perché volevi che si accendesse
la luce del corridoio. Ne hai messo uno sulla finestra della camera perché
volevi che qualcuno ti dicesse che l'avevi lasciata aperta prima che
piovesse. Hai messo un sensore di movimento in corridoio per la luce di
notte, e un altro in cucina perché la cappa dovrebbe accorgersi che stai
cucinando. Due inverni dopo la casa è piena esattamente dei sensori di cui è
fatto un antifurto, e li stai usando per accendere lampadine.

Poi chiedi quanto costa un antifurto. Viene qualcuno, ti fa un preventivo che
ti fa sbattere le palpebre, e propone di forare il muro per un contatto sulla
porta d'ingresso e un sensore in corridoio — cioè per i due sensori già
avvitati sullo stipite di casa tua. E poi c'è l'abbonamento mensile, perché
il tastierino deve telefonare a qualcuno.

Quindi quello che manca non è l'hardware. È la disciplina intorno:
aree che si inseriscono separatamente invece di un unico interruttore
tutto-o-niente, un tempo di ingresso che sopravvive a un riavvio, una zona
che dichiara cosa vuol dire "aperta" per lei invece di dare per scontato
`on`, un incidente solo invece di nove notifiche insieme, un registro ancora
leggibile fra tre settimane, e un modo di verificare tutto senza far partire
niente alle due di notte.

Questo è quello che trovi qui. Costa una serata di configurazione, e se i
sensori li hai già, la parte cara l'hai già pagata.

**Cosa onestamente non è:** un sistema certificato, né sorvegliato, né
hardware professionale. Non guarda nessuno, non è di nessun grado, e la
rilevazione vale quanto valgono sensori comprati per un interruttore della
luce. Quello che può essere — con un UPS sul router, un canale di notifica
che sopravvive al taglio della fibra, e un secondo sensore dove uno solo
sarebbe solo — è un ottimo risultato per quello che costa, su una casa che è
già intelligente.

## Cosa fa

- **Aree con stato indipendente.** Ognuna ha la sua entità
  `alarm_control_panel` e il suo stato; un pannello *Tutta la casa* le
  aggrega. Il piano terra può restare inserito mentre tu sei al primo piano.
- **Scenari di inserimento definiti da te.** La parzializzazione che vuoi tu:
  *Notte, solo piano terra*. *Solo garage*. *Cane in casa*. Quanti ne vuoi, non
  quattro modalità fisse. La Panoramica ne inserisce uno con un pulsante
  suo — *Inserisci «Notte»* — e accanto dice se la casa è pronta o quali zone
  non lo sono; inserire una sola area fuori da ogni scenario è l'eccezione,
  dietro *Solo un'area…*.
- **Un codice per ogni persona.** Salvato come hash e verificato solo nel
  backend: una card è un tastierino che trasmette un codice, non qualcosa che
  decide. Quali operazioni lo chiedono lo decidi tu, un'area o uno scenario
  possono chiederne di più, e ogni riga del registro dice chi è stato. Quando
  il pannello lo chiede, dice a cosa serve — *Codice per disinserire Piano
  terra* — e quale area o scenario lo sta chiedendo; lo dimentica dopo due
  minuti senza usarlo, dopo ogni inserimento o disinserimento, e quando il
  pannello si chiude. In più un codice di coercizione, che funziona
  esattamente come il codice del suo titolare, per qualunque cosa venga usato,
  e ogni volta fa scattare un allarme silenzioso; e il blocco dopo codici
  sbagliati ripetuti.
- **Un tastierino accanto alla porta, un tag in tasca.** Tastierini Ring e Zigbee, tag
  NFC, badge RFID e telecomandi. Foyer non parla con i singoli modelli: espone
  un contratto — i servizi `foyer.*`, MQTT nelle due direzioni con topic
  configurabili, e un endpoint HTTP di Foyer con un token per ogni
  dispositivo — e risponde in modo strutturato, così un tastierino può emettere
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
  una sola presa d'atto, invece di tre raffiche di notifiche nel momento
  peggiore possibile.
- **Una notifica che continua a cercare qualcuno.** Una rubrica di persone,
  non di servizi, ognuna con i suoi canali in ordine di priorità, e passi ai
  tempi che scegli: push adesso, SMS fra un minuto, una seconda persona due
  minuti dopo. Si ferma nell'istante in cui qualcuno prende atto — dal
  pulsante nella notifica push, disinserendo, da un tasto premuto durante la
  telefonata o da `foyer.acknowledge` — e ogni presa d'atto registra chi e da
  quale canale. Se non prende atto nessuno, l'ultimo passo lo dice come evento
  a sé. Le ore di silenzio lasciano passare un'effrazione e trattengono il
  resto.
- **Un registro eventi in un archivio tutto suo**, che la cancellazione dopo
  dieci giorni del recorder non può toccare: cosa è successo, dove, attraverso
  quale canale, se ogni azione ha davvero funzionato, e chi ha cambiato cosa.
- **Il registro parla di persone, e sa lasciarne andare una.** Consegna a
  qualcuno ogni riga che lo nomina, come file. Togli una persona dal registro
  senza perdere un solo evento — il racconto di *cosa è successo* sopravvive
  alla rimozione di *chi*. Accorcia la conservazione sulle categorie che
  nominano persone, oppure lascia che i nomi invecchino da soli, dopo che ti è
  stato detto chiaramente quanto costa.
- **Un simulatore che risponde a «cosa succederebbe se…» senza che succeda
  niente.** Scegli uno scenario e un'ora, forza l'apertura di una finestra un
  minuto dopo, e leggi tutta la decisione, comprese le azioni che *non*
  sarebbero partite e perché. [Qui sotto](#chiedere-cosa-succederebbe-senza-che-succeda-niente),
  con un esempio.
- **Un walk test che ti dice quali zone non ti hanno mai visto.**
  L'impianto è inserito per davvero e ogni risposta è trattenuta — tranne
  quelle delle zone 24h, manomissione, tecniche e panico, che restano
  completamente attive, perché un walk test non deve mai silenziare un
  rilevatore di fumo. Si chiude da solo, e finché è attivo lo dice su ogni
  schermo.
  [Qui sotto](#camminare-per-casa-e-premere-il-pulsante).
- **La casa può inserirsi da sola, e te lo dice prima.** Regole sulla
  presenza, su un orario o sullo stato di un'entità, con condizioni di
  sicurezza che le fermano — solo se è tutto disinserito, solo se tutte le
  zone sono pronte, solo se in casa non si muove niente da N minuti. Ognuna si
  annuncia prima con una push che porta un pulsante **Annulla**, e una
  sospensione che si chiama «Tecnico della caldaia, 09:00–13:00» tiene la casa
  aperta la mattina che aspetti qualcuno — così fra sei mesi il registro
  dice ancora perché. [Più sotto](#lasciare-che-la-casa-si-inserisca-da-sola).
- **Un pulsante di prova accanto a ogni azione e a ogni canale di un
  contatto, e si esegue davvero.** Fa
  suonare la sirena per tre secondi, manda la notifica sul serio. L'errore che
  evita è scoprire durante l'emergenza che il canale d'emergenza era
  configurato male. Con conferma, con permesso, e a registro come prova.
- **Foyer controlla che Foyer funzioni ancora.** La rete elettrica, ogni
  canale di notifica, un watchdog esterno che dà l'allarme da fuori casa
  quando i ping si fermano, e molte zone di una stessa radio che ammutoliscono
  insieme. Un allarme che non sa dirti che ha smesso di funzionare ha smesso
  di funzionare.
- **Test e diagnostica: una tabella in tempo reale di ogni zona**, con
  l'unica colonna che le pagine di configurazione non possono mostrarti — se
  Foyer considererebbe quel sensore *scattato adesso*, letto attraverso il
  trigger di quella zona. In più: se bloccherebbe l'inserimento e per quale dei
  due motivi, lo stato della batteria, il segnale radio, e quando ha rilevato
  qualcosa l'ultima volta.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-contacts-it.png" alt="La pagina Contatti: tre persone con i canali in ordine di priorità, i quattro passi di un'escalation con i tempi fra l'uno e l'altro, e i quattro modi per fermarla" width="900">
</p>

<details>
<summary><strong>Il resto di ciò che c'è già</strong></summary>

- **Otto preimpostazioni di zona** su proprietà modificabili: istantanea,
  ritardata, percorso (allarma solo se prima si è aperta una zona
  ritardata), 24h, manomissione, tecnica, panico, e zone chiave che
  inseriscono o disinseriscono invece di allarmare.
- **Ritardi di uscita e di ingresso** — con la possibilità di saltare quello di
  uscita quando sei già fuori, scritta sulla riga di inserimento perché rende
  istantanea ogni zona ritardata — e quattro cose che una zona può fare se è
  aperta mentre inserisci: bloccare, escludersi, aspettare che la chiudi, o
  farsi ignorare.
- **Inserimento forzato** come comando distinto e registrato, ed esclusione
  manuale di una zona — con una durata, dopo la quale viene inclusa di nuovo e
  te lo dice, perché una zona esclusa e dimenticata è esattamente la finestra
  da cui qualcuno entra.
- **Tempo massimo di sirena con memoria d'allarme**: la sirena si ferma, il
  fatto che sia scattato no.
- **Gruppi di verifica**, N su M entro una finestra, con i membri che mantengono
  la propria risposta: un rilevatore notifica, due fanno suonare la sirena.
- **Profili di risposta**: dieci azioni — notifica, sirena, luce, telecamera,
  scena, interruttore, messaggio vocale, chiamata a qualunque servizio di Home
  Assistant, attesa — ciascuna con al massimo due condizioni, ereditate
  dall'area, poi dallo scenario, poi dal profilo predefinito. Dopo un allarme
  ci sono due momenti: *Fine dell'allarme*, quando scade il tempo massimo di
  sirena o l'area viene disinserita durante l'allarme, e *Memoria d'allarme
  azzerata*, quando un disinserimento o il successivo inserimento di
  quell'area azzera la memoria, anche ore dopo — quello giusto per spegnere
  la lampada che dice che è successo qualcosa mentre eri fuori. Inserire di
  nuovo non è prendere atto dell'allarme: un incidente di cui nessuno ha
  preso atto resta aperto, e la sua escalation continua, finché qualcuno non
  ne prende atto o non disinserisce.
- **L'immagine insieme all'allarme**, e sei tu a dire per quale app. All'app
  Companion arriva un collegamento alla telecamera dal vivo attraverso il proxy
  autenticato di Home Assistant, senza scrivere nessun file; a Telegram arriva
  uno scatto, perché è il suo server a scaricarlo da fuori casa e quel
  collegamento non può seguirlo. Foyer te lo chiede invece di indovinarlo dal
  nome del servizio, perché ogni destinazione scarta in silenzio le chiavi che
  non conosce — e «ho allegato una telecamera e non è arrivato niente» è il
  modo in cui lo scopri, mesi dopo.
- **Campanello** quando una zona si apre mentre la sua area non la sorveglia, su
  un altoparlante, una sirena o il telefono, con ore di silenzio per singolo
  destinatario.
- **Uno stato che sopravvive a un riavvio**, compresa un'attesa a metà e una
  sirena che sta suonando.
- **Permessi per persona**, applicati su ogni servizio e ogni comando
  WebSocket e non solo nell'interfaccia, con una finestra di validità per i
  codici ospite e un ambito limitato ad aree o scenari scelti. Un'area o uno
  scenario dicono se chiedono un codice per inserire e per disinserire —
  *Codice richiesto*, *Senza codice* o *Come la politica globale*, e se i due
  non concordano vince quello che chiede il codice — e uno scenario può essere
  limitato alle persone spuntate in *Chi può usarlo*. Tutto ciò che cambia le
  persone — una persona, un tag, la persona per cui agisce una chiave, l'elenco
  delle persone di uno scenario — richiede *Gestire utenti e codici* oltre a
  *Modificare la configurazione*, da qualunque pagina e nel ripristino di un
  backup. L'ambito restringe ciò che agisce su un'area — inserire,
  disinserire, escludere una zona; modificare la configurazione, leggere il
  registro e provare un'azione non sono mai ristretti per aree. L'unica
  operazione su un'area che non restringe è il *Walk test*: copre tutta la
  casa, e finché il test è attivo nessuna area risponde a una rilevazione
  ordinaria, quindi può tenere zitta una casa inserita senza *Disinserire*
  ([più sotto](#a-cosa-servono-i-codici-e-a-cosa-no)).
- **Una casa inserita mantiene la risposta con cui è stata inserita.** Finché
  un'area è inserita non si possono cambiare la durata delle sirene, i
  ritardi, i profili con cui potrebbe rispondere e i contatti che questi
  avvisano, la politica dei codici e il blocco, se una regola possa
  disinserire, le radio e le loro soglie: prima si disinserisce. Chi può
  comandare la casa resta invece modificabile: il codice di un ospite, la
  regola di un telefono perso o il token di un tastierino si tolgono da
  ovunque, qualunque cosa sia inserita — tranne l'ultimo codice che qualcuno
  può usare, che non si può nemmeno far scadere prima, perché senza nessuno
  la politica dei codici si spegne da sola.
- **Pannello in italiano e in inglese**, con aiuto contestuale in ogni pagina,
  un Elimina che chiede prima conferma, lì accanto al pulsante, e una card
  nelle disposizioni `full`, `compact`, `keypad` e `badge` — l'ultima è di
  solo stato colorato, senza niente da premere, perché un tocco
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

## Chiedere cosa succederebbe, senza che succeda niente

Il simulatore usa lo stesso motore decisionale dell'allarme vero, con un mondo
e un orologio inventati, e poi non consegna mai il risultato a chi farebbe
suonare le sirene. Non è una promessa, è una garanzia strutturale: il motore è
una funzione pura, quindi «eseguilo e butta via la risposta» è tutta
l'implementazione — e un test verifica che il simulatore e l'allarme in
funzione arrivino alla stessa identica decisione dagli stessi identici dati.

Scegli uno scenario e un'ora, forza lo stato delle zone a intervalli decisi da
te, e leggi cosa succederebbe — comprese le azioni che *non* sarebbero partite,
ognuna con il suo motivo:

```
21:32:00  Area «Piano terra»: Disinserito → In inserimento · ritardo d'uscita fino alle 21:32:30
21:32:30  Area «Piano terra»: In inserimento → Inserito
            Profilo «Base», ereditato dal profilo predefinito
            ✓ Notifica di Home Assistant
21:33:30  Zona «PIR soggiorno» → on
          Area «Piano terra»: Inserito → In allarme · sirena fino alle 21:36:30
          Gruppo «Soggiorno»: 1 su 2 entro 60 s → non soddisfatto
          Incidente aperto 20260914-213330-1
            Profilo «Silenzioso», ereditato dalla zona
            ✓ Avvisa Luca
          ⏱ taglio della sirena alle 21:36:30
21:34:00  Zona «PIR ingresso» → on
          Gruppo «Soggiorno»: 2 su 2 entro 60 s → SODDISFATTO
          Zona aggiunta all'incidente 20260914-213330-1
            Profilo «Completo», ereditato dal gruppo
            ✓ Sirena interna
            ✗ Luci ingresso — condizione non soddisfatta: orario 22:00-07:00
            ✗ Luci scale — trattenuta da un ritardo precedente nella sequenza
          ⏱ il resto di questa sequenza alle 21:34:30
21:36:30  Area «Piano terra»: In allarme → Inserito
          Fine della sirena
```

Un rilevatore da solo è *Silenzioso*; due entro la finestra sono *Completo*.
Ecco com'è fatta una risposta graduata, vista prima che te la mostri un ladro.

Due limiti, perché sono la differenza fra uno strumento utile e l'illusione di
averne uno. Prova la **decisione**, non il trasporto: ti dice che una notifica
partirebbe verso un certo destinatario, non che quel destinatario funzioni. E
non sostituisce un walk test — forzare lo stato di una zona dimostra
cosa ne fa il motore, e non dimostra niente su dove sia puntato il rilevatore
del corridoio. Di quello si occupa la sezione qui sotto.

Come si legge una traccia, e cosa vale la pena provare prima di fidarsi di una
configurazione: [docs/simulator.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/simulator.md) (in inglese).

## Lasciare che la casa si inserisca da sola

Escono tutti i telefoni. Cinque minuti dopo vengono controllate le condizioni
— niente di aperto, niente che si muove dentro, casa disinserita — e su quei
telefoni arriva una push: *Non sembra esserci nessuno, quindi «Casa vuota»
inserirà Fuori casa. Annulla per fermarla.* Due minuti. Se premi Annulla non
succede; se non premi niente succede, e il registro dice quale regola ha
inserito la casa.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-rules-it.png" alt="La pagina Regole automatiche: una regola che inserisce quando tutti sono via da dieci minuti, con le sue condizioni di sicurezza e i due minuti di grazia, una finestra per il tecnico della caldaia, e il riquadro del disarmo automatico che nomina l'attacco da cui protegge e l'area perimetrale che nessuna regola può disinserire" width="900">
</p>

Le condizioni di sicurezza sono la parte che vale la pena configurare. Una
regola fermata da una di loro finisce nel registro sotto *Sistema*, perché
*«perché non si è inserita ieri sera?»* è una domanda che la gente fa, e il
silenzio è la peggior risposta possibile. E la mattina che aspetti qualcuno, una finestra
con un nome — «Tecnico della caldaia, 09:00–13:00» — tiene ferme le regole e,
se vuoi, mette il solo perimetro al posto di quello che avrebbero inserito.

Spegni la condizione che ogni zona sia pronta, e una finestra aperta non ferma
più la regola in silenzio: il conto alla rovescia la nomina e dice che la casa
non può inserirsi finché non viene chiusa, e la regola si inserisce da sola
appena lo è. I contatti della regola vengono avvisati di com'è andata — non
inserita e perché, poi inserimento in corso — anche nelle loro ore di
silenzio. In alternativa, con l'opzione **Inserisci comunque, escludendo le
zone aperte** la regola si inserisce lo stesso: spenta di default, esclude
solo le zone aperte che si possono escludere, mai una zona guasta, e il
registro lo segna come inserimento forzato.

**Inserire e disinserire non sono trattati come ugualmente sicuri.** Il
disinserimento automatico esiste, è spento finché non lo accendi, e non può
mai agire su un'area che hai segnato come perimetrale. In Home Assistant la presenza è
dedotta da un telefono: un telefono rubato, una deriva GPS di 200 metri o un
MAC clonato sulla tua rete sembrano esattamente te che torni a casa. Chi entra
con un telefono rubato trova comunque inserita ogni porta e finestra esterna —
imposto nel motore, con un test che lo verifica, non un default su una
schermata. [docs/automation-rules.md](docs/automation-rules.md) dice il resto
senza addolcirlo.

## Camminare per casa, e premere il pulsante

Il simulatore risponde a *cosa farebbe l'allarme*. Due cose non può dirtele:
se quel rilevatore è puntato davvero sul corridoio, e se la tua notifica
arriva davvero. Per quelle servono la casa e il canale in persona.

**Il walk test** inserisce per davvero ogni area disinserita che può esserlo
e non conserva una memoria d'allarme, e legge ogni sensore per davvero — e
trattiene tutta la risposta. Cammina di stanza in stanza e la pagina si
riempie in diretta. Quel che conta non sono le zone che ti hanno rilevato, ma
quelle che non l'hanno mai fatto, che stanno in cima all'elenco:
una porta che nessuno ha aperto e un rilevatore puntato sulla parete sbagliata
lì sono identici — mentre un sensore che ha semplicemente smesso di farsi
sentire viene segnato come guasto lì accanto, ed è l'unico dei tre casi che
l'elenco sa distinguere da solo.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-walktest-it.png" alt="Un walk test in corso: un banner dice che ogni risposta è trattenuta e che cosa resta attivo, e in cima alla tabella c'è la zona che non ha mai reagito, mentre le quattro che hanno reagito portano l'ora in cui ti hanno visto per la prima volta" width="900">
</p>

Tre cose non sono facoltative, perché finché il walk test è attivo
un'intrusione vera non produce nulla:

- **Le zone 24h, manomissione, tecniche e panico restano completamente
  attive.** Un walk test non silenzia mai un rilevatore di fumo.
- **Si chiude da solo.** Quindici minuti senza rilevazioni per impostazione
  predefinita, con ogni rilevazione che li rimanda — così una casa grande si
  cammina in un giro solo — e un tetto assoluto che lo chiude comunque. Non
  c'è un'impostazione che disattivi l'uscita automatica.
- **Lo dice ovunque.** Un banner nel pannello e su ogni layout della card,
  `badge` compreso, che non ha nulla da premere e lo mostra lo stesso; più una
  notifica all'inizio e alla fine, ed entrambe nel registro con la persona che
  l'ha avviata.

Una rilevazione durante il walk test viene registrata e non muove nient'altro:
niente allarme, niente incidente, nessuna memoria d'allarme, e nessuno dice a
HomeKit o ad Alexa che qualcuno è entrato. Uscendo vengono disinserite le
aree che il walk test aveva inserito — tranne una in allarme, o una a cui una
zona 24h o di manomissione ha lasciato la memoria d'allarme durante il test,
che solo un disinserimento fatto da una persona chiude — e ogni altra area
resta come era. Un'area che conserva già una memoria d'allarme quando il test
parte non viene inserita: il test inserisce per una
prova, non per una sorveglianza, quindi la lascia disinserita con la sua
memoria, e le sue zone vengono registrate lo stesso quando ti vedono.

Copre tutta la casa, chiunque lo avvii: viene inserita ogni area disinserita
che può esserlo, anche fuori dalle aree di chi lo avvia ma non una che
conserva ancora una memoria d'allarme, e un'area che qualcun altro aveva
inserito smette anch'essa di rispondere fino alla fine del test. Per questo *Walk
test* è un permesso da dare come si dà *Disinserire* —
[a cosa servono i codici](#a-cosa-servono-i-codici-e-a-cosa-no) spiega
perché, e la pagina *Utenti* lo dice quando lo spunti.

**La prova delle azioni** è un pulsante accanto a ogni azione, e la esegue
davvero: la sirena suona, la notifica parte. È il punto: l'errore che evita è scoprire durante l'emergenza che il
canale d'emergenza era configurato male. Chiede conferma, richiede il permesso
`test_actions` e un codice, fa suonare la sirena per tre secondi qualunque
sia la durata configurata, e lascia nel registro una riga marcata come prova —
mai come l'allarme che imita.

## Quando è l'allarme stesso a smettere di funzionare

Un allarme che non sa dirti che ha smesso di funzionare ha smesso di
funzionare. Quattro guasti sconfiggono in silenzio un allarme fai-da-te, e in
tutti e quattro la casa sembra tranquillissima: manca la corrente, si rompe il
canale di notifica, la radio ammutolisce, oppure Home Assistant muore.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-health-it.png" alt="La pagina Stato del sistema: rete elettrica presente, il watchdog che riporta ogni quindici minuti con payload vuoto, e ogni canale di notifica con il suo ultimo invio riuscito, o il fatto che non è mai stato usato" width="900">
</p>

- **Rete elettrica.** Indichi il sensore dell'UPS e quale suo stato significa
  assenza: un UPS dice `on` quando la corrente manca, un sensore di potenza
  dice `off`, quindi Foyer lo chiede invece di indovinarlo. Un black-out viene
  annunciato subito e non è mai una notte tranquilla.
- **Canali di notifica**, controllati ogni quarto d'ora e dopo ogni invio
  reale. Un servizio `notify` che qualcuno ha rimosso in un aggiornamento
  viene trovato prima della notte in cui serve, e l'avviso esce **su un canale
  che funziona ancora**: un avviso mandato sul canale morto non arriverebbe a
  nessuno.
- **Un watchdog esterno.** Foyer manda ping a un URL che scegli tu; se Home
  Assistant muore i ping si fermano e quel servizio dà l'allarme, che è
  l'unica risposta al fatto che un sistema morto non può annunciare la propria
  morte. Il battito **non porta niente**: un ping che dicesse «inserito, non
  c'è nessuno» racconterebbe a terzi esattamente quando venire. E l'URL è
  trattato come una credenziale — chi lo possiede può tenere il controllo
  verde per sempre — quindi, una volta salvato, non viene più mostrato: se ne
  scrive uno nuovo sopra.
- **Interferenza radio**, *sospetta* e mai dichiarata. Molte zone di una stessa
  radio che ammutoliscono in pochi secondi sono la sua firma — e anche quella
  di un crash del coordinatore, di un aggiornamento firmware, di un cambio di
  canale e di un black-out in una stanza piena di router alimentati a rete.
  Foyer le conta per radio, verifica che il coordinatore risponda ancora,
  aspetta un minuto per vedere se è ancora vero, e poi **non agisce attraverso
  quella radio**: annunciare un blackout Zigbee con una sirena Zigbee non è
  una notifica.

Niente di tutto questo è un'intrusione, quindi niente tocca mai un
`alarm_control_panel` — con un'eccezione: a casa inserita, un'interferenza
confermata apre un incidente, come il jamming in una centrale professionale. I
problemi persistenti diventano anche problemi di Home Assistant, in
Impostazioni, dove qualcuno li incontra senza aprire il pannello di Foyer.

[docs/system-health.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/system-health.md)
ha il dettaglio e chiama l'euristica con il suo nome;
[docs/resilience.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/resilience.md)
è quello più breve e più scomodo: cosa sopravvive quando qualcuno stacca la
corrente, perché un UPS sul router è la cosa che rende di più fra quelle che
puoi comprare, e perché un canale GSM locale è l'unico che sopravvive al
taglio della fibra.

## Il registro parla di persone

Il registro racconta chi era in casa, quando è arrivato e quando è uscito. In
una famiglia non sono affari di nessun altro — l'esenzione domestica del GDPR
lo copre e non c'è niente da fare. **Smette di coprirlo nel momento in cui il
registro scrive qualcun altro**: la signora delle pulizie le cui entrate
restano per un mese, il tecnico della caldaia, la babysitter. E non si applica
affatto al B&B, alla casa vacanze o al piccolo ufficio.

Così, nella pagina *Registro*, sotto *I dati di una persona*:

- **Esporta le righe di una persona** in CSV o JSON, in un file che porta il
  suo nome. Largo apposta: quello che ha fatto, più quello che la casa ha fatto
  a lei — il suo tag rifiutato, un'escalation che l'ha raggiunta.
- **Cancella la sua storia**, che non è la stessa cosa che cancellare il suo
  utente. Cancellare un utente lascia la storia di quello che ha fatto, perché
  il nome è copiato dentro ogni riga proprio perché resti. La cancellazione
  svuota il nome, l'account, il canale e il dispositivo sulle sue righe e
  lascia ogni evento dov'era: il registro continua a rispondere a *cosa è
  successo la notte del quattordici*, e non risponde più a *chi*. Viene
  registrata a sua volta, senza nominarla.

E nella pagina *Impostazioni*, sotto *Dati personali nel registro*:

- **Un preset di conservazione a sette giorni** che tocca solo le categorie che
  nominano persone, e lascia stare azioni, guasti e stati delle porte — quelli
  non nominano nessuno e sono quello che leggi quando un sensore non ha reagito
  tre settimane fa.
- **La pseudonimizzazione a tempo** (*Sostituisci i nomi nelle righe più
  vecchie*), spenta per impostazione predefinita, che dopo N giorni
  sostituisce i nomi con un identificatore stabile. Il pannello dice, prima che
  tu la accenda, che rinuncia alla risposta a *chi ha disinserito quella notte*
  per ogni riga più vecchia — che è esattamente la domanda per cui il registro
  esiste. Uno scambio vero, non una sicurezza gratuita, e non si torna indietro
  rispegnendola.

[docs/privacy.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/privacy.md)
è la versione pratica: cosa contiene una riga, dove finisce l'esenzione, e cosa
farci. È informazione, non consulenza legale — ed è in inglese, come tutta la
documentazione tecnica.

## Tastierini, tag e telecomandi

Foyer non parla con i singoli tastierini: espone un contratto. I modelli
cambiano ogni sei mesi, il contratto no. Tutto ciò che sa chiamare un servizio
di Home Assistant, pubblicare su un broker MQTT o fare una richiesta HTTP
all'endpoint di Foyer può inserire e disinserire questa casa. E qualunque
strada prenda, il registro non scrive «disinserito»: scrive chi, da quale
canale, con quale dispositivo.

- **Un dispositivo va dichiarato prima di poter comandare qualcosa.** Lo
  aggiungi nella pagina *Dispositivi di inserimento*; un dispositivo che
  l'impianto non conosce viene rifiutato qualunque codice porti, e il
  rifiuto finisce nel registro e in una notifica. Non è pignoleria: il blocco
  dopo codici sbagliati conta per dispositivo — e per account di Home Assistant
  nel pannello, nella card e nei servizi — quindi chi è
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
  accendi. Il dispositivo pubblica un comando e rilegge lo stato conservato sul
  broker (*retain*) per LED, segnali acustici e conto alla rovescia. Per
  impostazione predefinita quel messaggio dice il meno possibile: sta su un
  broker spesso condiviso, e quello che contiene viene raccontato a chiunque si
  colleghi dopo — compreso «casa inserita, non c'è nessuno». Tre livelli, e
  alzarlo è una scelta che fai sapendo cosa costa.
- **Sull'endpoint HTTP di Foyer**, per un dispositivo che non deve essere solo
  un nome su un broker: ognuno ha un token suo, mostrato una volta sola. Il
  token dice quale dispositivo sta chiedendo e non cifra niente, quindi in
  HTTP semplice il token e i codici digitati sul dispositivo si leggono sulla
  rete. Un dispositivo così viene servito lo stesso, ed è segnato *Non
  cifrato* in *Dispositivi di inserimento* e in ogni riga del registro che
  causa.
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
  documentazione del produttore e vanno verificati sul tuo firmware con
  `zwave_js.set_value`; e i cloni della famiglia Tuya cambiano i nomi delle
  azioni e i campi da una revisione di firmware all'altra, quindi il tuo
  tastierino Zigbee va guardato una volta sul suo topic prima di fidartene. Quello che
  i blueprint fanno con Foyer funziona comunque: a essere sbagliato è solo
  quello che il tastierino ti mostra.

**Dispositivi API.** Lo stesso endpoint serve un display touch nell'ingresso,
un relè che accende una spia «inserito», o un modulo ESP32 o Arduino fatto da
te. Ognuno legge e fa solo quello che è spuntato per lui, e ogni permesso
parte spento. Lo stato dell'allarme può essere di lettura libera; zone, batterie,
stato del sistema e registro, per impostazione predefinita, si leggono solo per
poco tempo dopo che qualcuno ha digitato un codice valido sul dispositivo, e
solo quello che quella persona può vedere. Ogni azione, inserire compreso e
anche sui tastierini, richiede un codice digitato sul dispositivo: il token da
solo non inserisce né disinserisce mai niente. Il contratto è scritto in
[docs/api/openapi.yaml](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/api/openapi.yaml),
versione v1, e un test in CI lo confronta con il codice; gli amministratori
possono leggerlo e provarlo con il token di un dispositivo nella pagina *API*
del pannello.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-api-device-it.png" alt="Un dispositivo sull'endpoint e cosa può leggere e fare: lo stato leggibile senza codice, zone, batterie e registro solo dopo un codice, inserire e disinserire permessi, escludere zone e prendere atto no, e la conferma che queste letture attraversano la rete senza cifratura" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-api-it.png" alt="La pagina API per gli amministratori: il contratto dei dispositivi, versione v1, mostrato con Swagger UI, con il pulsante Authorize per il token di un dispositivo e i tre percorsi dell'endpoint" width="900">
</p>

Ogni blueprint si importa sul tuo Home Assistant con un pulsante, da
[docs/keypads.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/keypads.md),
che contiene anche il contratto completo (servizi, MQTT, l'endpoint e i
dispositivi API), cosa vale onestamente ogni tipo di hardware e come scrivere
il proprio adattatore (in inglese, come tutta la documentazione tecnica).

Un tastierino non deve mai essere l'unica via d'ingresso: le batterie si
scaricano, le radio si disturbano, i broker si fermano. Tieni il pannello e la
card.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-devices-it.png" alt="Dispositivi di inserimento: due tastiere e un tag, ognuno dichiarato prima di poter comandare qualcosa, e il contratto MQTT con il messaggio che pubblicherà davvero" width="900">
</p>

## Cosa manca ancora, e conta

- **Nessun tastierino ESPHome nostro.** Una costruzione fai-da-te rientra nel
  contratto come qualunque altra, ma questo progetto non ne mantiene una
  in v1.

L'ordine è fissato e scritto, con quello che ogni passo deve dimostrare prima
di contare come fatto:
[la tabella di marcia](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md#16-roadmap).

## Foyer e Alarmo

[Alarmo](https://github.com/nielsfaber/alarmo) è l'implementazione di
riferimento in questo campo, ed è fatta bene. Foyer è scritto da zero e non ne
copia il codice. Dove differiscono oggi:

| | Foyer | Alarmo |
|---|---|---|
| **Escalation finché qualcuno non risponde** | Contatti con i canali in ordine di priorità, passi ai tempi che scegli, fermati da una qualunque delle quattro prese d'atto | Notifiche, nessuna escalation |
| **Inserirsi da sola, in sicurezza** | Regole con condizioni di sicurezza e un conto alla rovescia annullabile; il disinserimento spento finché non lo accendi, e mai su un'area segnata come perimetrale | Inserimento e disinserimento sulla presenza, via automazioni |
| **Simulatore** | Sì: lo stesso motore, un mondo e un orologio inventati, e una traccia che dice perché ogni azione sarebbe partita o no | — |
| **Walk test** | Sì: l'impianto è inserito per davvero, ogni risposta è trattenuta, e in cima ci sono le zone che non hanno mai reagito. Le zone 24h, manomissione, tecniche e panico restano attive | — |
| **Prova delle azioni** | Sì: fa suonare la sirena o parte il messaggio sul serio, con conferma, e nel registro come prova | — |
| **Scenari di inserimento** | Quanti ne vuoi, ciascuno inserisce un insieme di aree scelto | Le quattro modalità fisse di Home Assistant |
| **Aree con stato indipendente** | Sì: un `alarm_control_panel` ciascuna, più *Tutta la casa* | Una centrale sola, sensori raggruppati per modalità |
| **Fumo, gas, acqua** | Un canale separato, attivo a impianto disinserito, mai `triggered` su un'entità d'allarme | Sensori ordinari |
| **Un incidente per effrazione** | Sì, con una sola presa d'atto | Un allarme per sensore |
| **Utenti, codici, permessi** | Sì: un codice a testa, politica per operazione, codice di coercizione, blocco | Sì, codici per utente |
| **Tastierini, MQTT** | Sì, e un comando rifiutato torna indietro con un motivo stabile e le zone che hanno bloccato, per nome: un tastierino può suonare diversamente per *codice sbagliato* e per *finestra della cucina aperta* | Sì |
| **Tag NFC e telecomandi** | Nativi, legati a una persona, senza automazioni da scrivere | Tramite automazioni |
| **Gruppi di verifica (N su M)** | Sì, con i membri che mantengono la propria risposta | — |
| **Maturità** | Beta. Un solo autore, pochi mesi di vita | Anni di utilizzo, moltissime installazioni |
| **Italiano** | Pannello, card e aiuto contestuale di ogni pagina | Interfaccia tradotta |

Le righe in cui Alarmo ha un trattino sono quattro: tre sono modi di
controllare una configurazione invece di sperarci, e la quarta è il modo per
non farla suonare quando non serve. Quella che decide resta la maturità: se
vuoi un impianto che sia già stato collaudato da molti altri prima che da te,
usa Alarmo.

### Portare in Foyer una configurazione di Alarmo

Nessuno con quaranta sensori configurati li rimappa a mano per provare
qualcosa di nuovo, quindi Foyer può leggere la configurazione di Alarmo e
portarla dentro, da **Impostazioni → Importa da Alarmo**. Leggi
cos'è prima di usarlo.

**È uno strumento al meglio delle possibilità, non una migrazione.** Legge
`.storage/alarmo.storage`, che è il formato interno di Alarmo: il suo autore
può cambiarlo in qualunque versione, senza preavviso e senza colpa, perché non
è mai stato offerto a nessuno come interfaccia. Per questo l'importatore ti
dice tutto quello che non è riuscito a convertire, e rifiuta un file scritto
in una versione di archiviazione su cui non è stato verificato — dicendo quale
— invece di tirare a indovinare. Oggi sono le versioni da 6.1 a 6.3, quelle
che scrivono Alarmo da 1.9.5 a 1.10.19.

Ti mostra cosa farebbe prima di scrivere qualsiasi cosa, e aggiunge a quello
che c'è già invece di sostituirlo:

- **Aree, sensori e modalità** diventano aree, zone e scenari di Foyer: uno
  scenario per ogni modalità attivata che sorveglia qualcosa, oppure, se hai
  già uno scenario che riporta quella modalità a Home Assistant, è quello a
  inserire anche le nuove aree, così assistenti vocali e HomeKit continuano a
  funzionare. Dove Alarmo aveva più
  ritardi e Foyer ha posto per uno, prende il più lungo; dove un valore
  supera il limite di Foyer — una sirena che suonava mezz'ora — prende il
  limite. In entrambi i casi il report lo dice.
- **Ogni zona arriva spenta.** Alarmo legge `on` come allarme per qualunque
  sensore, che è esattamente il presupposto che Foyer è costruito per
  rifiutare: ogni zona porta la proposta di Foyer e non sorveglia niente
  finché non ne hai confermato il trigger nella pagina *Zone*.
- **Le persone arrivano senza codice, sempre.** Alarmo conserva i codici come
  hash nel proprio formato, e Foyer non accetta sulla fiducia una credenziale
  da un altro sistema, quindi ognuno ha bisogno di un codice nuovo nella pagina
  *Utenti* prima di poter disinserire con quello. Il report lo dice
  nella prima riga.
- **Sirene e interruttori** arrivano in un profilo di risposta. Notifiche,
  gruppi e le altre cose che Foyer non può portare sono elencati nel report,
  non indovinati: una
  notifica che arriva dove non dovrebbe è peggio di una che imposti di nuovo.

## Come puoi verificarlo invece di fidarti

Tre di queste cose puoi farle stasera: provare una notte nel
[simulatore](#chiedere-cosa-succederebbe-senza-che-succeda-niente),
[camminare per casa](#camminare-per-casa-e-premere-il-pulsante) e vedere quali
zone non si sono accorte di te, e premere il pulsante di prova accanto alla
tua sirena. Le altre sono strutturali, ed è per quelle che vale la pena
credere alle prime tre.

- **La parte che decide è una funzione pura.** «Questa zona si è aperta, questa
  area è inserita, e adesso?» viene deciso da codice che non può raggiungere
  Home Assistant, non ha un orologio suo e non può eseguire nessuna azione; è
  testato per conto proprio, e la CI rifiuta un commit che vi faccia entrare
  Home Assistant. È questo che rende veritiera, e non ottimistica, la risposta
  del simulatore: è la stessa funzione, a cui viene dato un mondo inventato, e
  un test verifica che lei e l'allarme in funzione arrivino alla stessa identica
  decisione dagli stessi identici dati.
- **Un buco nella copertura viene scritto.** Se Home Assistant è rimasto giù per
  due ore, il registro lo dice, con la durata. Non lascia mai credere che tu
  fossi protetto quando non lo eri.
- **Ogni azione dice se ha funzionato.** Una sirena che non ha suonato e una
  notifica che non è partita sono righe nel registro, marcate come non
  riuscite. Non silenzio.
- **Un nome che nessuno ha verificato è marcato come tale.** Una chiamata di
  servizio può dichiarare chi ha agito, e inserire non chiede un codice: quel
  nome resta nel registro, ma accanto compare *(non verificato)*. Una riga nata da
  un codice o da un tag NFC non porta quel marcatore. Una risposta sbagliata a
  «chi ha disinserito alle 03:14?» è peggio di nessuna risposta.
- **Il changelog dice cosa è cambiato nel comportamento**, non «varie
  correzioni», perché è quello che serve per decidere se prendere un
  aggiornamento.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-log-it.png" alt="Il registro: inserimento, un allarme, un inserimento rifiutato con la zona che l'ha bloccato, il buco di riavvio, una modifica di configurazione con valore prima e dopo, e una notifica non riuscita" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-users-it.png" alt="Utenti e codici: due persone con i loro permessi, ambito e validità, e la tabella di quali operazioni chiedono un codice" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-arm-code-it.png" alt="Inserire dalla Panoramica: la richiesta dice a cosa serve il codice, Codice per inserire Fuori casa, e quale area lo chiede, Primo piano" width="900">
</p>

Come si legge una traccia di decisione, e cosa vale la pena provare prima di
fidarsi di una configurazione:
[docs/simulator.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/simulator.md)
(in inglese).

## A cosa servono i codici, e a cosa no

I codici di Foyer servono a impedire che disinserisca chi è *dentro* casa tua:
familiari, ospiti, personale domestico, utenti non amministratori di Home
Assistant, chiunque prenda in mano il tablet a muro che hai lasciato sbloccato.
Non servono a fermare **te**. Un amministratore di Home Assistant può leggere
`.storage`, disattivare l'integrazione o chiamare qualunque servizio, quindi
per lui nessun codice di Foyer vuol dire niente — e per lo stesso identico
motivo il registro eventi è *utile* come traccia, non *inalterabile*.

Questo è il confine onesto, e vale la pena conoscerlo prima di appoggiarcisi.
Foyer è un'integrazione che fa quello che fa un allarme; non è un impianto
certificato, non soddisfa CEI 79-3 / EN 50131 o equivalenti, e non sostituisce
un impianto certificato dove una polizza o un capitolato lo richiedano.

**Il webhook di presa d'atto, se lo accendi, è un URL non autenticato.**
Esiste perché un provider vocale possa rimandare il tasto premuto durante una
chiamata. I webhook di Home Assistant sono aperti a chi ne conosce
l'indirizzo: chiunque lo abbia, o lo intercetti, può prendere atto di un
allarme in corso, cioè fermare l'escalation mentre sta andando dalla persona
successiva. Non può inserire, disinserire, leggere il registro o cambiare
niente. Non esiste finché non lo accendi, l'id è generato a caso, il pannello
ne mostra l'indirizzo una sola volta — quando viene generato — e spegnendolo
viene dimenticato; per rivederlo se ne genera uno nuovo.
[I dettagli](docs/notification-channels.md#twilio-voice-call) (in inglese).

**Un codice di coercizione è il codice del suo titolare, e lo dice solo al
registro.** Ogni persona può averne uno oltre al codice normale. Vale ovunque
vale quello normale — inserire, disinserire, escludere una zona, un walk test,
le impostazioni del pannello, sbloccare un dispositivo, una chiamata di
servizio, un tastierino, la card — e fa esattamente quello che farebbe il
codice normale, risposta compresa: chi è al tastierino non vede e non sente
nessuna differenza. Quello che cambia è un evento silenzioso, `duress`, che
scatta a ogni uso del codice, qualunque cosa si stesse facendo e che sia stata
permessa o no, e dice che cosa è stato chiesto (`{{ operation }}` in un
messaggio). Gli risponde solo il **profilo predefinito**, e nulla finché non
gli dai un'azione: mandalo a qualcuno fuori casa. È sempre silenzioso — resta
fuori quello che nomina l'elenco silenzioso, di serie la sirena, la voce e il
campanello — e anche una notifica di Home Assistant è la risposta sbagliata,
perché compare su ogni schermo di Home Assistant, tablet a muro compreso. La
riga sta nella pagina del registro e in un'esportazione, mai nella Panoramica,
in `sensor.foyer_last_event` o nel registro di un dispositivo API. Arriva anche
sul bus degli eventi di Home Assistant come `foyer_event`, ed è così che una
tua automazione può risponderle: una che mostra gli eventi di sicurezza da
qualche parte in casa deve lasciare fuori `duress`. Il bus porta solo quello
che il registro scrive, quindi disattivare la categoria `security` ferma anche
quell'evento; la risposta del profilo predefinito non dipende dal registro.
[Come rispondere](docs/notification-channels.md#answering-a-duress-code) (in
inglese).

**Chi può avviare un walk test può tenere zitta la casa.** Un walk test si
cammina in tutta la casa, quindi inserisce ogni area disinserita che può —
anche quelle che a chi lo avvia non sono permesse, ma non una che conserva
ancora una memoria d'allarme — e finché non finisce nessuna area risponde a
una rilevazione ordinaria, nemmeno una inserita da qualcun altro. Dura quindici minuti dall'ultima rilevazione per impostazione
predefinita, mai più di tre ore dall'inizio di un test — ma niente impedisce
di riavviarlo appena finisce, ogni volta con la sua notifica e le sue righe
nel registro — e basta il permesso *Walk test*, non serve *Disinserire*. È voluto, e non è mai silenzioso su se stesso:
chiede un codice per impostazione predefinita, mette un banner su ogni
schermo, manda una notifica all'inizio e alla fine, ed entrambe le sue righe
nel registro nominano la persona. Restano attivi durante il test: le zone
24h, manomissione, tecniche e panico, un allarme già in corso e un codice di
coercizione. Dai *Walk test* alle persone a cui daresti *Disinserire*. E
togliere *Codice richiesto* accanto ad *Avvio del walk test* lo consegna a
qualunque cosa possa avviarlo senza essere identificata — qualunque account
di Home Assistant che chiami `foyer.walk_test`, collegato a una persona o no,
perché una chiamata di servizio identifica una persona solo con un codice; e
un'automazione, uno script o un account non collegato a nessuno attraverso
`switch.foyer_walk_test` o il pannello — perché i
permessi si controllano sulla persona che chiede, e una richiesta che non
identifica nessuno non ne ha da controllare.

**E non è un sistema antincendio.** Il canale tecnico è davvero utile — è
attivo che la casa sia inserita o no, e disinserire non ha nessuna autorità su
di lui — ma un rilevatore di fumo collegato a Home Assistant non sostituisce
rilevatori certificati e interconnessi. Quelli comprali a parte: non costano
molto, e sono l'unica voce di questa pagina in cui sbagliarsi non riguarda un
furto.

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
   davanti al rilevatore, guarda cambiare lo stato. È l'unico passo che vale la
   pena fare con calma.
3. **Crea il tuo utente con un codice.** Finché nessuno ne ha uno, non viene
   chiesto a nessuno, e il pannello lo dice dove non puoi non vederlo. Da
   quel momento il pannello lo chiede anche a te dove la politica lo chiede,
   amministratore o no.
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
4. Nella barra laterale compare una voce **Foyer**, e una procedura guidata di
   cinque passi brevi completa la configurazione: *Area*, *Zone*, *Scenario*,
   *Utente e codice*, *Notifica di prova*. Prima di *Fine* elenca quello che i
   cinque passi non hanno coperto, ognuno con la pagina che lo copre.

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

*Completa* e *Compatta* aprono il tastierino quando serve un codice;
*Tastierino* lo mostra sempre, e un ritardo d'ingresso che chiederà un codice
lo apre da solo. Sopra le cifre dice a cosa servono — *Codice per inserire
Fuori casa*, *Codice per disinserire Piano terra* — e partono solo con quel
comando: qualunque altro pulsante parte senza. Le cifre digitate vengono
dimenticate dopo 30 secondi senza toccare un tasto, e quando la card esce
dallo schermo. Durante un ritardo d'ingresso o un allarme i pulsanti degli
scenari si fanno da parte, perché l'unica cosa da fare è disinserire.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-it.png" alt="La card nelle disposizioni completa e compatta durante il ritardo d'ingresso: ogni area con il suo stato, il conto alla rovescia, e il tastierino che si apre da solo perché per disinserire serve un codice" width="620">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-keypad-it.png" alt="Il layout a tastierino per un tablet a muro: tre cifre di un codice digitate, il tempo di ingresso che scorre, e il pulsante che lo chiude" width="620">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-code-it.png" alt="Il tastierino in attesa di un codice: la didascalia dice Codice per inserire Fuori casa, tre cifre digitate, e il tasto di conferma dice Inserisci Fuori casa" width="620">
</p>

## Domande che vengono fatte

<details>
<summary>Posso usare Foyer e Alarmo insieme?</summary>

Si possono installare entrambi, ma non puntarli sugli stessi sensori: avresti
due sistemi che decidono cosa significa una finestra aperta, e che si
inseriscono e disinseriscono l'uno all'insaputa dell'altro. Prova Foyer su
qualche zona, o su un impianto di prova, e spostaci il resto quando se lo
sarà guadagnato. L'[importatore](#portare-in-foyer-una-configurazione-di-alarmo)
è fatto proprio per questo: porta le zone spente, quindi niente viene
sorvegliato due volte finché non lo decidi tu.

</details>

<details>
<summary>Chi può disinserire?</summary>

Chi ha un codice, e solo per ciò che i suoi permessi consentono. Finché non
crei il primo utente non viene chiesto nulla a nessuno e chiunque abbia accesso
a Home Assistant può disinserire — il pannello lo dice apertamente finché dura.
Una persona può essere esentata dal digitare il codice sui canali che già sanno
chi è, come l'interfaccia di Home Assistant con il suo account; su un tastierino
condiviso il codice *è* l'identità, quindi lì l'esenzione non vale.

Essere amministratore di Home Assistant però non identifica nessuno: il tablet
a muro lasciato sbloccato è quasi sempre collegato con un account
amministratore, quindi il pannello chiede il codice anche all'amministratore,
come a chiunque altro, dove la politica lo chiede.

</details>

<details>
<summary>Posso inserire dalle card di Home Assistant, o a voce?</summary>

Sì, e risponde Foyer, come ovunque. Che cosa chiede prima Home Assistant
dipende da una sola cosa che Foyer gli dice: che per inserire serve un codice.
Lo dice solo finché la tua politica chiede un codice per inserire e nessuno ha
attivato l'esenzione qui sopra, perché Home Assistant rifiuterebbe chiunque non
ne digiti uno, anche la persona esentata. Il pannello *Tutta la casa* lo dice
solo quando ogni modalità che può ancora inserire chiede un codice: dove una
modalità non ne chiede, Home Assistant rifiuterebbe anche quella. Finché lo
dice, la finestra a comparsa di Home Assistant e i pulsanti di inserimento di
una card *Mosaico* chiedono il codice da sé. Quando non lo dice — qualcuno è
esentato, o le modalità non sono d'accordo — non lo chiedono: una persona
esentata inserisce senza codice, e chiunque altro a cui Foyer chieda un codice
viene rifiutato da Foyer, con una riga nel registro e un messaggio che dice
dove digitarlo — la card di Foyer, il pannello, o la card *Pannello degli
Allarmi* di Home Assistant, che mostra il campo del codice dovunque un codice
possa essere chiesto ma offre l'inserimento solo finché il pannello è
disinserito. Scegliere un'altra modalità con la casa già inserita è un cambio
di scenario, che per impostazione predefinita chiede un codice anche dove
inserire non lo chiede; la finestra a comparsa chiede un codice solo finché
Foyer dice che per inserire ne serve uno, quindi dove lo chiede solo il cambio
il codice si digita nella card di Foyer o nel pannello.

Gli assistenti vocali leggono la stessa risposta. Ad Alexa un pannello viene
offerto solo finché inserirlo non chiede un codice; Alexa non ne manda
nessuno, e non aspetta la risposta di Foyer, quindi un rifiuto si vede solo
nello stato del pannello e nel registro. Google Assistant chiede il suo PIN
prima di inserire solo finché serve un codice, e manda il PIN salvato nella
propria configurazione, se ce n'è uno, che l'abbia chiesto o no: se è il
codice Foyer di qualcuno, ciò che chiede viene fatto a suo nome; se non lo è,
è un codice sbagliato, e conta per il blocco.

Fai attenzione all'account con cui è collegato un assistente vocale, perché
agisce come quell'account di Home Assistant per chiunque stia parlando.
Collegato tramite l'account di una persona esentata, passa quell'esenzione a
chiunque sia a portata di voce: inserire senza codice, e passare la casa a
un'altra modalità, che disinserisce le aree inserite solo dalla modalità
precedente. Un PIN di Google che è un codice Foyer fa lo stesso, e viene
mandato senza che nessuno lo pronunci finché per inserire non serve un codice.
Collega gli assistenti vocali con un account che non sia collegato a una
persona esentata, e se il PIN di Google è un codice Foyer, dallo a una persona
che abbia solo ciò che lasceresti fare a chiunque vicino all'altoparlante —
*Inserire*, per esempio. Tramite Home Assistant Cloud agiscono come l'account
del Cloud, che la pagina *Utenti* non propone di collegare, quindi lì
l'esenzione non li raggiunge mai.

</details>

<details>
<summary>Sono l'amministratore e non ho un codice</summary>

In una casa dove altri ne hanno uno, o se il tuo utente Foyer è stato
disattivato o ha superato la sua finestra di validità, recuperi l'accesso da
**Impostazioni → Dispositivi e servizi → Foyer → Configura**. Riattiva il tuo
utente Foyer, toglie la sua finestra di validità e imposta un codice nuovo; un
account che non ha un utente Foyer ne riceve uno, con tutti i permessi. Sono
elencati solo gli account amministratore. Non è mai silenzioso: il recupero
viene scritto nel registro, mostrato come notifica di Home Assistant e mandato
a tutti i contatti, con il nome dell'account. Per chiunque altro si passa dalla
pagina *Utenti*.

</details>

<details>
<summary>Funziona senza internet?</summary>

Sì. Foyer non apre nessuna connessione verso l'esterno, e non richiede né un
account cloud né un broker. Se sopravvivano le *notifiche* a una linea tagliata
è un'altra domanda, e la risposta onesta è che una notifica push no — ed è per
questo che un'escalation è una lista di canali e non uno solo, e per cui almeno
un canale locale, per esempio un modem GSM USB, va messo in quella lista.

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

Se ne vanno la sua configurazione, lo stato dell'allarme salvato, ogni entità e
dispositivo che ha creato, il pannello nella barra laterale, le sue
segnalazioni in Impostazioni, le notifiche che aveva messo su e il messaggio
MQTT conservato sul broker (*retain*) — un messaggio conservato sopravvive all'integrazione e
continuerebbe a raccontare a chiunque si colleghi dopo cosa stava facendo la
casa.

L'archivio del registro eventi se ne va solo se lo hai detto tu, con un
interruttore nella pagina *Impostazioni* che è spento per impostazione
predefinita. La conferma di Home
Assistant è l'ultima finestra che c'è, quindi la domanda si fa prima — e
tenere trenta giorni di storia è l'unica risposta che non può distruggere
qualcosa che nessuno voleva distruggere. Il file è `foyer-log.db` nella
cartella di configurazione.

Gli scatti delle telecamere non vengono mai cancellati. Sono fotografie
dell'interno di casa tua, in una cartella che hai scelto tu e che può contenere
file che non sono mai stati di Foyer — rimuoverli sta a te.
[docs/privacy.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/privacy.md)
lo ripete tutto, nel posto dove uno lo va a cercare.

</details>

<details>
<summary>È disponibile nella mia lingua?</summary>

Oggi italiano e inglese, pannello, card e aiuto contestuale compresi.
Aggiungere una lingua non tocca il codice: si copiano due file JSON, si traduce
e si apre una pull request. La CI fallisce se gli insiemi di chiavi dei due
file non coincidono, quindi un pannello tradotto a metà non può essere
pubblicato. [CONTRIBUTING.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CONTRIBUTING.md#adding-a-language)
nomina i due file e l'unica riga che non è una traduzione pura.

</details>

## Se qualcosa va storto

Apri una [issue](https://github.com/foyer-labs/Foyer-Home-Defender/issues/new/choose):
il modulo chiede quanto segue e dice dove trovare ogni parte. Di'
quale versione di Foyer e di Home Assistant, cosa ti aspettavi, e cosa mostra
la pagina del registro: la riga di solito contiene già la risposta, quindi una
schermata vale più di una descrizione. In italiano o in inglese, come preferisci.

Allegare la **diagnostica** di Home Assistant, dalla pagina dell'integrazione
in Impostazioni, di solito trasforma una segnalazione in una risposta invece
che in cinque domande. È anonimizzata apposta: niente nomi, niente codici,
niente hash, niente URL, e gli id delle entità sostituiti da segnaposto
stabili, così porta la forma dell'impianto e niente sulle persone che
ci abitano.

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
[CONTRIBUTING.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CONTRIBUTING.md) dice cos'altro deve
portare una pull request (in inglese).

Il progetto completo, comprese le ragioni dietro le decisioni che sembrano
arbitrarie finché non si sa perché, è in
[docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md)
(in inglese, come tutto il codice e la documentazione tecnica).

## Segnalare un problema di sicurezza

Un modo per disinserire senza codice, un modo per far restare zitto l'allarme,
un modo per leggere il registro di qualcun altro: sono cose da dire all'autore
prima che siano pubbliche. Su questo repository è attiva la **segnalazione
privata di vulnerabilità** di GitHub:
[apri un advisory privato](https://github.com/foyer-labs/Foyer-Home-Defender/security/advisories/new).
Tutto ciò che non è una vulnerabilità sta meglio in una issue normale, dove
più persone possono aiutare.

[SECURITY.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/SECURITY.md)
dice cosa rientra e cosa no: un amministratore del tuo Home Assistant può
leggere `.storage`, disabilitare l'integrazione e chiamare qualunque servizio,
e nessuna versione di Foyer si difenderà da questo.

<p align="center">
  <a href="https://www.buymeacoffee.com/foyerlabs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-green.png" alt="Buy Me a Coffee" height="60"></a>
</p>

## Licenza

Apache-2.0. Vedi [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) e [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
