<p align="center">
  <img src="https://raw.githubusercontent.com/foyer-labs/Foyer-Home-Defender/master/docs/logo/foyer-hd-app-192.png" alt="Foyer Home Defender" width="120">
</p>

<p align="center"><a href="https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/README.md">English</a> · <strong>Italiano</strong></p>

# Foyer Home Defender

Foyer Home Defender trasforma Home Assistant in un vero centralino antintrusione:
aree con il proprio stato di inserimento, scenari di inserimento definiti
dall'utente, semantica delle zone, un motore di risposta, utenti identificati,
tastiere fisiche, un registro eventi verificabile e un simulatore che permette
di controllare la configurazione prima di fidarsene.

> **Stato: Fase 1 in corso — il nucleo dell'allarme. Non ancora qualcosa su cui
> fare affidamento.** Aree, zone, scenari, gruppi di verifica e profili di
> risposta si configurano dal pannello nella barra laterale. La macchina a stati
> ha ritardi di uscita e di ingresso, zone istantanee, ritardate, seguistrada,
> 24h, antimanomissione e antirapina, politiche di inserimento, inserimento
> forzato, esclusione manuale e temporizzata di una zona, un tempo massimo di
> sirena con memoria d'allarme, e uno stato che sopravvive a un riavvio. Fumo,
> gas e acqua viaggiano su un canale proprio, che il disinserimento non può
> zittire. Un allarme ora fa suonare sirene, lampeggiare luci, registrare una
> telecamera e inviare notifiche. Ciò che manca conta: non c'è **nessun registro
> eventi**, quindi il pannello non sa ancora raccontarti cos'è successo stanotte;
> le notifiche vanno a un solo servizio e non scalano finché qualcuno non
> risponde; e non ci sono utenti né codici, quindi **chiunque possa raggiungere
> Home Assistant può disinserire l'allarme.**

Il progetto completo è in [docs/SPEC.md](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/docs/SPEC.md) (in inglese, come tutto il codice e la documentazione tecnica).

## Cosa esiste già, e cosa distingue Foyer

[Alarmo](https://github.com/nielsfaber/alarmo) è l'implementazione di
riferimento in questo campo, ed è fatta bene: modalità di inserimento, ritardi
per sensore, un motore di azioni, utenti con codice, MQTT e una card Lovelace.
Foyer è scritto da zero e non ne copia il codice. Punta a tre cose che Alarmo
non fa:

- **Scenari illimitati, definiti dall'utente.** Alarmo è legato alle quattro
  modalità fisse di Home Assistant. Le case vere hanno bisogno di "Notte, solo
  piano terra", "Solo garage", "Cane in casa".
- **Un simulatore e un walk test.** Rispondere a "cosa succederebbe se si
  aprisse la finestra della cucina adesso, in questo scenario, a quest'ora?"
  senza aprirla.
- **Escalation con presa in carico.** Notifiche che scalano fra canali e persone
  finché un essere umano non prende in carico l'allarme.

Nessuna di queste esiste ancora: arrivano nelle fasi successive (SPEC §16).

## Modello di sicurezza

I codici di Foyer proteggono da familiari, ospiti, addetti alle pulizie, utenti
non amministratori di Home Assistant e da chiunque trovi un tablet a muro
sbloccato. **Non** proteggono da un amministratore di Home Assistant, che può
leggere `.storage`, disattivare l'integrazione o chiamare qualsiasi servizio
direttamente. Foyer non è un sistema d'allarme certificato.

I codici arrivano nella Fase 2. Fino ad allora non c'è nulla che protegga da
nessuno.

**Foyer non è un sistema antincendio.** Un rivelatore di fumo collegato a Home
Assistant non sostituisce rivelatori certificati e interconnessi fra loro.

## Installazione (repository personalizzato HACS)

1. In HACS, apri il menu → *Repository personalizzati*, aggiungi l'URL di questo
   repository con categoria *Integrazione*.
2. Installa *Foyer Home Defender* e riavvia Home Assistant.
3. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Foyer Home
   Defender*. Dai un nome alla prima area e al primo scenario, scegli l'entità
   della prima zona, poi conferma gli stati in cui va considerata in allarme.
   Verificali sul sensore vero: apri la porta, passa davanti al sensore e guarda
   come cambia lo stato.
4. Nella barra laterale compare la voce **Foyer**. Le altre aree, zone e scenari
   si aggiungono da lì (solo amministratori). Per mettere la card in una
   dashboard, scegli *Foyer Home Defender* nel selettore delle card, oppure usa:

   ```yaml
   type: custom:foyer-card
   entity: alarm_control_panel.foyer_<area>   # oppure alarm_control_panel.foyer_master
   ```

   La card viene caricata da sola: non serve aggiungere nessuna risorsa alla
   dashboard.

Richiede Home Assistant 2025.1 o successivo.

## Sviluppo

Codice, entità, servizi, messaggi di commit e documentazione tecnica sono in
inglese; l'interfaccia è tradotta in italiano e in inglese fin dal primo giorno.

```
custom_components/foyer/   l'integrazione (HACS installa questa cartella così com'è)
  core/                    motore decisionale puro: mai un import di Home Assistant
  runtime/ entity/ api/    gli strati rivolti a Home Assistant
  store/                   persistenza in .storage e migrazioni di schema
  translations/            en.json, it.json (Home Assistant) e panel/ (UI, aiuto)
  frontend/                bundle di pannello e card già compilati, versionati
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
controllo fallisce, la cosa da correggere è il codice, mai il test.

Per aggiungere una lingua: copia `translations/en.json` e
`translations/panel/en.json` nel nuovo codice lingua, traduci e apri una pull
request. La CI fallisce se gli insiemi di chiavi non coincidono.

## Licenza

Apache-2.0. Vedi [LICENSE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/LICENSE) e [NOTICE](https://github.com/foyer-labs/Foyer-Home-Defender/blob/master/NOTICE).
