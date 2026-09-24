# Documentazione

[English](README.md) · **Italiano**

Tutti i documenti sull'uso di Foyer Home Defender, una riga ciascuno, con la
pagina del pannello il cui link *Approfondisci* li apre. Il progetto vero e
proprio, con le ragioni dietro ogni decisione, è in [SPEC.md](SPEC.md)
(in inglese).

## Per cominciare

| Documento | Di cosa parla | Pagina del pannello |
|---|---|---|
| [Per iniziare](getting-started.it.md) | Requisiti, installazione, la configurazione iniziale, la procedura guidata del primo avvio, i primi quindici minuti, la Panoramica | *Panoramica* |
| [La card](card.it.md) | `foyer-card`: i suoi quattro layout, come chiede un codice, cosa mostra durante un ritardo, un allarme e un walk test | — |
| [Domande che vengono fatte](faq.it.md) | Chi può disinserire, le card di Home Assistant e gli assistenti vocali, l'amministratore senza codice, funzionare senza internet | — |
| [Passare da Alarmo](migrating-from-alarmo.it.md) | Cosa converte l'importatore, cosa non può convertire, e cosa controllare dopo | — |

## Configurarlo

| Documento | Di cosa parla | Pagina del pannello |
|---|---|---|
| [Zone, aree e scenari](zones.it.md) | Tipi di zona, trigger, contatti NC e NA, ritardi, regole all'inserimento, esclusioni, supervisione, il canale tecnico, il campanello, i gruppi di verifica | *Aree*, *Zone*, *Scenari*, *Gruppi di verifica* |
| [Profili di risposta](response-profiles.it.md) | Quale profilo risponde, momenti, incidenti, azioni, condizioni, template, immagini, escalation | *Profili di risposta* |
| [Canali di notifica](notification-channels.md) (in inglese) | Ricette: app Companion, Pushover, SMS e chiamate con Twilio, un modem GSM, Telegram, Signal; rispondere a un codice di coercizione | *Contatti* |
| [Modello di sicurezza](security-model.it.md) | Da cosa proteggono i codici e da cosa no, i permessi, il codice di coercizione, le credenziali, cosa può fare un amministratore | *Utenti* |
| [Tastierini, tag e telecomandi](keypads.md) (in inglese) | I contratti del servizio, MQTT e HTTP, i dispositivi API, gli adattatori inclusi, l'hardware | *Dispositivi di inserimento*, *API* |
| [Regole automatiche](automation-rules.md) (in inglese) | Inserire in base a presenza, orario o un'entità; condizioni di sicurezza, sospensioni, e perché il disinserimento automatico è limitato | *Regole automatiche* |
| [Impostazioni](settings.it.md) | Valori predefiniti globali, il registro, backup e ripristino, la lingua dei messaggi, la rimozione dell'integrazione | *Impostazioni* |

## Verificarlo, e conviverci

| Documento | Di cosa parla | Pagina del pannello |
|---|---|---|
| [Simulatore](simulator.md) (in inglese) | La diagnostica, il simulatore e la traccia delle sue decisioni, il walk test, la prova delle azioni | *Test e diagnostica* |
| [Stato del sistema](system-health.md) (in inglese) | Alimentazione di rete, canali di notifica, il watchdog esterno, le interferenze radio, le segnalazioni da riparare, la diagnostica | *Stato del sistema* |
| [Resilienza](resilience.md) (in inglese) | Cosa sopravvive a un blackout o alla fibra tagliata, e le quattro cose che aiutano | — |
| [Privacy](privacy.md) (in inglese) | Cosa contiene il registro, l'esenzione domestica e dove finisce, cancellare ed esportare i dati di una persona | *Registro* |
| [Risoluzione dei problemi](troubleshooting.it.md) | Una zona che non scatta mai, i falsi allarmi, i guasti, i rifiuti che si incontrano, aprire una segnalazione a cui si possa rispondere | — |

## Hardware

| Documento | Di cosa parla |
|---|---|
| [Scegliere i sensori](choosing-sensors.it.md) | Cosa rende un sensore adatto a un antifurto e non solo all'automazione |
| [Riusare i sensori di un antifurto esistente](reusing-existing-sensors.it.md) | Portare in Home Assistant i sensori di un antifurto esistente, e le avvertenze |

## Il progetto

| Documento | Di cosa parla |
|---|---|
| [Identità visiva](brand.it.md) | Il marchio, la palette, i file |
| [Contratto API](api/openapi.yaml) · [Contratto MQTT](api/asyncapi.yaml) (in inglese) | L'endpoint per i dispositivi e i messaggi MQTT, versione v1 |
| [Contribuire](../CONTRIBUTING.md) · [Politica di sicurezza](../SECURITY.md) · [Changelog](../CHANGELOG.md) (in inglese) | Come contribuire, come segnalare una vulnerabilità, cosa è cambiato in ogni versione |

I documenti scritti prima della versione 0.1.0-beta.23 (canali di notifica,
tastierini, regole automatiche, privacy, resilienza, simulatore, stato del
sistema) sono solo in inglese; gli altri sono in inglese e in italiano.
