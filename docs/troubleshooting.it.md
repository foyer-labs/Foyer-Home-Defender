# Risoluzione dei problemi

[English](troubleshooting.md) · **Italiano**

Questa pagina è per chi ha configurato Foyer e si è trovato davanti a qualcosa
che non si aspettava: una zona che resta muta, un allarme che nessuno ha
provocato, un inserimento o una modifica rifiutati, una notifica mai arrivata.
Per ogni caso dice cosa fa il software, perché, e come se ne esce. È costruita
dal changelog, dalle decisioni della [specifica](SPEC.md) (in inglese) nate da
problemi reali e dai rifiuti che il codice restituisce davvero — non da
segnalazioni raccolte sul campo.

La pagina del registro risponde alla maggior parte di queste domande prima di
questa pagina. Ogni rifiuto è una riga a sé, con il suo motivo e le zone che
l'hanno causato, perché «come mai ieri sera non si è inserito?» è una domanda
che la gente si fa.

---

## Una zona non scatta mai

Parti dagli **stati di scatto** della zona: gli stati in cui Foyer la considera
scattata, confermati da te nell'editor della zona sotto *Quando scatta questa
zona?*. Foyer non dà mai per scontato che `on` voglia dire allarme. Un contatto
magnetico normalmente chiuso (NC) legge `off` quando la porta è aperta, uno
normalmente aperto (NA) legge `on`, e una serratura legge `unlocked`; una zona
i cui stati di scatto indicano lo stato sbagliato non scatta mai, e niente
sembra fuori posto fino alla notte in cui conta. Apri *Test e diagnostica*,
apri la porta o passaci davanti, premi *Aggiorna* mentre il sensore è ancora
scattato — la tabella è un'istantanea e non si aggiorna da sola — e leggi la
colonna *Valutazione del trigger*
([come leggerla](simulator.md#diagnostics-am-i-looking-at-the-right-sensor),
in inglese). Se dice *Non scatterebbe* mentre la porta è aperta, gli stati di
scatto sono sbagliati: correggili nella pagina *Zone* e spunta di nuovo *Ho
verificato questi stati sul sensore reale*. L'editor della zona non cambia
l'entità di una zona esistente: per osservare un'altra entità, crea di nuovo la
zona e conferma allora i suoi stati di scatto.

Se gli stati di scatto sono giusti, scorri questo elenco.

- **L'entità è stata rinominata.** Una zona punta a un id di entità. Quando Home
  Assistant non ce l'ha più, *Test e diagnostica* elenca l'entità sopra la
  tabella, la sua riga dice *Entità inesistente*, e la zona è in guasto —
  *Guasto: non raggiungibile* — il che blocca l'inserimento della sua area.
  Foyer non segue una rinomina: ridai all'entità il suo vecchio id in Home
  Assistant, oppure elimina la zona e creala di nuovo sul nuovo id. Se la zona ha
  spuntato *Consenti l'inserimento anche in guasto*, l'area si inserisce lo
  stesso, e quella zona non sorveglia niente.
- **La zona è disattivata.** *Una zona disattivata viene ignorata del tutto*:
  la tabella la mostra come *Disattivata*. Le zone portate dall'importatore
  della pagina *Impostazioni* arrivano disattivate, segnate *Trigger da
  confermare* nella pagina *Zone*, perché i loro stati di scatto sono una
  proposta ricavata dal tipo di sensore e non qualcosa che qualcuno abbia
  verificato; non si possono attivare finché gli stati di scatto non sono
  confermati. Vedi
  [portare in Foyer una configurazione esistente](migrating-from-alarmo.it.md).
- **La sua area non la sta sorvegliando.** Una zona antintrusione dà l'allarme
  solo mentre la sua area è inserita. Un'area disinserita — compresa una
  lasciata fuori dallo scenario in corso e non inserita per conto suo — e
  un'area che sta ancora contando il suo ritardo d'uscita non sorvegliano le
  loro zone; lì una zona che si apre può solo
  suonare il campanello. Solo le zone con *Sempre attiva (24h)* spuntato — per
  impostazione predefinita le zone 24h, di manomissione e di panico — e le zone
  tecniche rispondono qualunque cosa stia facendo l'area.
- **Era già aperta.** Una zona che è scattata quando la sua area si inserisce
  non scatta finché non si chiude e si riapre: con *Se aperta all'inserimento*
  impostato su *Ignora*, «scatta la prossima volta che si apre». Lo stesso vale
  per la prima lettura di una zona nuova, che è il suo punto di partenza e non
  un evento: una zona salvata con la porta aperta, o un rilevatore salvato
  mentre rileva, dà l'allarme solo dopo essere tornata a riposo ed essere
  scattata di nuovo.
- **È esclusa.** Una zona esclusa non dà l'allarme. *Esclusa a mano* senza una
  durata dura finché l'area non viene disinserita; con una durata sopravvive al
  disinserimento e torna inclusa quando il tempo scade. Chiudere la zona non
  termina mai un'esclusione manuale — lo fa *Includi di nuovo*. Le zone escluse
  all'inserimento o da un inserimento forzato tornano sorvegliate appena si
  chiudono.
- **Le serve più di un'attivazione.** *Attivazioni necessarie* sopra 1 vuol
  dire che la zona non fa niente finché non è scattata quel numero di volte
  dentro la sua finestra, e un PIR tenuto su `on` conta una volta sola. Contano
  solo le attivazioni che darebbero subito l'allarme: la prima apertura di una
  zona ritardata avvia comunque il suo ritardo d'ingresso. Anche un gruppo di
  verifica con *I membri non producono nulla sotto la soglia* trattiene un
  membro, finché non rilevano dentro la finestra abbastanza membri da
  raggiungere la soglia.
- **È un evento o un tag.** Un'entità `event` ha bisogno del suo *Tipo di
  evento* — il pulsante che conta — e scatta solo a un nuovo evento di quel
  tipo; un `tag` scatta a ogni lettura e non prende un tipo. La tabella mostra
  *Solo alla lettura* per entrambi, perché una zona momentanea non è mai
  «aperta». Un'entità che torna da `unavailable` a un riavvio è Home Assistant
  che ripristina il suo ultimo evento, e non scatta.
- **Il sensore ha smesso di trasmettere e nessuno se n'è accorto.** Con
  *Limite di silenzio* vuoto — il valore predefinito — un sensore che smette di
  trasmettere senza che la sua integrazione lo segni come non disponibile
  continua a mostrare il suo ultimo stato, e Foyer non può distinguere «chiuso»
  da «sparito». Imposta il limite su ogni sensore che trasmette a intervalli
  regolari, più lungo del suo intervallo di trasmissione; superato quello, la
  zona è in guasto (*Guasto: muta da troppo tempo*). Lascialo spento per i
  sensori che trasmettono solo quando cambiano.

Per vedere se una zona si muove del tutto mentre la casa è disinserita, attiva
la categoria del registro *Attività zone (disinserito)* in *Impostazioni* per
il tempo che ti serve a guardare, poi spegnila: un sensore di movimento la
riempie con migliaia di righe al giorno. Il [simulatore](simulator.md) (in
inglese) prova cosa fa il motore con una zona; il walk test, nella stessa
pagina, dimostra che il sensore ti vede.

---

## Falsi allarmi

Leggi prima l'incidente nella pagina del registro: ogni zona che vi si è
aggiunta, nell'ordine in cui si è aggiunta, sotto un unico id di incidente.
Poi:

- **Un sensore solo non è una prova sufficiente.** *Attivazioni necessarie*
  sulla zona le fa aspettare più attivazioni dentro una finestra. Un gruppo di
  verifica nella pagina *Gruppi di verifica* conferma un allarme quando un
  certo numero dei suoi membri rileva dentro una finestra; per impostazione
  predefinita ogni membro dà comunque l'allarme da solo e il gruppo aggiunge la
  sua conferma, quindi la risposta graduata si ottiene dando ai membri un
  profilo di risposta più discreto di quello del gruppo. Con *I membri non
  producono nulla sotto la soglia*, un membro da solo non fa niente finché
  abbastanza altri membri sono leggibili e sorvegliati — nemmeno per un intruso
  vero visto da uno solo dei tanti sensori che funzionano, ed è per questo che
  è spento per impostazione predefinita. Quando restano troppo pochi membri in
  grado di contare, un membro da solo dà l'allarme per conto suo. La *Verifica
  incrociata* su
  una zona è lo stesso motore di un gruppo di due: registra la conferma e non
  zittisce nessuna delle due zone. Contano solo le attivazioni che darebbero
  subito l'allarme, quindi rientrare a casa attraverso il ritardo d'ingresso
  non soddisfa mai un gruppo.
- **Il sensore dell'ingresso è scattato mentre entravi.** Una zona *Percorso*
  eredita il ritardo d'ingresso solo se ce n'è uno in corso: quello della sua
  area, o uno aperto da una zona ritardata che le è stato detto di seguire in
  *Segue anche*. Quando la porta d'ingresso e il sensore dell'ingresso stanno
  in aree diverse, spunta lì la porta d'ingresso. Anche la sua area va
  disinserita, altrimenti il ritardo ereditato di quell'area finisce in un
  allarme. Prova il percorso nel simulatore prima di farci affidamento.
- **Il ritardo d'ingresso è troppo corto.** Un *Ritardo di ingresso* di zona
  lasciato vuoto eredita quello predefinito dell'area: 30 secondi se non lo
  cambi, al massimo 300. Una zona ritardata con ritardo 0 scatta subito.
- **Qualcuno ha inserito senza ritardo d'uscita.** `skip_exit_delay` su
  `foyer.arm` inserisce all'istante. Chi è ancora dentro si trova subito
  davanti zone inserite: la porta d'ingresso avvia il suo ritardo d'ingresso, e
  un sensore istantaneo nell'ingresso dà l'allarme. La riga *Inserito* registra
  che il ritardo d'uscita è stato saltato.
- **Una zona è stata riattivata mentre era scattata.** Solo la prima lettura di
  una zona nuova è un punto di partenza (e quella di una zona chiave, quando
  viene riattivata). Una zona che era in uso, è stata
  disattivata e poi riattivata mentre rilevava conta come scattata in quel
  momento — per una zona 24h, di manomissione, di panico o tecnica, è un
  allarme.
- **È stata cambiata la batteria di un sensore con antimanomissione.** Aprirne
  il guscio fa scattare il suo interruttore antimanomissione, e una zona
  *Manomissione* dà l'allarme qualunque cosa stia facendo la casa, anche
  disinserita. Disattiva quella zona nella pagina *Zone*, con la sua area
  disinserita, per tutto il tempo in cui il guscio resta aperto, e riattivala
  dopo.
- **Foyer si è riavviato.** Una zona che era chiusa quando Foyer si è fermato
  ed è aperta quando riparte si è aperta, per quanto il motore può sapere. La
  riga *Foyer non era in funzione* del registro dice da quando a quando la casa
  non è stata sorvegliata.
- **Un allarme senza nessuna zona.** Un'interferenza radio confermata con la
  casa inserita apre un incidente senza zone, perché non è stata una zona — è
  stata la radio. [Stato del sistema](system-health.md#radio-interference) (in
  inglese) spiega cosa conta e i quattro eventi ordinari che hanno esattamente
  lo stesso aspetto.

---

## Guasti: una zona che non si riesce a leggere

Una zona è in guasto quando la sua entità è `unavailable` o `unknown` o non
esiste, quando una condizione di scatto numerica legge qualcosa che non è un
numero, quando è rimasta muta oltre il suo *Limite di silenzio*, o quando la
sua entità della batteria non si riesce a leggere. Un'entità `event` o `tag`
che legge `unknown` semplicemente non è mai scattata, e non è un guasto;
`unavailable` invece lo è ancora. Un guasto non è mai «tutto
tranquillo»: blocca l'inserimento dell'area della zona, viene annunciato come
*Guasto di zona*, e *Test e diagnostica* mostra *Blocca: guasto*. Quando
l'entità stessa della zona è `unavailable` o `unknown` da due giorni (valore
predefinito), diventa anche una segnalazione di riparazione di Home Assistant;
un guasto per limite di silenzio, una lettura che non è un numero, un'entità
della batteria illeggibile o una zona già illeggibile all'avvio di Foyer non ne
aprono una.

- **Consenti l'inserimento anche in guasto**, sulla zona, lascia inserire la
  sua area comunque. Lascialo spento a meno che tu non sappia perché: quella
  zona allora non sorveglia niente mentre la casa crede di essere inserita.
  Esiste per il sensore di allagamento con la batteria scarica la mattina in
  cui parti.
- **Inserisci senza queste zone**, nella *Panoramica* o nella card, inserisce
  ed esclude le zone in guasto per questo inserimento. È un inserimento
  forzato: richiede il permesso `force_arm`, che una persona aggiunta nella
  pagina *Utenti* non ha all'inizio, un codice per impostazione predefinita, e
  ogni zona che esclude deve essere *Può essere esclusa*. Viene registrato come
  inserimento forzato.
- **Batterie.** L'entità della batteria di una zona viene letta in due modi,
  apposta. Una batteria scarica — sotto *Batteria scarica sotto*, 20 % per
  impostazione predefinita, o un `binary_sensor` di batteria che è `on` —
  avvisa e non blocca mai: l'inserimento va avanti e dice quali zone sono
  entrate in sorveglianza con una pila agli sgoccioli. Un'entità della batteria
  che non si riesce a leggere affatto è un guasto e blocca, perché un sensore di
  batteria che tace è una radio che tace.

Molte zone di una stessa radio che diventano non disponibili insieme sono un
evento della radio più che tanti guasti:
[Stato del sistema](system-health.md#radio-interference) (in inglese).

---

## Inserimento rifiutato

Ogni rifiuto dice il suo motivo, e quelli che riguardano le zone nominano le
zone. I testi qui sotto sono quelli del pannello; le finestre di Home
Assistant e una chiamata di servizio mostrano lo stesso motivo con parole
proprie.

| Cosa vedi | Cosa significa | Come se ne esce |
|---|---|---|
| *Inserimento non riuscito — ancora aperte: …* | È aperta una zona con *Se aperta all'inserimento* impostato su *Blocca l'inserimento* | Chiudila; oppure escludila prima; oppure *Inserisci senza queste zone*. *Escludi automaticamente* e *Ignora* non rifiutano mai; *Inserisci dopo la chiusura* aspetta |
| *Inserimento non riuscito: zona ancora aperta: …* | Una zona *Inserisci dopo la chiusura* è rimasta aperta oltre *Attendi la chiusura al massimo* (300 s per impostazione predefinita) dopo il ritardo d'uscita | Chiudila prima, o alza il limite |
| *Inserimento non riuscito — non rispondono: …* | Una zona in guasto | Vedi [Guasti](#guasti-una-zona-che-non-si-riesce-a-leggere) |
| *Impossibile forzare l'inserimento: queste zone non possono essere escluse: …* | Un inserimento forzato ha trovato una zona che non è *Può essere esclusa* | Chiudila o riparala |
| *Serve un codice.* | Lo chiede la politica dei codici, un'area o uno scenario; oppure lo scenario ha una lista *Chi può usarlo* e la richiesta non ha accertato nessuno — un inserimento senza codice, o uno `user_id` soltanto dichiarato — cosa che viene rifiutata finché qualcuno ha un codice, anche dove l'inserimento non chiede un codice | Digitalo: il pannello e la card lo chiedono da soli. Dalle card di Home Assistant, vedi più sotto |
| *Il codice non è corretto.* | Il codice non corrisponde a nessuno | Ridigitalo; ogni codice sbagliato conta per il blocco |
| *Troppi codici errati…* | Blocco in corso, vedi più sotto | Aspetta, o usa un altro canale |
| *Il tuo utente Foyer non ha il permesso per farlo.* | Alla persona manca il permesso (inserire, inserimento forzato, cambiare scenario…) | Spuntalo nella pagina *Utenti* |
| *Quel codice appartiene a un utente disattivato o fuori dal suo periodo di validità.* | Un codice ospite scaduto, o una persona disattivata | La pagina *Utenti* |
| *Non puoi agire su quell'area.* / *…usare quello scenario.* | Le aree o gli scenari della persona, o il *Chi può usarlo* dello scenario, la lasciano fuori | La pagina *Utenti* o *Scenari* |
| *È in corso un walk test. Terminalo, poi inserisci…* | L'inserimento viene rifiutato mentre è in corso un walk test: quando finisce disinserisce le aree che aveva inserito, e disferebbe il tuo | *Chiudi il walk test*, che per impostazione predefinita chiede un codice, poi inserisci. Quando finisce disinserisce le aree che il test aveva inserito, tranne un'area in allarme o rimasta con la memoria d'allarme per una zona 24h o di manomissione durante il test, che solo il disinserimento di una persona chiude, e lascia ogni altra area come l'ha trovata |
| *C'è un allarme in corso. Disinserisci prima di cambiare scenario.* | Si cambia scenario mentre un'area che toccherebbe è nel ritardo d'ingresso o in allarme | Disinserisci prima: cambiare scenario non zittisce mai un allarme |
| *Più scenari sono associati a questa modalità di inserimento…* | Due scenari condividono una modalità, quindi *Tutta la casa* non sa quale si intende | Inserisci lo scenario stesso, dal pannello, dalla card o da `select.foyer_scenario`. La pagina *Scenari* dice *Condivisa con un altro scenario* |
| *Lo stato attuale dell'area non lo consente…* | Già inserita, in inserimento o in allarme — oppure quello scenario è già in corso e non resta niente da inserire | Niente da fare |
| *Quel dispositivo non è fra i dispositivi di inserimento dell'impianto…* | Un `device_id` non dichiarato in *Dispositivi di inserimento* | Dichiaralo, vedi più sotto |
| *Foyer si stava ricaricando, quindi non è stato fatto nulla. Riprova.* | Ogni salvataggio della configurazione ricarica Foyer; la richiesta è arrivata nel mezzo | Riprova |

**Blocco.** Dopo cinque codici sbagliati entro 300 secondi, i codici da quel
canale vengono rifiutati per 300 secondi; ogni blocco successivo raddoppia,
fino a un'ora — o fino alla durata configurata, se è più lunga — e il raddoppio riparte da capo dopo un giorno senza blocchi.
Tutti e tre i numeri sono nella pagina *Utenti*. Un codice corretto interrompe
la serie di errori ma non un blocco già in corso. Ciò che viene bloccato è
circoscritto: il pannello, la card e i pannelli d'allarme di Home Assistant
condividono un solo contatore **per account di Home Assistant**, quindi un
account che tira a indovinare blocca sé stesso e nessun altro; le chiamate ai
servizi `foyer.*` hanno un contatore tutto loro per account, e le chiamate
senza un utente dietro, come le automazioni, ne condividono uno; un tastierino conta per dispositivo; l'endpoint dei dispositivi
conta un token mancante o sbagliato per indirizzo di provenienza, e un
dispositivo con il suo token giusto non viene mai rifiutato per il suo
indirizzo. Un **amministratore di Home Assistant non viene mai bloccato fuori
dal pannello, dalla card, dai pannelli d'allarme di Home Assistant o dai
servizi `foyer.*` chiamati dal suo account** — i tentativi vengono contati e
registrati, e l'account resta aperto — così nessuno può chiudersi fuori da
casa propria. La card dice fino a
quando; il pannello dice *I codici da questo account sono bloccati fino alle …*.

**Le card di Home Assistant rifiutano un inserimento senza codice.** Home
Assistant fa a Foyer una sola domanda, valida per tutti — per inserire serve un
codice? — e agisce in base alla risposta prima che Foyer veda chi sta
chiedendo. Foyer risponde sì finché la politica chiede un codice per inserire
e nessuno potrebbe usare *Non chiedere il codice dove questa persona è
identificata* — vale solo per una persona attiva, collegata a un account di
Home Assistant e dentro il suo periodo di validità; *Tutta la casa* risponde sì appena una modalità che può ancora
inserire ne chiede uno. Allora la finestra di Home Assistant e i pulsanti delle
card chiedono il codice, e una modalità che non ne chiede viene rifiutata da
Home Assistant finché non si digita un codice — anche da un'automazione, che
per questo inserisce con `foyer.arm`. Quando qualcuno può usare l'esenzione, quei pulsanti
smettono di chiederlo, e una persona a cui Foyer vuole chiedere un codice viene
rifiutata con *Per inserire serve un codice*, e le viene detto dove digitarlo:
la card di Foyer, il pannello di Foyer, o la card *Pannello degli Allarmi* di
Home Assistant finché il pannello è disinserito, che è l'unico momento in cui
quella card offre l'inserimento. Le [domande frequenti](faq.it.md) trattano per
intero le card di Home Assistant e gli assistenti vocali.

**Un dispositivo sconosciuto.** Ogni tastierino, tag e telecomando va
dichiarato in *Dispositivi di inserimento* prima di poter comandare qualcosa, e
un `device_id` che l'installazione non conosce viene rifiutato qualunque codice
porti — altrimenti chi chiama potrebbe inventarsi un nome di dispositivo nuovo
a ogni tentativo e non arrivare mai al blocco. Il rifiuto lascia una riga
*Dispositivo rifiutato* sotto *Sicurezza* e una notifica di Home Assistant,
*Foyer: dispositivo sconosciuto*. Un tastierino dichiarato sull'endpoint dei
dispositivi risponde solo lì: il suo nome via MQTT o in una chiamata di
servizio viene rifiutato allo stesso modo, e la notifica dice che il nome è
stato usato sulla strada sbagliata. Vedi [tastierini](keypads.md) (in inglese).

**«Come mai ieri sera non si è inserito?»** Filtra il registro su quella notte:

- *Inserimento rifiutato* sotto *Inserimento*, con il motivo e le zone, quando
  la richiesta è stata rifiutata nel momento in cui è stata fatta;
- *Inserimento fallito*, quando un inserimento accettato ha trovato una zona
  ancora aperta o in guasto alla fine del ritardo d'uscita; ogni volta che
  l'inserimento di una regola automatica è stato rifiutato per un motivo
  diverso dalla casa già inserita in quel modo, con il nome della regola; e
  quando un tag o una zona chiave non è riuscito a inserire;
- *Codice rifiutato* sotto *Sicurezza*, quando il rifiuto riguardava chi stava
  chiedendo — un codice sbagliato, un blocco, un permesso o un'area — con il
  motivo nel dettaglio della riga. Il suo esito dice *Codice errato* solo quando
  un codice è stato digitato ed era sbagliato; un codice che serviva e non è
  stato dato, un permesso, un periodo di validità, un'area o uno scenario
  dicono *Rifiutato*;
- *Azione automatica trattenuta* sotto *Sistema*, quando una regola automatica
  è stata fermata da uno dei suoi controlli di sicurezza, da una sospensione o
  dall'interruttore generale. Vedi
  [regole automatiche](automation-rules.md) (in inglese).

---

## Modifiche rifiutate mentre la casa è inserita

Finché un'area qualsiasi non è disinserita, la casa tiene ciò con cui è stata
inserita. Una modifica che cambierebbe come risponde a un allarme, o per cosa
chiede un codice, viene rifiutata e dice cosa ha toccato:

- le aree inserite, le loro zone e i loro gruppi di verifica, e lo scenario in
  corso;
- la durata della sirena, *Attendi la chiusura al massimo*, i ritardi
  d'ingresso e d'uscita predefiniti e il timeout del walk test;
- il profilo predefinito e quello tecnico, l'elenco delle zone silenziose e la
  cartella delle telecamere;
- ogni profilo di risposta con cui un'area inserita potrebbe rispondere, e ogni
  contatto che un profilo del genere nomina, che non si possono né modificare,
  né disattivare, né eliminare;
- la politica dei codici, la lunghezza del codice e il blocco, e per cosa
  un'area o uno scenario chiede un codice — comprese un'area disinserita e uno
  scenario non in corso, perché fanno parte di comandi che toccano l'area
  inserita;
- *Permetti alle regole di disinserire*, e le radio e le soglie in *Stato del
  sistema*.

Altrimenti chiunque abbia `edit_config` potrebbe abbassare la guardia di una
casa che nessuno ha disinserito, e niente nel registro sembrerebbe un
disinserimento. Un ripristino viene rifiutato esattamente dove verrebbe
rifiutata la stessa modifica fatta nella sua pagina.

Cosa resta libero: le persone, i loro codici, i permessi e l'esenzione, i tag,
i tastierini e i loro token, i dispositivi API, MQTT, il webhook per la presa
d'atto e le regole automatiche — togliere il codice a un ospite dall'altra
parte del mondo è la modifica di cui una casa inserita ha più bisogno — e poi
la lingua, il registro, il campanello, la soglia della batteria, lo scaricamento
del backup, la rete elettrica, il watchdog e i controlli dei canali. Un'area
disinserita si può programmare mentre le altre restano inserite, tranne per
cosa chiede un codice.

Fra le modifiche libere, una viene rifiutata: *Un'area è inserita e nessuno
resterebbe con un codice valido…* Senza un codice valido la politica si spegne
da sola, il che abbasserebbe la guardia per un'altra strada. Dai prima un
codice a qualcun altro, oppure disinserisci.

---

## Codici

**Non viene chiesto il codice a nessuno.** Finché nessuna persona attiva ha un
codice dentro il suo periodo di validità, la politica dei codici è inerte:
non si potrebbe verificare niente, quindi applicarla renderebbe solo impossibile
disinserire l'allarme. La *Panoramica* lo dice — chiunque abbia accesso a Home
Assistant può disinserire — e lo dice anche la pagina *Utenti*. Dura finché non
viene salvata la prima persona con un codice, e torna se l'unica persona che ne
ha uno viene disattivata o esce dal suo periodo di validità.

**Il codice viene chiesto a un amministratore.** Essere amministratore di Home
Assistant non identifica nessuno: il tablet a muro lasciato sbloccato è quasi
sempre collegato con un account amministratore. Quindi il pannello chiede il
codice a un amministratore dovunque lo chieda la politica, compreso il
salvataggio della configurazione. Ciò che un amministratore conserva è che i
codici sbagliati non lo bloccano mai fuori dal pannello, dalla card, dai
pannelli d'allarme di Home Assistant o dai servizi `foyer.*`. Un amministratore che non ha un codice, in
una casa dove altri ce l'hanno, o il cui utente Foyer è stato disattivato o è
scaduto, recupera l'accesso da **Impostazioni → Dispositivi e servizi → Foyer
Home Defender → Configura**: riattiva l'utente Foyer di quell'account, toglie il
suo periodo di validità e imposta un codice nuovo, oppure crea un utente con
tutti i permessi. Non è mai silenzioso: una riga nel registro, una notifica di
Home Assistant e un messaggio a ogni contatto attivo, ognuno con il nome dell'account.
Le [domande frequenti](faq.it.md) e il [modello di sicurezza](security-model.it.md)
dicono perché esiste e cosa non cambia.

**Un codice nuovo viene rifiutato perché già in uso.** I codici sono unici fra
tutte le persone, codici di coercizione compresi, così il registro può dire chi
ha agito. Il rifiuto non dice mai di chi sia il codice, e **conta come un codice
sbagliato** per il blocco del tuo account — altrimenti salvare una persona
diventerebbe un modo per provare codici sulla famiglia senza limiti. Proporre
uno dei due codici salvati di una persona come l'altro — il codice di
coercizione come nuovo codice ordinario, per esempio — viene rifiutato e
contato allo stesso modo.

**Ti viene richiesto un codice digitato un attimo fa.** Il pannello dimentica
un codice due minuti dopo l'ultimo uso, a ogni inserimento o disinserimento, e
quando si chiude; la card non ne conserva nessuno oltre il comando per cui è
stato digitato.

---

## Notifiche che non arrivano

- **Premi prima il pulsante di prova.** *Prova questo canale* nella pagina
  *Contatti* manda attraverso il canale salvato, come farebbe un allarme. Una
  prova che fallisce, o che non arriva mai, è la risposta, trovata prima della
  notte in cui conta.
- **Leggi il canale in Stato del sistema.** *In ordine*, *Mai usato*,
  *Servizio assente* o *Invii falliti*. Un canale su cui non è ancora stato
  mandato niente è *Mai usato*, non in ordine: solo un invio dimostra che
  consegna. Vedi
  [lo stato dei canali di notifica](system-health.md#notification-channel-health)
  (in inglese).
- **Controlla che qualcosa la mandi.** Il profilo predefinito di una nuova
  installazione risponde con una notifica di Home Assistant e nient'altro. Un
  messaggio sul telefono, e ogni passo dell'escalation, è un'azione notify
  aggiunta a un profilo di risposta per i momenti che ti interessano; la
  notifica di prova della procedura guidata non ne aggiunge nessuna.
- **Un'entità notify non è un servizio notify.** Un'entità prende un titolo e
  un messaggio e scarta tutto il resto — il pulsante per prendere atto, un
  avviso critico, un'immagine. Vedi
  [canali di notifica](notification-channels.md#a-notify-entity-is-not-a-notify-service)
  (in inglese).
- **Immagini.** Il *Come allegarla* della notifica indica il trasporto: l'app
  Companion scarica un link in diretta attraverso il proxy delle telecamere di
  Home Assistant; Telegram ha bisogno di un file, scritto nella *Cartella
  telecamere* (`media/foyer` per impostazione predefinita, mai `www`), che deve
  stare in `allowlist_external_dirs` altrimenti non viene scritto niente. Con
  *Le telecamere delle zone che hanno dato l'allarme*, le immagini partono
  solo a un allarme, mai quando parte un ritardo d'ingresso, e a un contatto
  solo su un canale push o di chat; *Sempre la stessa telecamera* allega la sua unica immagine alla
  notifica stessa, in qualunque momento l'azione venga eseguita. Una telecamera che non risponde costa la sua immagine,
  mai il testo.
- **Ore di silenzio.** Dentro le *Ore di silenzio* di un contatto passa solo
  ciò che raggiunge la *Gravità minima per passare*. La traccia del simulatore
  dice quando ogni contatto nominato da una notifica è stato trattenuto in
  questo modo.

---

## La card non compare nel selettore, o «Custom element doesn't exist»

Ricarica la pagina una volta con Ctrl+Maiusc+R (Cmd+Maiusc+R su Mac). Home
Assistant scrive il tag script della card dentro la pagina che genera: una
pagina caricata prima che Foyer fosse installato — o prima che fosse aggiornato
— non ce l'ha, e la riconnessione dopo un riavvio non ne scarica una nuova.
Nell'app per smartphone azzera la cache dell'interfaccia dalle sue
impostazioni, oppure chiudi e riapri l'app. Per verificare che il file ci sia,
apri `https://<il-tuo-home-assistant>/foyer_static/foyer-card.js`: deve
mostrare del JavaScript. Non serve aggiungere alcuna risorsa alla dashboard.
[La card](card.it.md) descrive il resto.

## HACS mostrava un commit invece di una versione

Fino alla `0.1.0-alpha.13` ogni versione era pubblicata come *pre-release* su
GitHub, e HACS offre solo le release che non sono pre-release: per un
repository che non ne ha nessuna ripiega sul ramo predefinito e mostra il
commit. Dalla `0.1.0-beta.1` le versioni sono pubblicate normalmente, quindi
HACS le vede, le mostra per nome e propone da solo gli aggiornamenti. Se avevi
abilitato l'entità *switch* «pre-release» che HACS crea per questo repository,
puoi disattivarla.

## La barra laterale mostra uno scudo semplice

È voluto: `mdi:shield-home`, perché Home Assistant risolve un'icona
personalizzata una volta sola e non riprova mai, e l'app per smartphone che
riparte da una pagina in cache resterebbe per sempre con un quadrato vuoto. Lo
scudo di Foyer è nell'intestazione del pannello; vedi [marchio](brand.it.md).

---

## Aprire una issue a cui si possa rispondere

Apri una [issue](https://github.com/foyer-labs/Foyer-Home-Defender/issues/new/choose):
il modulo chiede quanto segue e dice dove trovare ogni parte:

- **quale versione** di Foyer (in HACS) e di Home Assistant (*Impostazioni →
  Informazioni*);
- **cosa ti aspettavi**, e cosa è successo invece;
- **cosa mostra la pagina del registro** intorno a quel momento. La riga di
  solito contiene già la risposta — un rifiuto porta il suo motivo e le zone
  che l'hanno causato — quindi una schermata vale più di una descrizione. Per
  una zona che non scatta mai, aggiungi la sua riga in *Test e diagnostica*;
- **Scarica diagnostica**, da *Impostazioni → Dispositivi e servizi → Foyer
  Home Defender → ⋮*. Di solito trasforma cinque domande in una risposta. Porta
  la forma dell'impianto e niente sulle persone che ci abitano: nessun nome di
  persone, aree o zone, nessun codice o hash, nessun URL del watchdog, id del
  webhook o token di tastierino, nessun numero di telefono, id di chat, testo
  di messaggi o topic MQTT, e gli id reali delle entità sostituiti da
  segnaposto stabili come `binary_sensor.zone_3`. Non porta righe del registro
  né stati di scatto, ed è per questo che le due schermate qui sopra contano
  ancora. Se il pulsante manca perché Foyer non si è caricato, dillo: è il fatto
  più importante della segnalazione.

In italiano o in inglese, come preferisci.

Un modo per aggirare un codice, un modo per far restare zitto l'allarme, un
modo per leggere una credenziale o il registro di qualcun altro è una
vulnerabilità, non una issue: [SECURITY.md](../SECURITY.md) (in inglese) dice
come segnalarla in privato.
