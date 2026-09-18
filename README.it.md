<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.md">English</a> · <strong>Italiano</strong></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>Una vera centrale d'allarme per Home Assistant: aree che si inseriscono da sole, scenari definiti da te, zone che dichiarano cosa le fa scattare, e un registro che dice la verità.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?include_prereleases&sort=semver&label=versione" alt="Ultima versione"></a>
  <img src="https://img.shields.io/badge/stato-alpha-orange" alt="Alpha">
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 o successivo">
  <img src="https://img.shields.io/badge/HACS-repository%20personalizzato-41BDF5" alt="Repository personalizzato HACS">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licenza-Apache--2.0-blue" alt="Apache-2.0"></a>
</p>

> ### Stato: alpha. Il nucleo dell'allarme funziona, e ora chiede un codice.
>
> Può proteggere una casa, e lo sta facendo. **Utenti, codici, permessi e
> blocco dopo tentativi ripetuti ci sono**: crei un utente con un codice e il
> disinserimento lo chiede, dal pannello, dalla card e da un tablet a muro, e
> il registro dice finalmente chi è stato. I tastierini fisici e il contratto
> MQTT sono la prossima versione, ed è quello che trasforma questa alpha in
> una beta.

**Provalo se** hai già sensori di porta, finestra o movimento in Home
Assistant, vuoi una centrale con scenari di inserimento veri invece di una
cartella di automazioni, e sei disposto a far girare una alpha su una casa che
ha anche altre serrature.

**Non ancora, se** inserisci da un tastierino fisico, se ti serve MQTT, o se
vuoi qualcosa di finito: [Alarmo](https://github.com/nielsfaber/alarmo) queste
cose le fa oggi, e le fa bene.

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
- **Ritardi di uscita e di ingresso**, e quattro cose che una zona può fare se
  è aperta mentre inserisci: bloccare, escludersi, aspettare che la chiudi, o
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
  una card nelle disposizioni `full`, `compact` e `keypad`.

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

## Cosa manca ancora, e conta

- **Nessun tastierino fisico e nessun MQTT.** I codici funzionano dal
  pannello, dalla card e da un tablet a muro; un tastierino Ring o Zigbee
  appeso al muro non parla ancora con Foyer. *Prossima versione.*
- **Nessun simulatore e nessuna prova di percorso.** Non puoi ancora chiedere
  «cosa succederebbe se la finestra della cucina si aprisse adesso, con questo
  scenario, a quest'ora?» senza aprirla. *Dopo.*
- **Nessuna scalata delle notifiche.** Vanno direttamente a un servizio
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
| **Tastierini, MQTT** | **Non ancora** | Sì |
| **Maturità** | Alpha. Un solo autore, pochi mesi di vita | Anni di utilizzo, moltissime installazioni |
| **Simulatore, prova di percorso** | Previsti, non scritti | — |
| **Interfaccia in italiano** | Completa: pannello, card e testi di aiuto | Solo in inglese |

Se ti serve un allarme oggi e un tastierino al muro ti interessa, usa Alarmo.

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

Nient'altro: nessun account cloud, nessun broker MQTT, nessuna connessione
verso l'esterno che parta da Foyer.

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
<summary>HACS mostra il codice di un commit invece del numero di versione</summary>

Finché Foyer è in alpha, ogni versione è pubblicata come *pre-release* su
GitHub, e HACS offre solo le release che non sono pre-release: per un
repository che non ne ha nessuna ripiega sul ramo predefinito e mostra il
commit. Per vedere e scegliere i nomi delle versioni, abilita l'entità *switch*
che HACS crea per questo repository (*Impostazioni → Dispositivi e servizi →
Entità*, cerca «pre release»; è disabilitata di default). Dalla prima beta le
versioni saranno pubblicate normalmente e questa nota sparirà.

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
layout: full                               # full, compact o keypad
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

Per sapere quando arrivano i tastierini, metti il repository fra quelli che
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
tests/core, tests/repo     girano senza Home Assistant installato
tests/ha                   girano dentro l'ambiente di test di Home Assistant
```

```bash
pip install pytest ruff
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
