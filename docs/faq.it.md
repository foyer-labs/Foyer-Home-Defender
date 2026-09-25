# Domande che vengono fatte

[English](faq.md) · **Italiano**

Questa pagina raccoglie le domande che si fanno prima di installare Foyer e
nelle prime settimane in cui lo si usa. Ogni risposta è breve e rimanda al
documento che la spiega per bene. Se qualcosa è già andato storto, conviene
partire da [risoluzione dei problemi](troubleshooting.it.md).

---

## I sensori li ho già. Perché dovrei volere un antifurto?

Quasi tutti quelli che arrivano qui hanno già l'hardware e non l'hanno mai
guardato così.

Hai messo un contatto sulla porta d'ingresso perché volevi che si accendesse
la luce del corridoio. Ne hai messo uno sulla finestra della camera perché
volevi sapere che era aperta prima che cominciasse a piovere. Hai messo un PIR
in corridoio per la luce di notte, e un altro in cucina perché la cappa si
accorgesse che qualcuno sta cucinando. Due inverni dopo la casa è piena
esattamente dei sensori di cui è fatto un antifurto, e li stai usando per
accendere lampadine.

Poi chiedi quanto costa un antifurto. Viene qualcuno, ti fa un preventivo che
ti fa sbattere le palpebre, e propone di forare il muro per un contatto sulla
porta d'ingresso e un PIR in corridoio: cioè i due sensori già avvitati sullo
stipite di casa tua. E poi c'è l'abbonamento mensile, perché il tastierino deve
telefonare a qualcuno.

Quindi quello che manca non è l'hardware. È la disciplina intorno: aree che si
inseriscono separatamente invece di un unico interruttore tutto-o-niente, un
ritardo d'ingresso che sopravvive a un riavvio, una zona che dichiara cosa
vuol dire «aperta» per lei invece di dare per scontato `on`, un incidente solo
invece di nove notifiche insieme, un registro ancora leggibile fra tre
settimane, e un modo di verificare tutto senza far partire niente alle due di
notte. Questo è ciò che aggiunge Foyer, e costa una serata di configurazione.
[Per iniziare](getting-started.it.md) ti accompagna in quella serata.

## Non potrei farlo con le automazioni?

Puoi, e la prima versione funziona. Quello che costa i sei mesi successivi è
tutto il resto, e Foyer è costruito proprio attorno a quelle parti:

- **Un riavvio a metà di un ritardo d'ingresso.** Foyer salva gli stati delle
  aree, i ritardi in corso, lo spegnimento programmato di una sirena e
  l'avanzamento delle escalation a ogni modifica, e
  li ripristina quando Home Assistant riparte. Il registro annota il buco, così
  non lascia mai intendere che la casa fosse sorvegliata mentre Home Assistant
  era fermo.
- **Un sensore diventato `unavailable` tre settimane fa** e da allora letto
  come «chiuso». In Foyer un'entità `unavailable` o `unknown` è un guasto:
  blocca l'inserimento, finisce nel registro e compare nella diagnostica. Vedi
  [zone](zones.it.md).
- **Tre raffiche di notifiche per una sola effrazione**, perché ogni zona ha
  fatto scattare la sua automazione. Foyer raggruppa le zone di un'effrazione
  in un solo incidente, con una sola escalation e una sola presa d'atto. Vedi
  [profili di risposta](response-profiles.it.md).
- **«La cucina era davvero inserita alle 02:14?»**, chiesto dopo che il
  recorder di Home Assistant ha cancellato quella notte (per impostazione
  predefinita tiene dieci giorni). Foyer tiene un registro suo in un database
  separato, trenta giorni per categoria per impostazione predefinita. Vedi
  [privacy](privacy.it.md) per sapere cosa contiene.

Le tue automazioni restano benvenute. Ogni riga che Foyer scrive nel registro
viene anche emessa sul bus degli eventi di Home Assistant come `foyer_event`,
quindi un'automazione può ascoltarne una qualsiasi. E un profilo di risposta
può chiamare qualunque servizio di Home Assistant con la sua azione
`call_service`.

## Chi può disinserire?

Chi ha un codice, e solo dove i suoi permessi lo consentono: il permesso
*Disinserire*, e solo nelle aree consentite alla sua persona. Il codice lo
controlla il backend di Foyer, mai la card o il pannello, quindi chiamare il
servizio direttamente da Home Assistant non lo aggira.

Finché non esiste la prima persona con un codice, nessuno chiede un codice e
chiunque abbia accesso a Home Assistant può disinserire. Il pannello lo dice
nella *Panoramica* per tutto il tempo in cui dura, perché pretendere un codice
che nessuno ha renderebbe solo impossibile disinserire la casa.

Una persona può essere esentata dal digitare il codice dove Home Assistant sa
già chi è: l'interfaccia di Home Assistant, con l'accesso fatto dal suo
account collegato. Su un tastierino condiviso il codice *è* l'identità, quindi
lì l'esenzione non vale mai. Un tag dichiarato in *Dispositivi di inserimento*
agisce come la persona a cui è intestato senza nessun codice, ed è per questo
che l'editor dei tag avverte che un tag rubato inserisce e disinserisce.

Essere amministratore di Home Assistant non identifica nessuno: il tablet a
muro lasciato sbloccato è quasi sempre collegato con un account
amministratore. Quindi a un amministratore il codice viene chiesto come a
chiunque altro, ogni volta che la politica lo chiede. Ciò che un
amministratore conserva è che i codici sbagliati non lo bloccano mai fuori dal
pannello, dalla card, dai pannelli d'allarme di Home Assistant stesso o dai
servizi `foyer.*`. Il quadro completo è nel [modello di sicurezza](security-model.it.md).

## Posso inserire dalle card di Home Assistant, o a voce?

Sì. Le card d'allarme di Home Assistant, la finestra a comparsa dei dettagli, i
*Mosaico* e gli assistenti vocali parlano tutti con le entità pannello
d'allarme di Foyer (una per area, più *Tutta la casa*), e Foyer risponde a
ogni richiesta come fa ovunque.

Che cosa chiede prima Home Assistant dipende da una sola cosa che Foyer gli
dice: se per inserire serve un codice. Foyer dice di sì solo finché la tua
politica dei codici ne chiede uno per inserire (per impostazione predefinita
non lo chiede) e nessuno potrebbe usare l'esenzione qui sopra: vale solo per
una persona che l'ha attivata, è attiva, è collegata a un account di Home
Assistant ed è dentro il suo periodo di validità. Il motivo è che
Home Assistant agisce su quella risposta prima che Foyer veda chi sta
chiedendo: finché è sì, Home Assistant rifiuta ogni inserimento che arriva
senza codice, anche quello della persona esentata.

- **Finché Foyer dice che serve un codice**, la finestra a comparsa e i
  pulsanti di inserimento di un *Mosaico* lo chiedono. *Tutta la casa* lo dice
  appena una modalità che può ancora inserire chiede un codice, quindi una
  modalità che non ne chiede viene allora rifiutata da Home Assistant finché
  non si digita un codice, anche da un'automazione. Dai il codice a
  quell'automazione, oppure inserisci lo scenario con il servizio `foyer.arm`
  di Foyer.
- **Finché qualcuno può usare l'esenzione**, Home Assistant non chiede niente. La persona
  esentata inserisce senza codice; chiunque altro a cui Foyer chieda un codice
  viene rifiutato da Foyer, con una riga nel registro e un messaggio che dice
  dove digitarlo: la card di Foyer, il pannello di Foyer, o la card *Pannello
  degli Allarmi* di Home Assistant, che mostra un campo per il codice ovunque
  un codice possa essere chiesto, ma offre l'inserimento solo finché il
  pannello è disinserito.
- **Cambiare modalità con la casa inserita** è un cambio di scenario, che per
  impostazione predefinita chiede un codice anche dove inserire non lo chiede.
  La finestra a comparsa chiede un codice solo finché per inserire risulta
  necessario, quindi dove lo chiede solo il cambio il codice si digita nella
  card di Foyer o nel pannello.

Gli assistenti vocali leggono la stessa risposta. Ad Alexa un pannello viene
offerto solo finché inserirlo non chiede un codice; non ne manda nessuno e non
aspetta la risposta di Foyer, quindi un rifiuto si vede solo nello stato del
pannello e nel registro. Google Assistant chiede il
suo PIN prima di inserire solo finché serve un codice, ma manda il PIN salvato
nella propria configurazione che l'abbia chiesto o no: se quel PIN è il codice
Foyer di qualcuno, la richiesta viene fatta a suo nome; se non lo è, è un
codice sbagliato e conta per il blocco.

Un assistente vocale agisce come l'account di Home Assistant con cui è
collegato, per chiunque stia parlando. Collegato tramite l'account di una
persona esentata, passa quell'esenzione a chiunque sia a portata di voce, e un
PIN di Google che è un codice Foyer fa lo stesso. Come collegarne uno in
sicurezza è spiegato nel [modello di sicurezza](security-model.it.md). La card
è descritta in [card](card.it.md).

## Sono l'amministratore e non ho un codice

Succede in una casa dove altri hanno un codice, o quando la tua persona Foyer è
stata disattivata o ha superato la sua finestra di validità. Recuperi l'accesso
da **Impostazioni → Dispositivi e servizi → Foyer Home Defender → Configura**.

Scegli il tuo account di Home Assistant e digita un codice nuovo. Sono elencati
solo gli account amministratore, perché Home Assistant non dice a Foyer chi ha
aperto la finestra. La persona collegata a quell'account viene riattivata, la
sua finestra di validità viene tolta e il suo codice sostituito; un account
senza persona collegata ne riceve una nuova, con tutti i permessi. Il codice
deve avere la lunghezza impostata in Foyer e non deve appartenere già a
qualcuno; proporne uno che appartiene già a qualcuno conta come codice
sbagliato.

Non è mai silenzioso. Il recupero viene scritto nel registro, mostrato come
notifica di Home Assistant e mandato a tutti i contatti attivi, ognuno con il
nome dell'account. A chi non è amministratore si dà un modo per entrare dalla
pagina *Utenti*.

## Funziona senza internet?

Sì. Foyer non richiede né un account cloud né un broker MQTT, e non apre
nessuna connessione verso l'esterno per conto suo tranne il ping del watchdog
esterno, e solo dopo che gli hai dato un URL (vedi
[stato del sistema](system-health.it.md#the-external-watchdog)).

Se le tue *notifiche* sopravvivano a una linea tagliata è un'altra domanda. Una
notifica push no. Ed è per questo che un'escalation è una lista di canali e non
uno solo, e per cui almeno un canale locale, per esempio un modem GSM USB, va
messo da qualche parte in quella lista. [Resilienza](resilience.it.md) spiega cosa sopravvive a un blackout o a una fibra tagliata, e
[canali di notifica](notification-channels.it.md) ha le ricette.

## La mia configurazione sopravvive a un aggiornamento?

Sì: la configurazione salvata è versionata e migrata durante l'aggiornamento,
e [impostazioni](settings.it.md) spiega come, compreso il motivo per cui
tornare a una versione più vecchia può essere rifiutato.

## Cosa succede se rimuovo l'integrazione?

Se ne vanno con lei la sua configurazione, le entità, il pannello nella barra
laterale e il messaggio MQTT conservato sul broker. Il database del registro
resta, a meno che tu non abbia attivato l'opzione per cancellarlo, e gli scatti
delle telecamere non vengono mai cancellati;
[privacy](privacy.it.md#when-foyer-is-removed) ha l'elenco completo.

## È disponibile nella mia lingua?

Oggi in inglese e in italiano, compresi il pannello, la card, l'aiuto
contestuale e i messaggi che Foyer manda. Aggiungere una lingua non tocca il
codice: [CONTRIBUTING](../CONTRIBUTING.md#adding-a-language) (in inglese)
nomina i due file da tradurre.

## Posso usare Foyer accanto a un'altra integrazione d'allarme sugli stessi sensori?

Non sugli stessi sensori:
[migrare da Alarmo](migrating-from-alarmo.it.md#usarli-tutti-e-due-insieme)
spiega perché, e come passare un po' alla volta.

## Esiste un tastierino ESPHome?

Non uno mantenuto da questo progetto nella v1. Un tastierino ESPHome fatto in
casa rispetta il contratto come qualsiasi altro tastierino: può pubblicare sul
topic MQTT, chiamare `foyer.arm` e `foyer.disarm`, oppure parlare con
l'endpoint dei dispositivi di Foyer.
[Tastierini](keypads.it.md#choosing-the-hardware) confronta l'hardware e
descrive tutte e tre le strade.
