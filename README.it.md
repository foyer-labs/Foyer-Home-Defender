<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.md">English</a> · <strong>Italiano</strong></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?include_prereleases&sort=semver&label=versione" alt="Ultima versione"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5" alt="Home Assistant 2025.1 o successivo">
  <img src="https://img.shields.io/badge/HACS-repository%20personalizzato-41BDF5" alt="Repository personalizzato HACS">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licenza-Apache--2.0-blue" alt="Apache-2.0"></a>
</p>

Foyer Home Defender trasforma Home Assistant in una vera centrale d'allarme:
aree con un proprio stato di inserimento, scenari di inserimento che definisci
tu, zone che dichiarano cosa significa «in allarme» per loro, un motore di
risposta, un registro eventi verificabile e — nelle fasi successive — utenti
identificati, tastiere fisiche e un simulatore che permette di controllare la
configurazione prima di fidarsene.

> ### Stato: Fase 1 completa — il nucleo dell'allarme
>
> Una casa si può proteggere con questo. Pensaci due volte prima che sia
> l'*unica* cosa a proteggerla: **non ci sono ancora utenti né codici**, quindi
> chiunque possa raggiungere Home Assistant può disinserire l'allarme. I codici
> arrivano nella fase successiva.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-it.png" alt="Il pannello di Foyer: due aree inserite da un solo scenario, una in conto alla rovescia sul ritardo d'ingresso, e le zone non pronte" width="900">
</p>

## Cosa fa già oggi

- **Aree con un proprio stato di inserimento**, ciascuna con la sua entità
  `alarm_control_panel`, più una centrale che le aggrega.
- **Scenari definiti da te**: *Notte, solo piano terra*, *Solo garage*, *Cane in
  casa*. Non quattro modalità fisse.
- **Zone che dichiarano il proprio stato di allarme.** I contatti normalmente
  chiusi e normalmente aperti si comportano al contrario; Foyer propone la
  condizione a partire dalla classe del dispositivo e ti chiede di confermarla,
  perché un errore qui produce un allarme che non suona mai.
- **Otto preimpostazioni di zona** su proprietà modificabili: istantanea,
  ritardata, seguistrada, 24h, antimanomissione, tecnica, antirapina, e zone
  chiave che inseriscono o disinseriscono invece di allarmare.
- **Ritardi di uscita e di ingresso**, quattro politiche per una zona aperta al
  momento dell'inserimento (blocca, escludila, aspetta che si chiuda, ignorala),
  inserimento forzato, esclusione manuale e temporizzata, tempo massimo di
  sirena con memoria d'allarme.
- **Un canale separato per fumo, gas e acqua.** È attivo che la casa sia
  inserita o no, non tocca mai `alarm_control_panel` — dove *triggered* significa
  «effrazione» per HomeKit, Google e Alexa — e il disinserimento non lo azzera.
- **Incidenti, non allarmi per zona.** Un'effrazione vera fa scattare più zone:
  diventano un solo incidente, con una sola presa in carico, invece di tre
  raffiche di notifiche nel momento peggiore possibile.
- **Gruppi di verifica**, N su M entro una finestra, con i membri che mantengono
  la propria risposta: un rivelatore notifica, due fanno suonare la sirena.
- **Profili di risposta**: dieci azioni — notifica, sirena, luce, telecamera,
  scena, interruttore, messaggio vocale, chiamata a qualunque servizio di Home
  Assistant, attesa — ciascuna con al massimo due condizioni, ereditate
  area → scenario → predefinito.
- **Campanello** quando una zona si apre mentre la sua area non la sorveglia, su
  un altoparlante, una sirena o il telefono, con ore di silenzio per singolo
  destinatario.
- **Un registro eventi** in un archivio tutto suo, che la cancellazione dopo
  dieci giorni del recorder di Home Assistant non può toccare: cosa è successo,
  dove, attraverso quale canale, se ogni azione ha davvero funzionato, e chi ha
  cambiato cosa.
- **Uno stato che sopravvive a un riavvio**, compresi un'attesa in corso e una
  sirena che sta suonando — e il buco stesso viene registrato, così il registro
  non lascia mai credere che la casa fosse protetta quando non lo era.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-log-it.png" alt="La pagina del registro: inserimento, un allarme, un inserimento rifiutato che nomina la zona, il buco di riavvio e una notifica non riuscita" width="900">
</p>

## Cosa manca ancora, e conta

- **Nessun utente, nessun codice, nessun permesso.** Chiunque abbia accesso a
  Home Assistant può inserire e disinserire, e il registro annota il canale
  invece della persona. Fase 2.
- **Nessun simulatore e nessuna prova di percorso.** Non puoi ancora chiedere
  «cosa succederebbe se la finestra della cucina si aprisse adesso?» senza
  aprirla. Fase 3.
- **Nessuna scalata delle notifiche.** Vanno direttamente a un servizio
  `notify`; non salgono da push a SMS a telefonata finché qualcuno non risponde.
  Fase 4.
- **Nessun supporto per tastierini, nessun MQTT.** Fase 2.

Il progetto completo, fasi comprese, è in
[docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md)
(in inglese, come tutto il codice e la documentazione tecnica); cosa è cambiato
in ogni versione è in
[CHANGELOG.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/CHANGELOG.md).

## Accanto ad Alarmo

[Alarmo](https://github.com/nielsfaber/alarmo) è l'implementazione di
riferimento in questo campo, ed è fatta bene: modalità di inserimento, ritardi
per sensore, un motore di azioni, utenti con codice, MQTT e una card Lovelace.
Foyer è scritto da zero e non ne copia il codice. Punta a tre cose che Alarmo
non fa:

| | Foyer | Alarmo |
|---|---|---|
| **Scenari di inserimento** | Quanti ne vuoi, ciascuno inserisce un insieme di aree scelto — *già disponibile* | Le quattro modalità fisse di Home Assistant |
| **Simulatore e prova di percorso** | Previsti, Fase 3: lo stesso motore, un orologio finto, nulla di eseguito | — |
| **Scalata con presa in carico** | Prevista, Fase 4: push, poi SMS, poi telefonata, e si ferma quando una persona risponde | — |

Alarmo è un'integrazione finita e molto usata; Foyer è una alpha. Se ti serve un
allarme oggi e i codici ti interessano, usa Alarmo.

## Modello di sicurezza

I codici di Foyer — quando esisteranno — proteggono da familiari, ospiti,
personale domestico, utenti non amministratori di Home Assistant e da chiunque
trovi un tablet a muro sbloccato. **Non** proteggono da un amministratore di
Home Assistant, che può leggere `.storage`, disattivare l'integrazione o
chiamare qualunque servizio. Per lo stesso motivo il registro eventi è *utile*
come traccia, non *inalterabile*.

**Foyer non è un sistema d'allarme certificato**, e **non è un sistema
antincendio**: un rivelatore di fumo collegato a Home Assistant non sostituisce
rivelatori certificati e interconnessi.

## Installazione

1. In HACS, apri il menu → *Repository personalizzati*, aggiungi l'URL di questo
   repository con categoria *Integrazione*.
2. Installa *Foyer Home Defender* e riavvia Home Assistant.
3. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Foyer Home
   Defender*. Dài un nome alla prima area e al primo scenario, scegli l'entità
   della prima zona, poi conferma gli stati in cui conta come «in allarme».
   Verificali sul sensore vero: apri la porta, passa davanti al rivelatore,
   guarda il suo stato.
4. Nella barra laterale compare una voce **Foyer**, e una breve procedura
   guidata completa la configurazione: le altre zone, lo scenario, e una
   notifica di prova per sapere che il canale funziona.

Richiede Home Assistant 2025.1 o successivo.

> **Finché Foyer è in alpha, ogni versione è pubblicata come pre-release su
> GitHub**, e HACS mostra il commit anziché il numero di versione per i
> repository che non ne hanno nessuna marcata stabile. Per vedere e scegliere i
> nomi delle versioni, abilita l'entità *switch* che HACS crea per questo
> repository (*Impostazioni → Dispositivi e servizi → Entità*, cerca «pre
> release»; è disabilitata di default). Dalla prima beta le versioni saranno
> pubblicate normalmente.

### La card

Scegli *Foyer Home Defender* nel selettore delle card della dashboard, oppure
scrivila a mano:

```yaml
type: custom:foyer-card
entity: alarm_control_panel.foyer_master   # oppure alarm_control_panel.foyer_<area>
layout: full                               # oppure compact
```

La card viene caricata da sola: non serve aggiungere alcuna risorsa alla
dashboard. Non decide nulla da sé: manda un comando e mostra la risposta,
compreso il nome della zona che l'ha rifiutato.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-it.png" alt="La card nelle disposizioni completa e compatta" width="900">
</p>

## Sviluppo

```
custom_components/foyer/   l'integrazione (HACS installa questa cartella così com'è)
  core/                    motore decisionale puro: mai un import di Home Assistant
  runtime/ entity/ api/    gli strati che parlano con Home Assistant
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

`core/` non deve mai importare `homeassistant`: è ciò che mantiene il motore
decisionale una funzione pura, e quindi ciò che renderà veritiera la traccia del
simulatore. La CI lo verifica; se quel controllo fallisce, si corregge il
codice, mai il test.

Per aggiungere una lingua, copia `translations/en.json` e
`translations/panel/en.json` nel nuovo codice lingua, traduci, e apri una pull
request. La CI fallisce se gli insiemi di chiavi non coincidono.

## Licenza

Apache-2.0. Vedi [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) e [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
