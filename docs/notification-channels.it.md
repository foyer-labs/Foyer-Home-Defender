# Canali di notifica

[English](notification-channels.md) · **Italiano**

Ricette per i mezzi con cui un'escalation raggiunge le persone, e quanto vale
onestamente ciascuno quando qualcuno sta entrando in casa.

Tre cose vanno lette prima di configurare qualunque cosa:

- **Foyer non implementa nessun mezzo di trasporto.** Home Assistant ha già
  integrazioni `notify.*` per push, SMS, chiamate vocali e messaggistica.
  Foyer le orchestra: decide chi viene avvisato, in che ordine e quando
  fermarsi. Qualunque cosa serva a un canale — un numero di telefono, un id di
  chat, una priorità — la prende così com'è e la passa al servizio.
- **Ogni canale che dipende da internet si guasta proprio nel momento
  sbagliato.** Chi taglia la corrente o la fibra ha tagliato con essa la
  notifica push, il messaggio Telegram e la chiamata Twilio.
  [resilience.it.md](resilience.it.md) è il documento che dice cosa fare; in
  breve: un UPS sul router e almeno un canale GSM locale da qualche parte
  nella lista.
- **Prova ogni canale dalla pagina 6.** Il pulsante accanto a ciascuno invia
  davvero. Il guaio che evita è scoprire durante l'emergenza che il canale
  d'emergenza era configurato male, ed è il motivo per cui il pulsante esiste.

---

<a id="choosing-the-order"></a>

## Scegliere l'ordine

I canali di un contatto sono una lista ordinata, dalla priorità più alta, e un
passo dell'escalation nomina il canale che vuole. Una lista ragionevole:

| Passo | Canale | Perché |
|---|---|---|
| +0 s | Push dell'app Companion | Gratis, immediata, e può portare il pulsante che ferma tutto |
| +60 s | SMS tramite un modem GSM locale | Sopravvive al taglio della fibra, e non richiede un account da nessuna parte |
| +120 s | Push a una seconda persona | Il primo telefono potrebbe essere in tasca a un concerto |
| +300 s | Chiamata vocale | L'unico canale che sveglia chi dorme |

La regola dietro la tabella: metti il canale che sopravvive alla caduta di
internet **da qualche parte nella lista**, non in fondo. Una lista i cui primi
tre passi dipendono tutti dallo stesso router è lunga un passo.

**Prepara la lista con la casa disinserita.** Mentre un'area è inserita, un
contatto nominato da un profilo con cui la casa potrebbe rispondere — subito o
come passo dell'escalation — non può essere modificato, spento o eliminato: il
numero, il servizio, le ore di silenzio e la persona a cui è collegato decidono
tutti chi sente l'allarme. Contano tutti i suoi canali, perché un passo che non
ne nomina nessuno, o ne nomina uno spento, passa dal primo canale ancora
attivo. I contatti di una regola non sono bloccati: sentono la regola, non
l'allarme.

**Una nota sui nomi dei servizi qui sotto.** L'app Companion, Pushover e il
modem GSM creano un servizio con un nome fisso. Gli altri sono piattaforme YAML
`notify:`, il cui servizio prende il nome dal `name:` che dai alla piattaforma
— se lo ometti, Home Assistant crea invece `notify.notify`. I nomi qui
presuppongono che tu abbia impostato `name:` in modo corrispondente, e il menu
a tendina della pagina 6 ti mostra cosa ha davvero questa installazione.

---

<a id="home-assistant-companion-app"></a>

## App Companion di Home Assistant

Il canale che la maggior parte delle case ha già, e l'unico in questo documento
il cui pulsante torna a Foyer.

**Servizio:** `notify.mobile_app_<device>`, creato dall'app stessa quando
accede. Se il servizio manca, il telefono non ha completato la configurazione.

**Notifiche con azioni.** Spunta *Può portare un pulsante di presa d'atto* sul
canale. Foyer allora invia la notifica con un'azione il cui id è
`FOYER_ACKNOWLEDGE`, e ascolta l'evento `mobile_app_notification_action` che
l'app emette quando viene premuta. Non serve nient'altro: nessuna
automazione, nessun blueprint. La presa d'atto passa per lo stesso controllo di
ogni altra, e il registro annota il contatto a cui era andata la notifica.

**Avvisi critici di iOS.** Un allarme alle quattro del mattino è esattamente
ciò per cui esistono: suonano nonostante Full immersion, Non disturbare e
l'interruttore silenzioso. Metti questo nei dati extra del canale:

```yaml
push:
  sound:
    name: default
    critical: 1
    volume: 1.0
```

Il telefono chiede il permesso la prima volta che ne arriva uno, e li rifiuta
in silenzio finché non viene concesso — quindi invia una prova dalla pagina 6
mentre hai il telefono in mano, non mentre ti stanno svaligiando casa.

**Cosa torna indietro.** L'azione porta con sé a quale allarme appartiene e a
quale contatto è stata inviata, e Foyer li legge dall'evento e da
`action_data`, a seconda di quale dei due l'app compila. Una risposta che
arriva senza nessuno dei due prende atto comunque: prende atto **sia**
dell'incidente di intrusione sia del canale tecnico, per lo stesso motivo per
cui lo fa `button.foyer_acknowledge` — la persona ha premuto un pulsante che
dice "l'ho visto", e tirare a indovinare quale allarme intendesse è il modo in
cui un rilevatore di fumo chiude un furto.

**Android.** Queste cinque chiavi tengono la notifica fuori dalla coda del
risparmio energetico e fuori dal mucchio silenzioso della tendina delle
notifiche:

```yaml
ttl: 0
priority: high
channel: Foyer alarm
importance: high
media_stream: alarm_stream_max
```

L'ultima è la parte che conta alle quattro del mattino, e quella che non è
semplicemente "consegnata subito": riproduce la notifica al volume della
sveglia, nonostante l'interruttore silenzioso e Non disturbare. L'app chiede il
permesso per Non disturbare la prima volta, nelle proprie impostazioni, quindi
— di nuovo — invia una prova dalla pagina 6 con il telefono in mano.

---

<a id="pushover"></a>

## Pushover

**Integrazione:** `pushover`. **Servizio:** `notify.pushover`.

La priorità 2 è quella che vale la pena configurare: il messaggio si ripete
finché la persona non ne prende atto *in Pushover*, che è una seconda presa
d'atto in un secondo posto e non ha niente a che fare con quella di Foyer.
Usala per il passo che non deve sfuggire, e tieni una priorità normale per
quelli precedenti.

```yaml
priority: 2
retry: 60      # secondi tra una ripetizione e l'altra, almeno 30
expire: 600    # rinuncia dopo questo tempo
sound: siren
```

Pushover rifiuta la priorità 2 senza sia `retry` sia `expire`, quindi un
canale a cui manca uno dei due fallisce proprio quando viene usato. Provalo.

---

<a id="twilio-sms"></a>

## SMS con Twilio

**Integrazione:** `twilio` più `twilio_sms`. **Servizio:** `notify.twilio_sms`.

La destinazione è il numero in formato internazionale, `+39…`. Costa una
frazione di centesimo a messaggio e arriva su qualunque telefono, anche senza
connessione dati — ma passa da Twilio, via internet, da questa casa: muore con
la fibra esattamente come la push.

---

<a id="twilio-voice-call"></a>

## Chiamata vocale con Twilio

**Integrazione:** `twilio_call`. **Servizio:** `notify.twilio_call`.

Una chiamata è l'unico canale in questo documento che sveglia qualcuno in modo
affidabile. Twilio legge il messaggio con la propria sintesi vocale, oppure
scarica il TwiML da un URL che ospiti tu.

**La pressione di un tasto DTMF.** Il §7.2 della specifica elenca "la pressione
di un tasto durante la chiamata" fra i quattro modi di prendere atto, e questo
è come si collega: il TwiML raccoglie una cifra e fa una POST al webhook di
presa d'atto di Foyer.

```xml
<Response>
  <Gather numDigits="1" action="https://example.org/api/webhook/YOUR_ID" method="POST">
    <Say language="it-IT">Allarme Foyer. Premi 1 per prendere atto.</Say>
  </Gather>
</Response>
```

**Foyer non legge la cifra.** È la POST stessa la presa d'atto: qualunque tasto
sia stato premuto, e qualunque altra cosa possa raggiungere quell'URL, risponde
all'allarme. `<Gather>` fa la POST solo quando viene premuto un tasto, ed è
questo che fa funzionare la ricetta — ma è bene sapere che la cifra non è un
secondo controllo.

Per impostazione predefinita questo prende atto dell'incidente di intrusione.
Per rispondere invece al canale tecnico — una chiamata fatta per il rilevatore
di fumo — mettilo nella query string dell'azione, che è la parte dell'URL che
controlli tu: `…/api/webhook/YOUR_ID?target=technical`.

E se questa installazione ha alzato la politica dei codici per la presa d'atto
(pagina 7; per impostazione predefinita non serve nessun codice), allora né
questo né il pulsante in una notifica push possono rispondere affatto: un
webhook non porta nessun codice. Lascia quell'unica operazione senza codice,
oppure non contare su queste due strade.

**Leggi questo prima di accendere il webhook.** Un webhook di Home Assistant
**non è autenticato**. Chiunque abbia quell'URL — o lo intercetti, dato che il
fornitore telefonico e ogni passaggio intermedio lo vedono — può prendere atto
di un allarme in corso, il che significa fermare l'escalation mentre sta
andando dal tuo vicino. È tutto quello che può fare: non può disinserire,
inserire, leggere il registro o cambiare la configurazione. La posizione di
Foyer è dichiarata, non sottintesa:

- il webhook non esiste finché non lo accendi tu, dalla pagina 6;
- l'id è generato dal backend, lungo e casuale, ed è l'unica cosa che protegge
  l'URL;
- spegnerlo fa dimenticare l'id, quindi riaccenderlo ne consegna uno nuovo
  invece di far rivivere un indirizzo che qualcuno potrebbe ancora avere;
- l'indirizzo viene mostrato una volta sola, quando viene generato — l'URL
  intero se Home Assistant conosce il proprio indirizzo esterno, altrimenti il
  percorso, davanti al quale metterai tu quell'indirizzo — e Foyer non può
  mostrarlo di nuovo. Copialo subito nel fornitore della chiamata vocale. Per
  rivederlo, generane uno nuovo dalla pagina 6, il che ferma subito quello
  vecchio;
- dai l'indirizzo al fornitore della chiamata vocale e a nient'altro, via
  HTTPS.

Se lo scambio non ne vale la pena — e per molte case non ne vale — lascialo
spento e prendi atto dalla notifica push, dalla card, dal tastierino o da
`foyer.acknowledge`. L'escalation si ferma in modo altrettanto completo.

---

<a id="sms--a-usb-gsm-modem"></a>

## `sms` — un modem GSM USB

**Integrazione:** `sms` (Gammu). **Servizio:** `notify.sms`.

L'unico canale in questo documento che non dipende affatto da internet. Una
chiavetta USB da 20 € e una SIM prepagata, e il messaggio esce di casa sulla
rete mobile — che è ancora in piedi quando la fibra è tagliata e, con un UPS
sulla macchina di Home Assistant, quando lo è la corrente.

Da sapere prima di comprare:

- la chiavetta deve essere supportata da Gammu; la famiglia Huawei E173 / E3531
  è la solita risposta sicura;
- una SIM prepagata che non viene mai usata viene disattivata dalla maggior
  parte degli operatori dopo qualche mese. Mandati ogni tanto un messaggio di
  prova dalla pagina 6: è anche l'unico modo per sapere se la SIM ha ancora
  credito;
- il modem è un dispositivo seriale. `/dev/ttyUSB0` cambia da un riavvio
  all'altro, quindi punta l'integrazione a `/dev/serial/by-id/…`.

Questo è il canale di cui il §7.3 raccomanda che ogni installazione ne abbia
uno.

---

<a id="telegram"></a>

## Telegram

**Integrazione:** `telegram_bot`, configurata in *Impostazioni → Dispositivi e
servizi*. **Canale:** l'entità notify che crea per ogni chat (`notify.<chat>`).

Home Assistant ha deprecato il vecchio servizio YAML `notify.telegram`, quindi
ora una chat è un'entità notify. Le entità non portano immagini (vedi sotto),
con un'eccezione: quando l'allegato è *Telegram — foto come file* e il canale è
una chat Telegram, Foyer manda ogni immagine con il servizio dell'integrazione,
`telegram_bot.send_photo`, dopo il testo. Un vecchio servizio `notify.telegram`
funziona ancora finché Home Assistant lo mantiene.

Gratis, immediato, e porta le immagini — ed è per questo che l'azione `notify`
chiede per quale mezzo è pensato un allegato della telecamera. Il server di
Telegram scarica l'immagine da fuori casa senza una sessione propria, quindi
gli serve un **file**; l'app Companion, che ha fatto l'accesso, si accontenta
di un link al proxy della telecamera. Scegliere quello sbagliato produce un
messaggio senza immagine e senza spiegazione.

Un bot Telegram non può iniziare una conversazione: scrivi al bot una volta da
ogni telefono che deve ricevere gli avvisi, altrimenti i messaggi non vanno da
nessuna parte.

---

<a id="signal"></a>

## Signal

**Integrazione:** `signal_messenger`, che richiede un container
[signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api)
in esecuzione da qualche parte nella tua rete. **Servizio:**
`notify.signal`.

L'opzione più riservata di questo elenco — il messaggio è cifrato end-to-end e
Signal non conserva nulla — al prezzo dell'unica configurazione in questo
documento che richiede di far girare un altro servizio e di registrarci un
numero di telefono. Ne vale la pena per le case che usano già Signal; non come
primo canale.

---

<a id="a-notify-entity-is-not-a-notify-service"></a>

## Un'entità notify non è un servizio notify

Compaiono entrambi nel menu a tendina, e non sono equivalenti. Un **servizio**
`notify.*` accetta un titolo, una destinazione e qualunque dato extra il mezzo
capisca — che è ciò che porta un avviso critico di iOS, una foto Telegram o il
pulsante di presa d'atto. Un'**entità** notify accetta un messaggio e un titolo
e nient'altro; tutto il resto viene scartato, e Foyer lo dice nel registro di
Home Assistant invece di lasciarlo sparire. L'unica eccezione sono le immagini
per una chat Telegram, descritte [sopra](#telegram).

Quindi: per un canale che deve fare più che dire una frase, scegli il servizio.
La pagina 6 dice la stessa cosa accanto alla casella di spunta.

<a id="what-foyer-sends"></a>

## Cosa invia Foyer

Una notifica porta il messaggio che l'azione produce, con l'insieme fisso di
variabili del §6.4 — `{{ zone }}`, `{{ area }}`, `{{ incident_zones }}` e le
altre — e qualunque cosa aggiungano i dati extra del canale stesso. Niente
della casa finisce in un messaggio che non hai scritto tu: il principio del
§2.1 è che tutto ciò che esce di casa parte dal minimo che funziona, perché un
messaggio lo legge chiunque stia dall'altra parte.

L'unica cosa che Foyer aggiunge da sé è l'azione di presa d'atto, e solo su un
canale dichiarato capace di portarla.

<a id="answering-a-duress-code"></a>

## Rispondere a un codice di coercizione

Un codice di coercizione fa tutto quello che fa il codice ordinario del suo
proprietario, e ogni volta che viene usato Foyer genera un evento silenzioso,
`duress` — per un disinserimento, ma altrettanto per un inserimento, una zona
esclusa, un walk test, una pagina di impostazioni, un dispositivo sbloccato o
una richiesta rifiutata. Chi sta accanto alla persona che lo digita non vede
niente di diverso; il messaggio è l'unico posto in cui si vede.

Quattro cose decidono come rispondere:

- **Solo il profilo predefinito risponde a `duress`.** L'evento non appartiene
  a nessuna area e a nessun incidente, quindi il profilo di un'area o di uno
  scenario non viene mai interpellato. Metti l'azione sul profilo scelto come
  predefinito in *Impostazioni*.
- **Niente risponde finché non aggiungi un'azione.** Il profilo con cui parte
  una nuova installazione non lo fa: la sua unica azione è una notifica di Home
  Assistant.
- **Una notifica di Home Assistant è la risposta sbagliata.** Compare su ogni
  schermo di Home Assistant, compreso il tablet a muro su cui è stato digitato
  il codice. Lo stesso vale per qualunque cosa la casa faccia ad alta voce:
  `duress` gira sempre in silenzio, e i tipi nella lista silenziosa — la
  sirena, la voce e il campanello per impostazione predefinita — restano fuori
  dalla sua risposta qualunque cosa dica il profilo. L'editor dei profili
  avverte di entrambe le cose.
- **Mandalo a qualcuno fuori casa**, tramite un contatto o un servizio
  `notify.*`, con un messaggio che dica cosa è successo:

```
{{ user }} ha usato un codice di coercizione alle {{ time }}: {{ operation }} {{ area }}
```

`{{ operation }}` nomina cosa è stato costretto a fare la persona — `disarm`,
`arm`, `bypass_zone`, `edit_config`, `export_log`, `unlock`, e per un
interruttore il verso in cui è andato: `walk_test` e `end_walk_test`,
`auto_arming_on` e `auto_arming_off`, `chime_on` e `chime_off` — e
`{{ area }}`, `{{ scenario }}` e `{{ zone }}` cosa nominava la richiesta. Non
va mai in escalation: non c'è niente di cui prendere atto, quindi scegli un
canale che raggiunga qualcuno al primo colpo. Una richiesta fatta di nuovo con
quel codice due minuti dopo è un secondo messaggio, perché è una seconda cosa
che la persona è stata costretta a fare.

La riga `duress` sta nella pagina del registro e in un'esportazione, e in
nessun posto dove la troverebbe un'occhiata: non nella Panoramica, non in
`sensor.foyer_last_event`, non nel registro di un dispositivo API. Sta sul bus
degli eventi di Home Assistant come `foyer_event`, come ogni riga, ed è così
che anche una tua automazione può rispondere — ed è per questo che
un'automazione che mostra gli eventi di sicurezza da qualche parte in casa
deve lasciare fuori `duress`.

Il bus sente solo quello che scrive il registro. Una riga `duress` viene
scritta, e inviata come `foyer_event`, anche con la categoria `security`
spenta in *Impostazioni*; con un registro che non è stato possibile aprire non
c'è nessuna riga `duress` e nemmeno un `foyer_event` per essa. La risposta del
profilo predefinito non dipende dal registro, ed è quella su cui contare.

Quello che invia una risposta alla coercizione viene giudicato solo dal
controllo periodico dei canali
([stato del sistema](system-health.it.md#notification-channel-health)): un
canale che trova guasto viene comunque segnalato, fino a un quarto d'ora dopo
invece che pochi secondi dopo la digitazione del codice.

---

<a id="when-a-send-fails"></a>

## Quando un invio fallisce

Il passo viene annotato come fallito nel registro, sotto `action`, con l'errore
restituito dal mezzo — e un invio al canale di un contatto viene ritentato una
volta, qualche secondo dopo, per il servizio che dopo un riavvio non è ancora
pronto. (Una notifica che nomina direttamente un servizio, invece di un
contatto, non viene ritentata.) Il nuovo tentativo va per conto suo, quindi
l'allarme non lo aspetta, e l'escalation prosegue con i suoi tempi: un canale
morto resta morto, ed è il passo successivo a raggiungere qualcuno.

Verificare che un canale sia *ancora* valido — che il servizio esista ancora,
che il modem sia ancora registrato, che l'ultimo invio abbia funzionato — è
compito dello [stato del sistema](system-health.it.md#notification-channel-health),
che lo fa da solo. Il pulsante di prova della pagina 6 vale comunque la pena
di premerlo dopo ogni aggiornamento di Home Assistant che tocca
un'integrazione con cui invii notifiche.
