# Identità visiva

[English](brand.md) · **Italiano**

Questa pagina descrive il marchio di Foyer Home Defender: da cosa è ricavato, i
suoi tre colori, i file in [`docs/logo/`](logo/) e dove viene usato ciascuno, e
le poche regole che li tengono coerenti. È per chi contribuisce toccando il
pannello, la card o il README, e per chiunque voglia mettere l'icona su una
propria dashboard. Il riferimento di progetto è
[SPEC §17](SPEC.md#17-visual-identity) (in inglese).

<p align="center"><img src="logo/foyer-hd-lockup-light-bg.png" alt="Il logotipo completo di Foyer Home Defender su fondo chiaro: lo scudo a sinistra, la scritta FOYER in inchiostro e sotto HOME DEFENDER in ambra" width="560"></p>

## Il marchio

Il marchio amplia il simbolo di **Foyer** che c'era prima (archi uno dentro
l'altro che si allontanano, una porta ad arco illuminata e una linea di
soglia) racchiudendolo in uno scudo. Lo scudo è stato scelto perché si legge
subito come prodotto di sicurezza, e per un progetto che ancora nessuno
conosce questo conta più di un richiamo geometrico interno (decisione 17).

Dentro lo scudo il disegno è ridotto a quello che si legge anche in piccolo:
due archi, il più vicino pieno e il più lontano a metà opacità, e la porta
sotto di loro. La porta è l'unico elemento caldo e pieno; tutto il resto è una
linea.

## Palette

| Token | Valore | Ruolo |
|---|---|---|
| Ink | `#0D1014` | Fondo su scuro, tratto su chiaro |
| Paper | `#E8ECF2` | Tratto su scuro, fondo su chiaro |
| Amber | `#F0A835` | La porta: l'unico elemento caldo e pieno |
| Amber on light | `#B4780F` | Il sottotitolo *HOME DEFENDER* del logotipo su fondo chiaro, per il contrasto |

**L'ambra non si inverte mai.** Su fondo chiaro le linee e la scritta passano
da Paper a Ink, e l'ambra del sottotitolo si scurisce in `#B4780F` perché si
legga ancora su uno sfondo pallido. La porta resta `#F0A835` in ogni file a
colori, su fondo chiaro o scuro.

## I file

Tutti i file qui sotto sono in [`docs/logo/`](logo/).

| File | Dove compare | Vincolo |
|---|---|---|
| `foyer-hd-icon.svg` | L'icona `foyer:shield`, per le dashboard | Un disegno a parte: 24 px, un solo colore, `currentColor`, tratto 3.4. Non è l'icona della barra laterale |
| `foyer-hd-symbol-dark-bg.svg`<br>`foyer-hd-symbol-light-bg.svg` | L'intestazione del pannello, disegnata a 32 px; il file per fondo scuro quando il tema di Home Assistant è in modalità scura, quello per fondo chiaro altrimenti | A colori, fondo trasparente |
| `foyer-hd-app.svg`, `foyer-hd-app-512.png`, `foyer-hd-app-192.png` | Il PNG da 192 px apre tutti e due i README, largo 120 | Riquadro arrotondato in Ink, il simbolo scalato a 0.84 per lasciare un margine di sicurezza |
| `foyer-hd-lockup-dark-bg.svg` / `.png`<br>`foyer-hd-lockup-light-bg.svg` / `.png` | Questa pagina | Due file, non uno ricolorato |

Tre dettagli su come sono collegati:

- **Il simbolo dell'intestazione viene incorporato nel pannello in fase di
  build.** Il pannello importa i due file SVG come testo, così la pagina li
  disegna senza una seconda richiesta e senza che i file vengano serviti per
  conto loro.
- **I README caricano il riquadro da un indirizzo GitHub assoluto**, non da un
  percorso relativo. HACS mostra il README dentro Home Assistant, dove un
  percorso relativo viene risolto rispetto a Home Assistant invece che al
  repository, e lì il logo una volta si è rotto.
- **`foyer:shield` è generata, non scritta a mano.** Home Assistant disegna
  un'icona personalizzata come un unico tracciato pieno in `currentColor` e non
  disegna i tratti, quindi `scripts/build_sidebar_icon.py` trasforma in
  contorni i tratti di `foyer-hd-icon.svg` con la stessa geometria e scrive il
  risultato in `frontend/src/icons/icon-path.ts`. La CI esegue lo script e
  fallisce quando il tracciato nel repository non corrisponde più all'SVG, così
  i due non possono divergere. Se l'icona cambia, modifica l'SVG ed esegui di
  nuovo lo script.

Per usare l'icona su una dashboard, scrivi `icon: foyer:shield` ovunque una
card accetti un'icona. Il set di icone viene registrato da un modulo che Home
Assistant carica in ogni pagina, quindi è disponibile su qualunque dashboard
una volta configurata l'integrazione.

### Gli altri file in `docs/logo/`

Cinque file non fanno parte dell'insieme descritto sopra. Sono il marchio di
Foyer di prima, senza lo scudo, inseriti nel repository insieme alle
specifiche grafiche. Niente nel codice, nei README o negli altri documenti li
usa.

| File | Cos'è |
|---|---|
| `foyer-simbolo.svg` | Il simbolo originale: tre archi a piena opacità, al 60 % e al 32 %, la porta in ambra e una linea di soglia, in Paper su fondo trasparente |
| `foyer-icona.svg`, `foyer-icona.png` | Lo stesso simbolo su un riquadro arrotondato in Ink; il PNG ne è una resa a 1067 × 1067 |
| `foyer-scuro.svg` | Il simbolo originale con la scritta FOYER, in Paper, per fondo scuro |
| `foyer-chiaro.svg` | Lo stesso logotipo in Ink, per fondo chiaro |

Usano un tratto di 3.6 invece del 3.2 del marchio con lo scudo.

## Le regole che lo tengono coerente

- **L'icona della barra laterale è `mdi:shield-home`**, ed è una concessione,
  non una preferenza (decisione 74). Un set di icone personalizzate viene
  registrato da un modulo JavaScript, e Home Assistant risolve un'icona
  personalizzata una volta sola. Quando la barra laterale viene disegnata prima
  che quel modulo sia partito, che è quello che fa l'app companion quando parte
  da una pagina in cache, Home Assistant ripiega su un elemento legacy e non
  riprova più, e nella barra laterale resta per sempre un quadrato vuoto. Per
  questo lo scudo di Foyer è disegnato dove il codice di Foyer è sicuramente
  caricato, l'intestazione del pannello, e `foyer:shield` resta registrata per
  chi la vuole su una propria dashboard.
- **L'icona da 24 px è ridisegnata, mai rimpicciolita.** Viene resa a 24 px e
  prende il colore del tema, quindi non può usare l'ambra né l'arco a metà
  opacità che fanno funzionare il simbolo a colori: rimpicciolendo la versione
  a colori si ottiene una poltiglia grigia. `foyer-hd-icon.svg` è un disegno a
  sé: il contorno dello scudo, un arco e una porta piena, in `currentColor`
  senza colori di riempimento, sfumature o opacità. L'arco più tenue è escluso
  perché a quella dimensione sparirebbe.
- **La scritta e il sottotitolo non dipendono da nessun font.** *FOYER* è
  costruita con barre e tratti, e *HOME DEFENDER* è salvato come contorni
  (Poppins Medium, convertito), spaziato in modo da coprire la larghezza della
  scritta sopra. Niente nel repository ha bisogno di un font installato per
  disegnare il logotipo.
- **Lo spessore del tratto è costante**: 3.2 nella griglia da 64 unità del
  simbolo, con giunzioni e terminazioni arrotondate, e 3.4 nell'icona
  monocromatica, perché regga il disegno a 24 px. Le lettere della scritta sono
  spesse 3.4 unità.

## Non ancora trattato qui

- **L'uso del marchio da parte di terzi.** Non è stata scritta nessuna regola
  su chi possa usare il nome o il logo, e come. Questa pagina descrive i file;
  non concede né nega niente.
- **Favicon e immagine dell'integrazione.** Il pannello non imposta una favicon
  propria, e `custom_components/foyer/` non contiene immagini, quindi oggi
  nessuno dei due posti usa un file di questo insieme.
