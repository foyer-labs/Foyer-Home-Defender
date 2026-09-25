# Il registro parla di persone

[English](privacy.md) · **Italiano**

*Informazioni pratiche, non consulenza legale.*

Il registro eventi di Foyer annota chi era in casa, quando è arrivato e quando
è uscito, per trenta giorni di serie. Sono dati personali di **tutti quelli che
vivono in casa**, non solo di chi ha installato l'impianto — e, prima o poi,
anche di persone che in casa non vivono affatto.

Questa pagina dice cosa c'è nel registro, dove smette di valere l'esenzione per
uso domestico, e cosa ti dà Foyer per farci qualcosa.

---

<a id="what-a-row-contains"></a>

## Cosa contiene una riga

Una riga per evento, nel database SQLite di Foyer — `foyer-log.db` nella
cartella di configurazione di Home Assistant. Di proposito non è il recorder,
la cui pulizia a dieci giorni distruggerebbe in silenzio un requisito di trenta.

| Colonna | Cosa dice |
|---|---|
| `ts` | quando, al millisecondo, in UTC |
| `category`, `event_type`, `severity`, `outcome` | cosa è successo, e se ha funzionato |
| `area_id`, `zone_id`, `scenario_id`, `incident_id` | dove, e a quale notte appartiene |
| `user_id`, `user_name` | **chi** |
| `channel`, `device_id` | **come** è arrivato: il tastierino dell'ingresso, un tag, l'app |
| `detail` | un piccolo documento JSON — quali zone, quale profilo, cosa ha cambiato una modifica della configurazione |

Due di queste dicono più di quanto sembri. `device_id` nomina il tastierino che
qualcuno ha usato, e nella maggior parte delle case una certa persona usa un
certo tastierino; `channel` distingue chi digita un codice alla porta da chi
disinserisce dal telefono a letto. Tutte e due diventano "chi" appena conosci la
famiglia, ed è per questo che cancellare una persona toglie anche quelle (più
sotto).

**`user_name` viene scritto in ogni riga di proposito.** Non è un riferimento
alla pagina degli utenti, è una copia del nome. È questo che rende sicuro
eliminare un utente — la storia di quello che ha fatto gli sopravvive — ed è
esattamente questo che rende la cancellazione un'operazione a sé e non un
effetto collaterale.

**Ogni riga finisce anche sul bus degli eventi di Home Assistant** come
`foyer_event`, così automazioni e raccoglitori di log esterni possono
iscriversi. Tutto quello che era in ascolto ha la sua copia, e niente di quello
che Foyer fa qui la raggiunge. Se inoltri `foyer_event` a qualcosa fuori casa,
quella copia la gestisci tu.

---

<a id="the-household-exemption-and-where-it-stops"></a>

## L'esenzione per uso domestico, e dove finisce

Nel GDPR (Regolamento generale sulla protezione dei dati), l'articolo 2,
paragrafo 2, lettera c) mette del tutto fuori dal regolamento i trattamenti
effettuati "per l'esercizio di attività a carattere esclusivamente personale o
domestico". Il registro dell'allarme di una famiglia, tenuto sul suo hardware e
letto da lei, sta dentro quell'esenzione. Nessuno deve fare niente.

**Smette di valere nel momento in cui il registro annota qualcun altro.** Non
quando lo pubblichi, non quando lo condividi — quando annota quella persona.

- La **persona delle pulizie** che viene il martedì, i cui arrivi e le cui
  uscite restano in archivio per un mese.
- Il **tecnico della caldaia** fatto entrare per una mattina, e il tag che è
  stato creato per lui.
- La **babysitter**, chi porta a spasso il cane, il vicino che annaffia le
  piante.

E non vale **per niente** per le installazioni che non sono una casa privata:

- un **B&B** o una **casa vacanze**, dove ogni ospite è un interessato e il
  registro annota quando degli sconosciuti sono entrati e usciti dalla loro
  stanza;
- un **piccolo ufficio**, un **negozio** o un **laboratorio**, dove il registro
  è un dato di presenza dei dipendenti — che in diversi paesi europei è
  regolato ben oltre il GDPR, da norme sul controllo delle persone al lavoro, e
  in Italia in particolare dall'articolo 4 dello Statuto dei lavoratori. Chiedi
  prima di installarlo, non dopo.

Quello che ne segue non è un banner di licenza. Sono tre cose pratiche: tenere
di meno, poter consegnare a qualcuno i suoi dati, e poterlo togliere.

---

<a id="keep-less-retention-and-the-short-preset"></a>

## Tenere di meno: la conservazione, e la scorciatoia breve

La conservazione è già per categoria, nella **pagina 11 — Impostazioni**: trenta
giorni ovunque di serie, con pulizia quotidiana.

Accanto a quei campi c'è un pulsante **accorcia a sette giorni**. Porta
`arming`, `alarm`, `action`, `security` e `config` a sette giorni — `action`
compresa, perché annota chi ha preso atto di un allarme — e **lascia stare le
altre tre**: `system` e le due categorie `zone_*` portano guasti, riavvii e
stati delle porte, che non nominano nessuno e sono quello che leggi quando vuoi
sapere perché un sensore non ha reagito tre settimane fa. Accorciarle non fa
guadagnare niente e fa perdere qualcosa di concreto.

Sette giorni è quello che di solito vuole un'installazione con personale
domestico: abbastanza per rispondere a "cos'è successo lo scorso fine
settimana", abbastanza poco perché gli spostamenti di nessuno restino in
archivio per un mese.

---

<a id="hand-somebody-their-own-data"></a>

## Consegnare a qualcuno i suoi dati

**Pagina 10 — Registro**, in fondo: scegli una persona ed esporta le sue righe
in CSV o JSON. Il file prende il suo nome, perché è un file che consegni a lei.

La selezione è volutamente **ampia**. Comprende:

- ogni riga in cui è lei ad agire (`user_id`),
- ogni riga che nomina un **tag suo** — una lettura rifiutata riguarda lei,
- ogni riga che nomina un **contatto collegato a lei** — un'escalation che l'ha
  raggiunta sul telefono riguarda lei.

Una richiesta di accesso dell'interessato riguarda i dati personali di
qualcuno, non le righe in cui la colonna `user_id` risulta coincidere; un
export che si fermasse alla prima di quelle tre sarebbe una risposta che lascia
fuori metà della persona.

**Esportare richiede il permesso `view_log`, e il riquadro in cui si trova
richiede `manage_users`** — il conteggio delle persone sopra i pulsanti fa parte
della cancellazione, che è competenza di `manage_users`. In pratica le due cose
le fa la stessa persona. Non c'è modo per qualcuno di scaricare le proprie righe
senza che gli sia affidato il registro, ed è un limite voluto, non una svista:
il registro è la documentazione di sicurezza di una casa, e aprirne la lettura a
chiunque ci compaia sarebbe un buco più grande di quello che chiude. In una
famiglia non è un problema — la richiesta si fa a chi ha configurato
l'impianto, che esporta il file e lo consegna. **In un B&B, in un affitto o in
un ufficio è un accordo che qualcuno deve prendere**, e prenderlo fa parte del
gestirne uno.

---

<a id="take-somebody-out"></a>

## Togliere qualcuno

Stessa pagina, stesso riquadro: **cancella la sua storia**.

*Non* è eliminare il suo account utente, e la differenza è tutto il punto.
Eliminare un utente toglie l'account e lascia la storia di quello che ha fatto,
perché `user_name` è stato copiato in ogni riga proprio per questo. Cancellare
la storia di una persona fa l'opposto: gli eventi restano esattamente dove sono,
e la persona ne esce.

Cosa fa a ognuna delle sue righe:

- `user_id`, `user_name`, `channel` e `device_id` vengono svuotati;
- il suo nome viene tolto dal documento `detail` di quelle righe ovunque
  compaia — come parola intera, così una persona che si chiama Ed non si porta
  via `added` ed `enabled`;
- una riga di configurazione che annota una modifica al *suo account* perde il
  collegamento a quell'account, ma conserva il nome di chi ha fatto la
  modifica. Quella riga è la documentazione di qualcun altro su quello che ha
  fatto, e una persona che chiede di essere dimenticata non chiede di svuotare
  la traccia di controllo di un'altra.

Cosa lascia intatto: l'ora, l'area, la zona, l'evento, l'incidente. **Il
registro risponde ancora a "cos'è successo la notte del quattordici" e non
risponde più a "chi".**

Due cose che non raggiunge, dette qui invece di lasciartele scoprire:

- **Un nome che qualcun altro ha messo nel nome di un oggetto.** Se un
  amministratore ha chiamato un tag "Il tag di Ana", la riga che annota *quella*
  modifica è dell'amministratore, non di Ana, e il suo testo resta. Rinomina
  l'oggetto e la riga successiva porta il nome nuovo; la riga vecchia è la
  storia di quello che ha fatto l'amministratore.
- **Una riga il cui account non è di Foyer.** La cancellazione cerca per account
  Foyer, per l'account Home Assistant collegato a esso, e per nome nelle righe
  che non portano nessun account. Chi compare nel registro solo con un account
  Home Assistant non collegato al suo utente Foyer non viene trovato —
  collega i due nella pagina 7 e lo sarà.

Prima di procedere, il pannello mostra quante righe ha trovato e con quale
chiave — il suo account, o solo il suo nome. Il secondo numero non è rumore: una
riga scritta prima che fosse un utente Foyer, o con un nome che nel frattempo ha
cambiato, porta il nome e un altro id, e cercare solo per account lascerebbe il
nome nelle righe più vecchie — quelle su cui è più probabile che qualcuno
faccia domande.

C'è una casella: **tieni un identificatore stabile invece di dimenticare**.
Spenta di serie. Accesa, le righe conservano un identificatore opaco
`person-…` che collega ancora le sue righe fra loro, così "la stessa persona ha
agito in tutte e due le notti" sopravvive. Questa è minimizzazione, non
cancellazione, e chi chiede di essere dimenticato di solito chiede l'altra.
Chiediglielo.

E sii onesto su cosa protegge l'identificatore. Da solo non dice niente, ma
**la tabella che lo riporta a un nome sta nella configurazione** — è un campo
di ogni persona, e viaggia nel backup della configurazione, così ripristinarne
uno non stacca tutte le righe già scritte. Quindi uno pseudonimo nasconde un
nome a chi legge il registro; non nasconde niente a chi può leggere `.storage` o
ha un backup, che è lo stesso confine che `docs/security-model.md` traccia
attorno a tutto il resto.

**La cancellazione viene a sua volta registrata**, sotto `config`, con chi l'ha
eseguita e quante righe ha toccato — e **senza nominare la persona**. (L'unico
caso in cui la riga porta il nome è quando qualcuno cancella sé stesso, perché
la riga nomina chi ha eseguito l'operazione.) Cancellare l'intero registro viene
registrato (§10.3) e così anche questo, ma una riga che registrasse una
cancellazione nominando la persona cancellata lascerebbe dietro di sé proprio
la cosa che le era stato chiesto di togliere.

Richiede il permesso `manage_users` e un codice.

---

<a id="or-let-it-happen-by-itself-timed-pseudonymisation"></a>

## Oppure lascia che succeda da sé: la pseudonimizzazione a tempo

**Pagina 11 — Impostazioni**, sotto *Dati personali nel registro*. Spenta di
serie.

Accesa con un ritardo di N giorni, una passata gira una volta al giorno — e una
volta a ogni avvio, perché un'installazione che si riavvia più spesso di una
volta al giorno altrimenti non la farebbe mai girare — e sostituisce il nome in
ogni riga più vecchia di N giorni con l'identificatore stabile di quella
persona, nelle colonne e dentro il dettaglio. Le righe più recenti di N giorni
restano intatte. Salvare una qualunque impostazione riavvia l'integrazione,
quindi la prima passata avviene pochi secondi dopo che l'hai accesa: il pannello
ti chiede di confermare prima di farlo.

**Leggi questo prima di accenderla.** Rinuncia alla possibilità di rispondere a
*"chi ha disinserito quella notte"* per ogni riga più vecchia del ritardo — che
è la domanda per cui il registro esiste, e il motivo per cui ogni persona in
questo impianto ha il suo codice invece di condividerne uno. È uno scambio vero,
non una funzione di sicurezza gratuita, e Foyer non la presenterà come tale.

È anche irreversibile. Spegnerla ferma la passata; non riporta indietro nessun
nome. Sia l'accensione sia lo spegnimento vengono registrati, con chi li ha
fatti.

Tre limiti da conoscere:

- Lavora a partire dalla **pagina degli utenti**: può sostituire un nome solo
  con l'identificatore di qualcuno che questa installazione ha ancora. Le righe
  che nominano una persona nel frattempo eliminata dalla configurazione
  conservano il nome. Se stai per eliminare qualcuno, cancella prima la sua
  storia — quell'operazione raggiunge quelle righe e questa no.
- Trova le stesse righe che trova la cancellazione, e manca le stesse: una
  persona il cui account Home Assistant non è collegato al suo utente Foyer
  nella pagina 7.
- Non raggiunge le copie che sono uscite. Tutto quello che si era iscritto a
  `foyer_event` ha tenuto quello che ha ricevuto.

---

<a id="what-a-backup-carries"></a>

## Cosa porta un backup

Il backup della configurazione nella pagina 11 porta l'**impostazione di
pseudonimizzazione** e l'identificatore di ogni persona, così ripristinare un
backup non spegne in silenzio la protezione, e non conia identificatori nuovi
che staccherebbero ogni riga già pseudonimizzata da ogni riga scritta dopo.

**Non** porta il registro. Niente di quello che fai qui può essere annullato
ripristinando un backup, ed è giusto così: una cancellazione che un ripristino
potesse annullare non sarebbe una cancellazione.

---

<a id="when-foyer-is-removed"></a>

## Quando Foyer viene rimosso

Nella pagina 11 c'è un ultimo interruttore: **cancella il database del registro
se Foyer viene rimosso**. Spento di serie.

Deve essere un interruttore e non una domanda fatta al momento, perché il
"sei sicuro?" di Home Assistant è l'ultima finestra di dialogo che c'è —
un'integrazione che viene rimossa non può mostrarne una sua. Quindi la domanda
si fa in anticipo, e per chi non ha mai risposto la risposta è *tieni*, perché
il §16 della specifica dice di chiedere invece di indovinare e tenere è la
risposta che non distrugge niente.

Se lo lasci spento, il file resta dov'era: `foyer-log.db` nella cartella di
configurazione, con i suoi compagni `-wal` e `-shm`. Cancellalo a mano quando
vuoi.

Cosa si porta via la rimozione in ogni caso: ogni entità e dispositivo dai
registri di Home Assistant, il pannello nella barra laterale, i problemi in
Riparazioni, le notifiche che Foyer aveva mostrato, e il **messaggio MQTT
retained** — un messaggio retained sopravvive all'integrazione che l'ha
pubblicato e continuerebbe a dire a chiunque si colleghi a quel broker dopo cosa
stava facendo la casa l'ultima volta che Foyer ha parlato.

Cosa **non** si porta via: le **istantanee delle telecamere**. Foyer le scrive di
serie sotto `media/foyer` — dentro la cartella multimediale di Home Assistant,
`/media` su Home Assistant OS — e sono fotografie dell'interno di una casa — l'unica
cosa in questa pagina che a nessuno viene in mente di cercare. La cartella è
configurabile, può puntare ovunque e può contenere file che non sono mai stati
di Foyer, quindi toglierli è lasciato a te. Vai a guardare.

---

<a id="what-foyers-log-is-not"></a>

## Cosa non è il registro di Foyer

È **utile per ricostruire, non a prova di manomissione**. Un amministratore di
Home Assistant con accesso al filesystem può cancellare il database e basta, e
niente qui lo cambia; `docs/security-model.md` lo dice più per esteso. Lo scopo
del registro è rispondere a domande oneste dopo i fatti, non sopravvivere a
qualcuno deciso a riscriverlo.
