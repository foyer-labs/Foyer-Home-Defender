# Impostazioni

[English](settings.md) · **Italiano**

La pagina *Impostazioni* raccoglie ciò che vale per tutta l'installazione e non
per una singola area, zona o persona: i valori da cui parte ogni area, il punto
in cui finisce ogni risposta, il campanello, cosa conserva il registro, i dati
personali nel registro, il backup della configurazione, l'importatore e la
lingua in cui Foyer scrive i suoi messaggi. Questo documento percorre la pagina
nell'ordine in cui la mostra il pannello e, per ogni impostazione, dice cosa
cambia se la cambi, il valore predefinito, i limiti e dove trovare i dettagli.
È per chi ha `edit_config`, che serve per ogni salvataggio in questa pagina,
insieme a un codice ogni volta che la politica ne chiede uno per modificare la
configurazione — e per impostazione predefinita lo chiede.

Quasi tutti i campi si salvano appena ne esci, e ogni salvataggio ricarica
l'integrazione; l'unico blocco con i suoi pulsanti *Salva* e *Annulla* è il
campanello. Un salvataggio rifiutato viene spiegato sotto la sua scheda, e il
campo torna al valore salvato.

Due cose non sono in questa pagina, anche se sono globali. La politica dei
codici, la lunghezza del codice e il blocco stanno nella pagina *Utenti*,
accanto alle persone a cui si applicano; li spiega
[il modello di sicurezza](security-model.it.md). La rete elettrica, il
watchdog, i controlli dei canali e le radio stanno in *Stato del sistema*;
vedi [system-health.md](system-health.md) (in inglese).

---

## Mentre un'area è inserita

Una casa inserita tiene la risposta e i codici con cui è stata inserita.
Finché un'area qualsiasi non è disinserita — inserita, in inserimento, nel suo
ritardo d'ingresso o in allarme — una modifica che cambierebbe il modo in cui
la casa risponde a un allarme, o ciò per cui chiede un codice, viene rifiutata
spiegando perché. Altrimenti chi ha `edit_config` potrebbe abbassare la guardia
di una casa che nessuno ha disinserito, e nel registro niente sembrerebbe un
disinserimento.

Ogni impostazione globale sta da una parte o dall'altra di questa linea, e un
test fallisce se ne arriva una nuova che non sta in nessuna delle due: così
un'impostazione aggiunta più avanti non può finire dalla parte libera solo
perché nessuno ci ha pensato.

| Resta com'è finché tutte le aree non sono disinserite | Libera in qualsiasi momento |
|---|---|
| *Durata delle sirene*, *Attendi la chiusura al massimo*, *Ritardo d'ingresso predefinito*, *Ritardo d'uscita predefinito*, *Timeout del walk test* | *Batteria scarica sotto* |
| *Profilo predefinito*, *Profilo tecnico*, *Una zona silenziosa sopprime*, *Cartella telecamere* | Il campanello, tutto |
| La politica dei codici, la lunghezza del codice e il blocco (pagina *Utenti*) | Il registro: categorie, conservazione, la riduzione rapida |
| Se una regola automatica può disinserire (pagina *Regole automatiche*) | I dati personali nel registro, compreso l'interruttore per la disinstallazione |
| Le radio e le soglie di interferenza (pagina *Stato del sistema*) | *Lingua dei messaggi* |
| | Lo scaricamento del backup |
| | Se la procedura guidata iniziale è conclusa |

Le due schede con campi bloccati lo dicono in alto finché un'area è inserita.
Le pagine *Regole automatiche*, *Utenti* e *Stato del sistema* contengono le
altre, e le rifiutano allo stesso modo. Restano bloccati anche i profili con
cui un'area inserita potrebbe rispondere, e i contatti che nominano;
[response-profiles.it.md](response-profiles.it.md) dice quali.

---

## Valori predefiniti

*Con cosa partono le aree nuove, e i limiti che valgono per tutte.*

| Impostazione | Predefinito | Limiti | Da inserito |
|---|---|---|---|
| *Durata delle sirene* | 180 s | 1–900 s | bloccata |
| *Attendi la chiusura al massimo* | 300 s | 60–1800 s | bloccata |
| *Ritardo d'ingresso predefinito* | 30 s | 0–300 s nel pannello | bloccata |
| *Ritardo d'uscita predefinito* | 30 s | 0–300 s nel pannello | bloccata |
| *Batteria scarica sotto* | 20 % | 1–100 % | libera |
| *Timeout del walk test* | 900 s | 60–3600 s | bloccata |

**Durata delle sirene** è il tempo di taglio della sirena: per quanto un'area
resta in allarme prima che i suoi dispositivi sonori si fermino e l'area torni
allo stato in cui era prima dell'allarme. Il tetto di 900 secondi è il
riferimento EN 50131 per le sirene esterne, e nessun valore superiore viene
accettato. Uno scenario può impostare un tempo suo, più breve o più lungo,
entro lo stesso limite — è ragionevole che uno scenario notturno suoni meno di
uno diurno — e un disinserimento ferma le sirene prima. Dopo il taglio la
memoria d'allarme resta finché l'area non viene disinserita o inserita di
nuovo.

**Attendi la chiusura al massimo** vale solo per le zone con politica di
inserimento *Inserisci dopo la chiusura*: per quanto, dopo il ritardo d'uscita,
una zona del genere può restare aperta prima che l'inserimento fallisca come se
la zona l'avesse bloccato. Una zona può avere un valore suo; questo è quello
che usa quando non ce l'ha. Vedi [zone](zones.it.md).

**Ritardo d'ingresso predefinito** e **Ritardo d'uscita predefinito** sono i
ritardi che il backend dà a un'area salvata senza ritardi propri. La pagina
*Aree* non ne manda mai una così: fa partire ogni nuova area da 30 s per
entrambi, qualunque cosa dicano queste impostazioni, quindi i ritardi di una
nuova area impostali lì. Il pannello offre 0–300 s per entrambi; i ritardi di
ogni area vengono tenuti entro 0–300 s al salvataggio. Le aree esistenti
tengono i loro; una zona può sovrascrivere il ritardo d'ingresso e uno scenario quello
d'uscita. Vedi [zone](zones.it.md).

**Batteria scarica sotto** decide quando un'entità batteria numerica è
considerata scarica. Una batteria scarica avvisa e non blocca mai
l'inserimento, ed è per questo che questa impostazione resta libera anche da
inserito; un `binary_sensor` di batteria si legge invece dal suo `on`. Vedi
[simulator.md](simulator.md#batteries) (in inglese).

**Timeout del walk test** è per quanto un walk test resta attivo senza
rilevazioni prima di chiudersi da solo. Ogni rilevazione lo rimanda, e un
tetto di tre ore dall'inizio lo chiude comunque. La chiusura automatica è
obbligatoria, quindi nessun valore qui la disattiva. Resta bloccato da inserito
perché un walk test zittisce anche le aree che ha inserito qualcun altro. Vedi
[simulator.md](simulator.md#walk-test--which-zones-never-saw-you).

---

## Risposta

*Dove finisce ogni catena di ereditarietà, e cosa tace in una zona silenziosa.*
Tutto ciò che sta in questa scheda resta bloccato mentre un'area è inserita.

- **Profilo predefinito** — ciò che ogni area, zona e scenario eredita se non
  lo sovrascrive, e l'unico profilo che risponde a un momento che non
  appartiene a nessuna area, come l'uso di un codice di coercizione.
  Un'installazione nuova ne ha già uno, creato quando si configura Foyer.
- **Profilo tecnico** — ciò con cui rispondono le zone fumo, gas e allagamento
  che non hanno un profilo proprio, qualunque cosa stia facendo la casa: un
  rilevatore non deve rispondere in modo diverso a seconda di come è inserita
  la casa. Se è vuoto, risponde il profilo predefinito.
- **Cartella telecamere** — dove vengono scritti gli scatti e le registrazioni
  delle telecamere, relativa alla cartella di configurazione, `media/foyer` per
  impostazione predefinita. Un percorso assoluto, `..` e qualsiasi cartella
  dentro `www` vengono rifiutati, perché Home Assistant serve `www` senza
  autenticazione e l'interno di una casa non è una cosa da pubblicare. La
  cartella deve anche stare negli `allowlist_external_dirs` di Home Assistant,
  altrimenti lì non si può scrivere niente.
- **Una zona silenziosa sopprime** — i tipi di azione senza i quali una zona
  marcata silenziosa esegue la sua risposta: per impostazione predefinita
  *Sirena*, *Messaggio parlato* e *Campanello*, ma si può scegliere qualsiasi
  tipo di azione. Il silenzio appartiene alla zona; un'altra zona che entra
  nello stesso incidente suona comunque.

La catena di ereditarietà, la lista del silenzio e le telecamere sono spiegate
in [response-profiles.it.md](response-profiles.it.md).

---

## Campanello

*Suona quando si apre una zona con il campanello attivo mentre la sua area non
è inserita* — area per area, quindi con il solo perimetro inserito una porta
interna suona comunque. Tutto il blocco è libero anche da inserito, e si salva
con il suo pulsante *Salva*.

- **Suona su** — media player, sirene, e servizi o entità `notify`. Nessun
  campanello suona finché non ne spunti almeno uno. Ogni destinazione può avere
  il suo *Silenzio dalle* / *alle*, che per quella destinazione sostituisce la
  fascia globale.
- **Modalità** — *Suono singolo*, oppure *Pronuncia il nome della zona*
  tramite l'entità di *Sintesi vocale* scelta accanto. Con il suono singolo,
  *Contenuto da riprodurre* è ciò che riproduce un media player. In entrambe le
  modalità, una sirena suona per un secondo se supporta una durata impostata, altrimenti viene
  saltata.
- **Volume** — in percentuale, 0–100. Vuoto lascia il volume del lettore
  com'è.
- **Silenzio dalle** / **alle** — nessun campanello dentro questa fascia, che
  può attraversare la mezzanotte. Vuoto: mai silenzio.
- **Anche durante il ritardo d'uscita** — disattivato per impostazione
  predefinita, così la porta da cui esci non suona mentre la sua area conta
  alla rovescia.

Ogni zona ha il suo interruttore del campanello, e `switch.foyer_chime` zittisce
il campanello senza toccare queste impostazioni. Durante un walk test nessuna
zona suona. Vedi [zone](zones.it.md).

---

## Registro eventi

*Quali categorie vengono registrate, e per quanto ciascuna viene conservata.*
Libero anche da inserito.

Ognuna delle otto categorie — *Inserimento*, *Allarme*, *Azione*,
*Configurazione*, *Sicurezza*, *Sistema*, *Attività zone (inserito)*,
*Attività zone (disinserito)* — ha un interruttore e una conservazione in
giorni: 30 per impostazione predefinita, da 1 a 3650. Ogni categoria è attiva
per impostazione predefinita tranne *Attività zone (disinserito)*, che un PIR
in soggiorno riempie di migliaia di righe al giorno; attivala mentre cerchi un
problema e poi spegnila di nuovo.

Una categoria disattivata da quel momento non scrive più niente. Le righe che
ha già scritto restano finché non scadono i loro giorni. Disattivare
*Sicurezza* ha una conseguenza che vale la pena leggere prima di farlo: i
codici sbagliati, i blocchi e i codici di coercizione non vengono più
registrati, e per loro non parte nessun `foyer_event`, quindi un'automazione
che risponde a un codice di coercizione smette di sentirlo. Il profilo
predefinito gli risponde comunque.

**Accorcia a 7 giorni** porta *Inserimento*, *Allarme*, *Azione*, *Sicurezza* e
*Configurazione* a sette giorni e lascia stare le altre tre. È pensato per le
case con personale domestico: quelle sono le categorie che nominano persone,
mentre le altre portano guasti e stati delle porte, che non nominano nessuno e
sono quello che si legge quando un sensore non ha reagito tre settimane fa.
Vedi [privacy.md](privacy.md#keep-less-retention-and-the-short-preset) (in
inglese).

---

## Dati personali nel registro

Due impostazioni dell'installazione; cancellare o esportare le righe di una
singola persona si fa dalla pagina *Registro*. Libere anche da inserito. Vedi
[privacy.md](privacy.md) (in inglese).

- **Sostituisci i nomi nelle righe più vecchie** — disattivato per
  impostazione predefinita. Se lo attivi, le righe più vecchie del numero di
  giorni scelto (da 1 a 365, si parte da 30) tengono un identificatore stabile
  invece di un nome. In cambio si rinuncia, per ognuna di quelle righe, alla
  risposta a «chi ha disinserito quella notte», che è proprio la domanda per
  cui il registro esiste, e non si torna indietro: disattivarlo non riporta
  nessun nome. Il pannello chiede conferma prima di attivarlo, perché la prima
  passata gira al prossimo avvio, e salvare una qualsiasi impostazione è un
  avvio. L'attivazione e la disattivazione vengono registrate entrambe. Vedi
  [privacy.md](privacy.md#or-let-it-happen-by-itself-timed-pseudonymisation).
- **Cancella il database del registro se Foyer viene rimosso** — disattivato
  per impostazione predefinita. Vedi
  [Rimuovere l'integrazione](#rimuovere-lintegrazione) più sotto.

---

## Backup della configurazione

*Nessuno che abbia configurato quaranta zone lo rifarà una seconda volta.*

**Esporta JSON** scarica tutta la configurazione in un unico file. Non viene
mai rifiutato perché un'area è inserita; chiede `edit_config` e il codice, come
ogni comando di configurazione. Il file porta con sé la versione di schema con
cui è stato scritto, e la scheda mostra la versione della configurazione
salvata adesso.

Un backup non contiene mai una credenziale. I codici e i codici di coercizione
restano fuori, né come hash né in altra forma; lo stesso vale per il token di
un tastierino, l'indirizzo del webhook per la presa d'atto e l'URL del
watchdog. Un backup è un file che esce dalla macchina, e un hash di codice lì
dentro sarebbe un esercizio di indovinare fatto offline. Porta invece
l'identificatore di pseudonimizzazione di ogni persona, così un ripristino non
stacca le righe già pseudonimizzate; e non porta il registro.

**Ripristina da un file…** sostituisce la configurazione con quella del file:

- Un file di uno schema più vecchio viene aggiornato con gli stessi passi che
  usa un aggiornamento vero. Uno scritto da una versione maggiore più recente
  viene rifiutato invece di essere letto a metà.
- Poi passa dalla stessa validazione di ogni modifica e, mentre un'area è
  inserita, viene rifiutato esattamente dove lo sarebbe la stessa modifica
  fatta da sola nella sua pagina.
- Un ripristino che aggiunge, toglie o cambia una persona, un tag, la persona
  per cui agisce un interruttore a chiave, o le persone che possono usare uno
  scenario, richiede `manage_users` oltre a `edit_config`. Altrimenti
  `edit_config` sarebbe un modo per darsi tutti i permessi, o la chiave di
  qualcun altro.
- Le credenziali restano quelle dell'installazione, perché niente in un file
  può impostarne una. Una persona già presente con lo stesso id tiene i suoi
  codici; una persona nuova per questa installazione arriva senza. Un
  tastierino sull'endpoint dei dispositivi già presente tiene il suo token;
  ogni altro aspetta che gliene venga generato uno in *Dispositivi di
  inserimento*. Il webhook e l'URL del watchdog restano come sono, e un
  watchdog che nel file risulta attivo torna attivo solo quando c'è un URL
  salvato.
- Una zona che questa installazione tiene con la condizione di scatto non
  confermata resta non confermata, a meno che il file non ne cambi la
  condizione di scatto: modificare un file perché dica `true` non è qualcuno
  che controlla il sensore.

Lo stesso export e lo stesso ripristino sono i servizi `foyer.export_config` e
`foyer.import_config`, con gli stessi controlli.

**La mia configurazione sopravvive a un aggiornamento?** Sì. La configurazione
salvata è versionata e migrata un passo alla volta durante l'aggiornamento, e
ogni voce del changelog dice se lo schema si è mosso. Tornare *indietro*
attraverso un cambio di schema maggiore viene rifiutato apposta, invece di
essere letto a metà: una versione più vecchia che ignorasse in silenzio ciò che
non capisce potrebbe smettere in silenzio di proteggere qualcosa.

---

## Importa da Alarmo

Legge la configurazione di Alarmo da questo Home Assistant e porta le sue aree,
i sensori, le modalità e le persone accanto a ciò che c'è già. **Leggi da
Alarmo** mostra cosa creerebbe e tutto ciò che non è riuscito a portare;
niente viene scritto finché non premi **Applica**. Le zone arrivano spente
finché non confermi la condizione di scatto di ognuna nella pagina *Zone*, e
nessuno arriva con un codice. L'applicazione passa dalla stessa validazione e
dallo stesso rifiuto ad area inserita di un ripristino. Cosa converte, cosa
non può convertire e cosa controllare dopo è in
[migrating-from-alarmo.it.md](migrating-from-alarmo.it.md).

---

## Lingua dei messaggi

**Lingua dei messaggi** è la lingua di ciò che Foyer manda fuori: le parole che
scrive lui nelle notifiche, i loro pulsanti e le notifiche di Home Assistant
che mette su. Non è la lingua del pannello: il pannello segue quella di ogni
utente di Home Assistant, quindi un secondo selettore per il pannello sarebbe
una fabbrica di bug, mentre la casa ha una sola lingua per i suoi messaggi
anche quando il telefono che ne legge uno non ce l'ha. *Come Home Assistant*,
il valore predefinito, segue la lingua in cui gira Home Assistant, letta al
momento dell'invio. L'elenco contiene le lingue che Foyer include. Un messaggio
che hai scritto tu in un profilo di risposta viene mandato così come l'hai
scritto. Libera anche da inserito.

---

## Rimuovere l'integrazione

Rimuovere Foyer da *Dispositivi e servizi* porta via con sé la sua
configurazione, lo stato dell'allarme salvato, ogni entità e dispositivo che ha
creato, il pannello nella barra laterale, le sue segnalazioni di riparazione,
le notifiche che aveva messo su e il suo messaggio MQTT conservato sul broker —
un messaggio conservato sopravvive all'integrazione e continuerebbe a
raccontare a chiunque si colleghi dopo a quel broker cosa stava facendo la
casa.

Il database del registro eventi se ne va solo se lo hai detto prima, con
**Cancella il database del registro se Foyer viene rimosso** in questa pagina,
disattivato per impostazione predefinita. La conferma di Home Assistant è
l'ultima finestra che c'è, quindi la domanda si fa prima, e tenere è la
risposta che non può distruggere qualcosa che nessuno voleva distruggere. Se
resta disattivato, il file rimane nella cartella di configurazione come
`foyer-log.db`.

Gli scatti delle telecamere non vengono mai cancellati. Sono fotografie
dell'interno della casa, in una cartella che hai scelto tu e che può contenere
file che non sono mai stati di Foyer, quindi rimuoverli sta a te.
[privacy.md](privacy.md#when-foyer-is-removed) (in inglese) ha i dettagli.

---

## La procedura guidata iniziale

Se la procedura guidata iniziale è conclusa è un dato salvato insieme a queste
impostazioni, ma non è un campo di questa pagina. Lo imposta la procedura
stessa quando è finita o quando la chiudi, e appartiene all'installazione, non
a chi apre il pannello. È libero anche da inserito. Vedi
[getting-started.it.md](getting-started.it.md).

---

## Non ancora trattato qui

- Schermate della pagina.
- I campi della pagina *Utenti* per la politica dei codici, la lunghezza del
  codice e il blocco, oltre al rimando qui sopra.
