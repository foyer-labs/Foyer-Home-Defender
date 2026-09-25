# Resilienza

[English](resilience.md) · **Italiano**

Cosa sopravvive quando qualcuno stacca la corrente, e cosa no.

Questo è il riassunto onesto più breve di tutto quello che segue: **un progetto
che promette notifiche d'allarme solo via internet sta facendo una promessa che
non può mantenere.** Ogni notifica push, ogni messaggio Telegram e ogni
chiamata Twilio viaggia su una connessione che si ferma quando si ferma il
router, e il router si ferma quando va via la corrente. Chi vuole che il tuo
allarme resti muto non ha bisogno di sconfiggerlo. Gli basta trovare
l'armadietto del contatore.

Foyer non può risolvere questo problema. Quello che può fare è dirlo,
avvisarti nel momento in cui succede attraverso una strada che funziona
ancora, e fare in modo che qualcosa fuori casa si accorga di quando tace.

---

<a id="the-attack-plainly"></a>

## L'attacco, detto chiaramente

Ci vogliono circa novanta secondi e nessuna abilità.

1. **Va via la corrente**, staccata al contatore o al quadro elettrico, che
   molto spesso stanno fuori dalla porta d'ingresso o in un armadietto senza
   serratura.
2. **Il router muore all'istante.** Non ha batteria. Home Assistant può
   benissimo morire con lui.
3. **Ogni canale che dipende da internet è sparito.** La notifica push non può
   partire. Il messaggio Telegram non può partire. La chiamata vocale non può
   essere fatta.
4. **Le sirene tacciono** se erano alimentate dalla rete elettrica, come lo
   sono quasi tutte.

Non c'è niente di teorico in tutto questo, e niente di sofisticato. È il motivo
per cui le centrali professionali hanno una batteria, una sirena con la sua
batteria e un combinatore GSM.

La versione con la fibra tagliata è la stessa storia con un passaggio in meno:
la corrente resta, Home Assistant continua a girare, le sirene suonano ancora,
e ogni messaggio continua a non partire.

---

<a id="the-four-things-that-actually-help"></a>

## Le quattro cose che aiutano davvero

In ordine di quanto rendono per quello che costano.

<a id="1-a-ups-on-the-router--and-on-whatever-runs-home-assistant"></a>

### 1. Un UPS sul router — e su qualunque cosa faccia girare Home Assistant

È la cosa di maggior valore in tutta questa pagina.

Un piccolo UPS che tiene in vita il router, il modem e la macchina di Home
Assistant per trenta minuti trasforma l'attacco qui sopra da «l'allarme è
diventato muto» in «l'allarme mi ha chiamato e mi ha detto che è andata via la
corrente». Trenta minuti sono molto più di quanto duri l'evento.

Due dettagli da fare bene:

- **Il modem oltre al router.** Con la fibra e il cavo spesso sono due
  scatole, e solo una sta dietro all'UPS.
- **Anche Home Assistant ne ha bisogno.** Un router acceso senza nessuno che
  parli attraverso di lui è metà del lavoro.

Un UPS ti dà anche il sensore della rete elettrica: tramite NUT, o attraverso
una presa smart, diventa un'entità, e la
[pagina 14](system-health.it.md#mains-power-and-the-ups) trasforma un'interruzione
di corrente in una notifica che parte mentre la batteria ha ancora trenta
minuti davanti.

<a id="2-one-channel-that-does-not-need-the-internet"></a>

### 2. Un canale che non ha bisogno di internet

Un modem GSM USB con la sua SIM, pilotato dall'integrazione `sms` di Home
Assistant, è l'unico canale di notifica in questo documento che sopravvive al
taglio della fibra. Costa più o meno quanto un buon contatto magnetico per porta.

Mettilo nella lista dei canali di un contatto, in qualunque posizione:
un'escalation che parte con una push e ripiega sull'SMS dopo sessanta secondi
è la forma abituale, e vuol dire che l'SMS viene mandato solo quando nessuno ha
risposto alla push. Vedi [notification-channels.it.md](notification-channels.it.md).

I suoi limiti, visto che questa pagina serve a dirli:

- Ha bisogno della rete elettrica come tutto il resto, quindi va dietro
  all'UPS.
- Ha bisogno di copertura cellulare dove sta, e di solito sta in un
  armadietto.
- Un aggressore deciso con un jammer lo sconfigge, ed è una persona di
  un'altra categoria rispetto a quella che ha trovato l'armadietto del
  contatore.

Provalo dalla pagina 6. Un modem GSM configurato male è esattamente il guasto
che il pulsante di prova esiste per evitare.

<a id="3-an-external-watchdog"></a>

### 3. Un watchdog esterno

Foyer fa un ping a un URL che scegli tu; se i ping smettono, quel servizio ti
avvisa. È l'unica risposta al fatto che un sistema morto non può segnalare la
propria morte.

L'interruzione di corrente qui sopra ferma i ping entro un intervallo, e
l'avviso arriva da un posto che non è casa tua. Non sostituisce l'UPS — ti
avvisa dopo invece che nel momento — ma è gratis, si configura in due minuti,
ed è l'unica cosa in questa pagina che funziona quando a guastarsi è Home
Assistant stesso.

Configuralo nella [pagina 14](system-health.it.md#the-external-watchdog).
**Ospitalo da un'altra parte.** Un watchdog che gira sulla stessa macchina, o
su un'altra macchina nella stessa casa, muore con lei e non protegge niente.

<a id="4-sounders-that-are-not-on-the-affected-radio"></a>

### 4. Sirene che non stanno sulla radio colpita

Due punti distinti che tornano entrambi alla stessa idea.

Una sirena alimentata dalla rete elettrica si ferma quando va via la corrente.
Una sirena con la sua batteria no, e una sirena esterna autoalimentata è
quello che usa un'installazione professionale proprio per questo motivo.

E una sirena sulla rete Zigbee è inutile nell'unico caso descritto in
[interferenze radio](system-health.it.md#radio-interference): Foyer non prova
nemmeno a usarla, e lo dice. Quello che resta è una sirena cablata, o una su
un'altra radio.

---

<a id="what-foyer-does-about-it"></a>

## Cosa fa Foyer

| Guasto | Cosa fa Foyer |
|---|---|
| Manca la rete elettrica | `system_power_lost` subito, con gravità da allarme, su qualunque canale funzioni ancora. Un profilo può rispondere. |
| Home Assistant muore | I ping si fermano e il watchdog esterno avvisa. Al ritorno, il vuoto viene registrato: il registro non lascia mai intendere che la casa fosse coperta quando non lo era. |
| Manca internet | Tre ping falliti e Foyer lo segnala in locale: il primo avvertimento che nessuna notifica via internet sarebbe partita. |
| Un canale si rompe | Lo trova il controllo periodico o un invio fallito, compare nella pagina *Contatti*, e viene annunciato su un canale che funziona ancora. |
| La radio tace | Segnalato, e non si risponde attraverso quella radio. |

È tutto nella [pagina 14](system-health.it.md). Niente di questo tocca la
macchina a stati dell'intrusione, con un'eccezione: un'interferenza confermata
con la casa inserita apre un incidente, come fa il jamming in una centrale
professionale.

---

<a id="what-foyer-cannot-do-about-it"></a>

## Cosa Foyer non può fare

Detto una volta, chiaramente, perché il resto di questa pagina si legge meglio
tenendolo a mente:

- **Non può avvisarti su una connessione che non esiste.** Niente può.
- **Non può far suonare una sirena che non ha corrente.**
- **Non può continuare a funzionare quando Home Assistant non funziona.** Il
  vuoto del riavvio viene registrato proprio perché l'alternativa è un sistema
  che lascia intendere di stare sorvegliando quando non lo faceva.
- **Nessuno sta sorvegliando.** Foyer avvisa le persone che hai indicato,
  attraverso mezzi di trasporto che non gli appartengono. Un'escalation che
  non raggiunge nessuno è un esito che la famiglia deve aver previsto — il che
  di solito vuol dire un contatto che non è in casa.

Foyer non è un sistema d'allarme certificato, e niente di quanto sopra è un
difetto da correggere in una versione futura. È la forma che prende un allarme
costruito con hardware di consumo sulla rete e sulla corrente della casa
stessa, e la cosa onesta da fare è documentarlo.

---

<a id="a-sensible-baseline"></a>

## Una base sensata

Per una famiglia che vuole una risposta sola invece di un menu:

1. Un UPS che copre il router, il modem e Home Assistant.
2. Un modem GSM USB come secondo canale di almeno un contatto.
3. Un watchdog esterno su healthchecks.io o Uptime Kuma, con un ping ogni
   quindici minuti.
4. Lo stato dell'UPS stesso come entità della rete elettrica nella pagina 14.
5. Una sirena esterna autoalimentata, non su una radio.
6. Almeno un contatto che non vive in casa.

Sono forse centocinquanta euro di hardware, ed è la differenza fra un allarme
che tace quando qualcuno apre l'armadietto del contatore e uno che ti chiama
mentre sta succedendo.
