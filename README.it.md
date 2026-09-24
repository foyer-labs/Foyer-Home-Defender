<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.md">English</a> · <strong>Italiano</strong></p>

<h1 align="center">Foyer Home Defender</h1>

<p align="center"><em>Una centrale antintrusione per i sensori che hai già in Home Assistant — con un simulatore che ti dice cosa farebbe prima che tu te ne fidi.</em></p>

<p align="center">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/releases"><img src="https://img.shields.io/github/v/release/foyer-labs/Foyer-Home-Defender?sort=semver&include_prereleases&label=versione" alt="Ultima versione"></a>
  <img src="https://img.shields.io/badge/stato-beta-yellow" alt="Beta">
  <img src="https://img.shields.io/badge/Home%20Assistant-2026.6%2B-41BDF5" alt="Home Assistant 2026.6 o successivo">
  <img src="https://img.shields.io/badge/HACS-repository%20personalizzato-41BDF5" alt="Repository personalizzato HACS">
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE"><img src="https://img.shields.io/badge/licenza-Apache--2.0-blue" alt="Apache-2.0"></a>
  <a href="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml"><img src="https://github.com/foyer-labs/Foyer-Home-Defender/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
</p>

Il contatto sulla porta che accende la luce del corridoio e il sensore di
movimento che fa da luce notturna sono i sensori di cui è fatto un antifurto.
Foyer li trasforma in uno: aree che si inseriscono per conto loro, scenari di
inserimento con i nomi che scegli tu, una risposta che continua a cercare
qualcuno finché non risponde — e un modo per verificare tutto senza far
partire niente.

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-overview-it.png" alt="Il pannello di Foyer: due aree inserite da un solo scenario, una in conto alla rovescia sul ritardo d'ingresso, le zone non pronte e gli ultimi eventi" width="900">
</p>

## Cosa ottieni

- **Aree e scenari tuoi.** Ogni area si inserisce per conto suo e ha la sua
  entità di centrale d'allarme; *Notte, solo piano terra*, *Solo garage* o
  *Cane in casa* sono scenari, quanti ne servono alla casa.
  [Per iniziare](docs/getting-started.it.md)
- **Zone che dicono cosa vuol dire «scattata».** I contatti normalmente chiusi
  e normalmente aperti si comportano al contrario, quindi lo stato di scatto
  di ogni zona si conferma sul sensore vero, e un sensore che diventa
  `unavailable` è un guasto, mai «tutto tranquillo». [Zone](docs/zones.it.md)
- **Chiedi prima di fidarti.** Un simulatore che prova una notte senza che
  succeda niente, un walk test che mostra quali zone non ti hanno mai visto, e
  un pulsante di prova che fa suonare la sirena sul serio.
  [Simulatore](docs/simulator.md) (in inglese)
- **Un incidente per effrazione, e una notifica che continua a cercare.** La
  finestra, il corridoio e le scale diventano un solo incidente con una sola
  presa d'atto; push adesso, SMS fra un minuto, poi una seconda persona,
  finché qualcuno non risponde. [Profili di risposta](docs/response-profiles.it.md) ·
  [Canali di notifica](docs/notification-channels.md) (in inglese)
- **Un codice per ogni persona, verificato solo nel backend.** Permessi per
  persona, un codice di coercizione che funziona come quello normale e fa
  scattare un allarme silenzioso, il blocco dopo codici sbagliati ripetuti, e
  un registro che dice chi ha fatto cosa. [Modello di sicurezza](docs/security-model.it.md)
- **Tastierini, tag e dispositivi tuoi.** Tastierini Ring e Zigbee, tag NFC e
  telecomandi, tramite servizi, MQTT o l'endpoint HTTP di Foyer, con un rifiuto
  che dice quale zona è aperta. [Tastierini](docs/keypads.md) (in inglese)
- **Fumo, gas e acqua su un canale separato.** Attivo che la casa sia inserita
  o no, e mai annunciato come un'effrazione. [Zone](docs/zones.it.md#il-canale-tecnico)
- **Una casa che si inserisce da sola quando escono tutti**, dopo un conto
  alla rovescia che puoi annullare. Il disinserimento automatico è spento di
  serie e non tocca mai il perimetro. [Regole automatiche](docs/automation-rules.md) (in inglese)
- **Un allarme che dice quando ha smesso di funzionare.** Rete elettrica, ogni
  canale di notifica, un watchdog esterno e le interferenze radio.
  [Stato del sistema](docs/system-health.md) (in inglese)
- **Un registro tutto suo, trenta giorni di serie**, con gli strumenti per
  consegnare a qualcuno i suoi dati o toglierlo dal registro.
  [Privacy](docs/privacy.md) (in inglese)
- Una configurazione di Alarmo esistente si può portare in Foyer.
  [Passare da Alarmo](docs/migrating-from-alarmo.it.md)

<table>
  <tr>
    <td width="50%"><img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-zone-it.png" alt="L'editor della zona chiede in quali stati la zona è in allarme, e pretende che tu li abbia verificati sul sensore vero"></td>
    <td width="50%"><img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/panel-walktest-it.png" alt="Un walk test in corso: un banner dice che ogni risposta è trattenuta e che cosa resta attivo, e in cima alla tabella c'è la zona che non ha mai reagito"></td>
  </tr>
</table>

<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/screenshots/card-it.png" alt="La card nelle disposizioni completa e compatta durante il ritardo d'ingresso: ogni area con il suo stato, il conto alla rovescia, e il tastierino che si apre da solo perché per disinserire serve un codice" width="420">
</p>

## Per iniziare

Ti servono Home Assistant 2026.6 o successivo, un sensore di porta, finestra
o movimento che già funziona e un servizio `notify.*` funzionante. Nessun
account cloud, e nessun broker a meno che un tuo dispositivo parli MQTT.

1. In HACS aggiungi questo repository come *Repository personalizzato*,
   categoria *Integrazione*, installa *Foyer Home Defender* e riavvia Home
   Assistant.
2. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Foyer Home
   Defender*, e conferma gli stati in cui la prima zona conta come scattata.
3. Apri **Foyer** nella barra laterale: una procedura guidata di cinque passi
   completa la configurazione.

[Per iniziare](docs/getting-started.it.md) spiega l'installazione a mano, la
procedura guidata e i primi quindici minuti; [la card](docs/card.it.md) porta
l'allarme su una dashboard.

## La sicurezza in un paragrafo

I codici di Foyer proteggono da familiari, ospiti, personale delle pulizie,
utenti di Home Assistant non amministratori e chiunque trovi un tablet a muro
sbloccato. **Non** proteggono da un amministratore di Home Assistant, che può
leggere `.storage`, disattivare l'integrazione o chiamare direttamente
qualunque servizio — ed è anche per questo che il registro è utile come
traccia ma non inalterabile. Chi può avviare un walk test può tenere zitta una
casa inserita finché il test non finisce, quindi quel permesso si dà come si
dà *Disinserire*. Foyer non è un impianto d'allarme certificato, e non è un
sistema antincendio. [Il modello di sicurezza](docs/security-model.it.md) dice
il resto.

## Documentazione

| | |
|---|---|
| [Per iniziare](docs/getting-started.it.md) | Installazione, procedura guidata, i primi quindici minuti, la Panoramica |
| [Zone, aree e scenari](docs/zones.it.md) | Stati di scatto, contatti NC e NA, ritardi, politiche di inserimento, gruppi di verifica, il canale tecnico |
| [Profili di risposta](docs/response-profiles.it.md) | Cosa succede, quando, e perché ha suonato |
| [Canali di notifica](docs/notification-channels.md) | Ricette, dall'app Companion a un modem GSM (in inglese) |
| [Modello di sicurezza](docs/security-model.it.md) | Da cosa proteggono i codici, e da cosa no |
| [Simulatore](docs/simulator.md) | Diagnostica, simulatore, walk test e prova delle azioni (in inglese) |
| [Tutti i documenti](docs/README.it.md) | Tastierini, regole automatiche, stato del sistema, resilienza, privacy, impostazioni, la card, risoluzione dei problemi, domande frequenti… |

I documenti scritti prima di questa versione — tastierini, canali di notifica,
regole automatiche, privacy, resilienza, simulatore, stato del sistema — sono
in inglese; tutti gli altri sono in entrambe le lingue.

## Stato

Beta. Foyer è scritto da un solo autore, e ogni versione è una release GitHub
ordinaria che HACS propone per numero di versione. La configurazione salvata
porta la versione del suo schema e viene migrata in avanti a ogni
aggiornamento, e il [changelog](CHANGELOG.md) dice, versione per versione,
cosa è cambiato nel comportamento.

## Contribuire, sicurezza, licenza

Issue e pull request sono benvenute, in italiano o in inglese;
[CONTRIBUTING.md](CONTRIBUTING.md) spiega come si prepara l'ambiente di
sviluppo e l'unica regola che non si piega mai, e aggiungere una lingua non
tocca il codice. Un problema di sicurezza va in un
[advisory privato](https://github.com/foyer-labs/Foyer-Home-Defender/security/advisories/new),
non in una issue — vedi [SECURITY.md](SECURITY.md).

<p align="center">
  <a href="https://www.buymeacoffee.com/foyerlabs" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-green.png" alt="Buy Me a Coffee" height="60"></a>
</p>

Apache-2.0. Vedi [LICENSE](LICENSE) e [NOTICE](NOTICE).
