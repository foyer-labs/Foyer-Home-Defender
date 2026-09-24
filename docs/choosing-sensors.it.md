# Scegliere i sensori

[English](choosing-sensors.md) · **Italiano**

Questa pagina è messa insieme dalla documentazione dei produttori e delle
integrazioni. Niente di quello che c'è scritto è stato provato su hardware da
questo progetto.

Un sensore comprato per accendere una lampada e un sensore a cui affidi la
guardia di una porta sono spesso la stessa scatoletta, ma gli si chiedono
cose diverse. Alla lampada basta sapere che qualcuno è entrato. L'antifurto
deve sapere anche che il sensore è ancora lì, ancora alimentato, ancora
sentito, e ancora lo stesso che è stato montato. Questa pagina è per chi
compra sensori per Foyer, o deve decidere di quali fidarsi fra quelli che ha
già in casa. Descrive categorie e cosa cercare in una scheda tecnica, non
modelli. Per i sensori che appartengono a un antifurto esistente, vedi
[riusare i sensori di un antifurto esistente](reusing-existing-sensors.it.md).

---

## Cosa cercare

| Caratteristica | Perché conta per un antifurto | Dove finisce in Foyer |
|---|---|---|
| Interruttore antimanomissione | Dice che il contenitore è stato aperto o il sensore staccato dal muro | Una seconda zona, di tipo *Manomissione* |
| Intervallo di supervisione | Dice che il sensore è vivo quando non succede niente | *Limite di silenzio (secondi)* sulla zona |
| Resistenza all'elusione con un magnete | Un contatto che si può tenere chiuso da fuori non protegge niente | Niente in Foyer può rimediare; si sceglie al momento dell'acquisto |
| Radio | Decide cosa gli fanno un jammer, un router spento o una banda affollata | [Interferenze radio](system-health.md#radio-interference) (in inglese) |
| Segnalazione della batteria | Una pila si scarica in silenzio se niente lo segnala | *Entità della batteria* sulla zona |
| Immunità agli animali e tempo cieco dei PIR | Decidono i falsi allarmi e il secondo rilevamento che non arriva mai | *Attivazioni necessarie*, gruppi di verifica |

### Manomissione

Un sensore con interruttore antimanomissione segnala quando qualcuno ne apre
il coperchio o lo stacca dal supporto. Dove l'integrazione lo espone, arriva
in Home Assistant come entità a sé, un `binary_sensor` con device class
`tamper`, accanto a quella della porta o del movimento.

Crealo come zona a sé. Foyer propone il tipo *Manomissione* per quella device
class: sempre attiva, mai esclusa, in allarme che l'impianto sia inserito o
no, e registrata come manomissione invece che come intrusione. Tenerla
separata dal contatto fa sì che il registro dica *quale* delle due è
successa, e che un intruso che toglie il sensore a impianto disinserito
venga comunque sentito.

Due conseguenze da conoscere prima del primo cambio di batteria. Aprire il
contenitore la fa scattare, inserito o no; con la sua area disinserita,
spegni prima la zona di manomissione (*Attiva*) e riaccendila dopo — una zona
disattivata viene ignorata del tutto, e una zona non si può modificare mentre
la sua area è inserita. E un walk test non la elenca: le zone sempre attive
restano operative invece di essere sotto test.

### Intervallo di supervisione

Alcuni sensori segnalano a intervalli regolari anche quando non cambia
niente — un segnale di presenza, o heartbeat. È quello che permette a un
antifurto di distinguere «la porta è chiusa» da «il sensore non c'è più». Un
sensore che segnala solo quando cambia non si distingue da uno morto finché
la porta non si apre e non arriva niente.

Foyer conta quei segnali di presenza. Con un *Limite di silenzio (secondi)*
impostato sulla zona, un'entità che non riporta niente per più del limite è
in guasto: blocca l'inserimento a meno che la zona non lo consenta, genera
`zone_fault`, e compare come *Guasto: muta da troppo tempo* in *Test e
diagnostica*. Una segnalazione conta anche quando lo stato non è cambiato,
perché Foyer legge il `last_reported` di Home Assistant invece del momento
dell'ultimo cambio — a patto che l'integrazione scriva lo stato invariato: un
sensore binario MQTT lo fa solo con `force_update: true`. Il limite è spento di default e si può impostare da 60
secondi a 7 giorni, zona per zona.

Quando scegli, preferisci un sensore la cui documentazione dichiari un
intervallo di segnalazione, e imposta il limite con buon margine oltre
quello. Per un sensore che segnala solo quando cambia, lascia il limite
spento: manderebbe in guasto una porta che resta chiusa. I dettagli sono in
[zone](zones.it.md).

### Elusione con un magnete

Un contatto magnetico è un interruttore tenuto in posizione da un magnete. Un
secondo magnete appoggiato al telaio da fuori può tenerlo chiuso mentre la
porta si apre. Cosa riduce il rischio:

- **Contatti a incasso**, montati dentro il telaio e la porta, dove non c'è
  una superficie su cui appoggiare un magnete e non c'è niente da vedere.
- **Contatti progettati per accorgersi di un magnete estraneo.** Alcuni lo
  sono; se è così, il produttore lo dice.
- **Un secondo livello** a cui dei magneti non importa nulla, che è
  l'argomento dell'ultima sezione.

### Banda radio e mesh

| Radio | Cosa offre la categoria | Cosa sapere |
|---|---|---|
| Zigbee | Mesh a 2,4 GHz; i dispositivi alimentati da rete di solito fanno da ripetitori per quelli a batteria | Condivide la banda con il Wi-Fi. Una mesh dipende dal fatto che i suoi ripetitori siano alimentati |
| Z-Wave | Mesh sotto il gigahertz, frequenza che cambia per regione | Una banda separata da Wi-Fi e Zigbee |
| 433 MHz | Economica, semplice, lunga portata; molti dispositivi unidirezionali e non cifrati | Spesso nessun segnale di presenza e nessuna conferma di ricezione; vedi [riusare](reusing-existing-sensors.it.md#tre-cose-che-la-via-radio-perde) |
| Wi-Fi | Nessun hub in più | Dipende dal router e dalla sua alimentazione; consuma molto le batterie |

Qualsiasi radio si può disturbare. Home Assistant non può misurare il
disturbo, ma Foyer ne sorveglia la firma — molte zone di una stessa radio
che diventano non disponibili insieme, mentre il coordinatore risponde
ancora — e a impianto inserito la tratta come un allarme:
[interferenze radio](system-health.md#radio-interference) (in inglese).
Quel controllo funziona solo per i sensori che *diventano* non disponibili
quando smettono di essere sentiti, che è un motivo in più per preferire una
radio con segnali di presenza.

Distribuire una casa su due radio non è un punto debole: un jammer o un
guasto su una lascia intatta l'altra.

### Segnalazione della batteria

Indica sulla zona l'entità della batteria del sensore (*Entità della
batteria*): un `sensor` in percentuale, o un `binary_sensor` di batteria,
dove `on` vuol dire scarica. Una batteria scarica avvisa e non blocca mai
l'inserimento; un'entità della batteria che non si riesce a leggere affatto è
un guasto, e quella sì che blocca. La soglia è *Batteria scarica sotto* nella
pagina *Impostazioni*, 20 % di default. Il ragionamento è in
[batterie](simulator.md#batteries) (in inglese).

### PIR: immunità agli animali e tempo cieco

**Immunità agli animali.** Alcuni PIR sono fatti per ignorare un animale fino
a un peso dichiarato, e solo se montati all'altezza e con l'angolo indicati
nel manuale. Un animale che sale sulle scale o sul divano può comunque essere
visto. Un PIR senza immunità agli animali in una casa con un cane è un falso
allarme che aspetta solo la prima notte.

**Tempo cieco.** Un PIR a batteria di solito ignora il movimento per un certo
tempo dopo averne segnalato uno, per risparmiare la pila; il manuale dice per
quanto. In quel tempo qualcuno può attraversare tutta la stanza senza che
parta niente. Per Foyer questo conta in un punto che vale la pena mettere
per iscritto: *Attivazioni necessarie* su una zona conta i rilevamenti di
quella zona entro la sua finestra, e sotto quel numero la zona non fa
assolutamente niente. Un PIR a cui chiedi due rilevamenti entro 60 secondi,
con un tempo cieco di tre minuti, non manda mai il secondo, e non va mai in
allarme. Su un PIR così lascia *Attivazioni necessarie* a 1, e cerca la
conferma in un secondo sensore.

---

## Perché una zona a più livelli batte un sensore migliore

Ogni sensore ha un modo per essere eluso: un magnete, un jammer, un tempo
cieco, una pila scarica, un cane. Un sensore più caro restringe quel modo;
non lo elimina. Un secondo sensore di tipo *diverso*, che sorveglia lo
stesso passaggio, si elude con qualcos'altro. Un contatto sulla finestra e un
PIR nella stanza dietro si battono con un magnete più una camminata lenta,
non con uno solo dei due.

In Foyer sono due zone — spesso in due aree, una perimetrale e una interna —
e un modo per dire che si confermano a vicenda.

### Il miglioramento vero più economico

Di solito è un secondo sensore in un
[gruppo di verifica](zones.it.md#gruppi-di-verifica), non un contatto
migliore.

Un gruppo va in allarme quando abbastanza dei suoi membri rilevano entro la
sua finestra: due su due, due su tre. Di default i membri continuano ad
andare in allarme anche da soli, e il gruppo aggiunge la sua conferma e il
suo profilo di risposta. È questo che rende la risposta graduale: dai ai
membri un profilo silenzioso e al gruppo uno rumoroso, e un PIR da solo manda
una notifica mentre due entro un minuto fanno suonare la sirena. Il falso
allarme di un sensore smette di costare una sirena, e l'intruso vero, che ne
attraversa più di uno, la sirena la sente comunque. *Verifica incrociata*
su una zona registra con un solo campo che un sensore ne ha confermato un
altro, ma una coppia non ha un profilo di risposta suo: per la risposta prima
silenziosa e poi rumorosa, crea un gruppo di due.

Due regole decidono dove mettere il secondo sensore:

- **Contano solo i rilevamenti che farebbero scattare subito l'allarme.**
  Aprire la porta d'ingresso e passare durante il ritardo d'ingresso non
  soddisfa mai un gruppo, quindi rientrare a casa non può far partire il
  profilo rumoroso.
- **Una zona appartiene al massimo a un gruppo o a una coppia**, altrimenti
  il suo rilevamento conterebbe due volte.

*I membri non producono nulla sotto la soglia* esiste ed è spento di
default, perché altrimenti un sensore da solo davanti a un intruso vero
produrrebbe silenzio.

---

## Non ancora trattato qui

- Modelli consigliati, e qualsiasi cosa verificata su hardware reale.
- Sensori di rottura vetri, di vibrazione e d'urto, PIR a tenda e barriere
  da esterno.
- Sensori cablati su un ingresso di Home Assistant, e resistenze di fine
  linea.
- Quali integrazioni espongono come entità la manomissione, il segnale di
  presenza e la batteria di un sensore.
- Le sirene, e cosa ne rende una adatta a un antifurto.
- Il montaggio: altezze, angoli, e cosa un PIR non dovrebbe avere davanti.
