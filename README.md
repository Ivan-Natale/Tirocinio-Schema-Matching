# Schema Matching - Tirocinio

Progetto sviluppato nell'ambito del tirocinio sullo schema matching.

L'obiettivo di questa fase è confrontare due semplici baseline lessicali
per individuare corrispondenze tra gli attributi di due schemi tabellari.

I metodi attualmente implementati sono:

1. similarità di Jaccard sui nomi degli attributi;
2. similarità basata sulla distanza di Levenshtein.

---

## Dataset

Sono stati utilizzati due schemi contenenti 9 attributi ciascuno.

La ground truth è stata costruita manualmente e contiene 7
corrispondenze considerate corrette.

Esempi di corrispondenze presenti nella ground truth:

- `customer_id` ↔ `client_code`
- `first_name` ↔ `given_name`
- `last_name` ↔ `family_name`
- `email` ↔ `email_address`
- `birth_date` ↔ `date_of_birth`
- `postal_code` ↔ `zip_code`
- `total_spent` ↔ `total_amount`

---

## Baseline 1 - Jaccard

La prima baseline utilizza la similarità di Jaccard.

I nomi degli attributi vengono suddivisi in parole utilizzando
il carattere `_`.

Ad esempio:

`birth_date`

diventa:

`{birth, date}`

mentre:

`date_of_birth`

diventa:

`{date, of, birth}`

La similarità viene calcolata come:

numero di parole in comune / numero totale di parole diverse

Per questo esempio:

2 / 3 = 0.6667

---

## Primo esperimento

La prima versione della baseline utilizzava una soglia pari a 0.50.

Risultati:

- TP: 2
- FP: 0
- FN: 5
- Precision: 1.0000
- Recall: 0.2857
- F1-score: 0.4444

La precision è elevata, ma la recall è bassa perché molte
corrispondenze corrette non vengono individuate.

---

## Esperimento con più soglie Jaccard

La baseline è stata successivamente testata con cinque soglie:

- 0.20
- 0.30
- 0.33
- 0.50
- 0.70

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 6 | 6 | 1 | 0.5000 | 0.8571 | 0.6316 |
| 0.30 | 6 | 3 | 1 | 0.6667 | 0.8571 | 0.7500 |
| 0.33 | 6 | 3 | 1 | 0.6667 | 0.8571 | 0.7500 |
| 0.50 | 2 | 0 | 5 | 1.0000 | 0.2857 | 0.4444 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

### Osservazione personale sulla soglia 0.33

La soglia 0.33 è risultata particolarmente interessante perché
permette di recuperare diverse corrispondenze che condividono una
sola parola significativa.

Ad esempio:

- `first_name` ↔ `given_name`
- `last_name` ↔ `family_name`
- `postal_code` ↔ `zip_code`
- `total_spent` ↔ `total_amount`

Rispetto alla soglia 0.50, la recall aumenta da 0.2857 a 0.8571.

Tuttavia vengono introdotti anche falsi positivi, ad esempio:

- `first_name` ↔ `family_name`
- `last_name` ↔ `given_name`
- `postal_code` ↔ `client_code`

Questo mostra il compromesso tra precision e recall:
abbassare la soglia permette di individuare più corrispondenze,
ma aumenta anche il numero di abbinamenti errati.

La coppia `customer_id` ↔ `client_code` rimane invece non
riconosciuta perché la similarità di Jaccard è pari a 0.

---

## Baseline 2 - Levenshtein

Come seconda baseline è stata implementata la distanza di Levenshtein.

La distanza di Levenshtein misura il numero minimo di operazioni
necessarie per trasformare una stringa in un'altra.

Le operazioni considerate sono:

- inserimento di un carattere;
- cancellazione di un carattere;
- sostituzione di un carattere.

La distanza viene trasformata in una similarità compresa tra 0 e 1:

similarità = 1 - distanza / lunghezza massima delle due stringhe

Un valore vicino a 1 indica stringhe molto simili.

A differenza di Jaccard, Levenshtein confronta direttamente i
caratteri e non divide il nome dell'attributo in parole.

---

## Risultati Levenshtein

Sono state utilizzate le stesse cinque soglie:

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 5 | 36 | 2 | 0.1220 | 0.7143 | 0.2083 |
| 0.30 | 5 | 14 | 2 | 0.2632 | 0.7143 | 0.3846 |
| 0.33 | 5 | 12 | 2 | 0.2941 | 0.7143 | 0.4167 |
| 0.50 | 3 | 2 | 4 | 0.6000 | 0.4286 | 0.5000 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

Tra le soglie testate, 0.50 produce il valore di F1 più alto
per Levenshtein.

---

## Confronto preliminare

Considerando il valore di F1 più alto osservato tra le soglie testate:

| Metodo | Soglia | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|
| Jaccard | 0.33 | 0.6667 | 0.8571 | 0.7500 |
| Levenshtein | 0.50 | 0.6000 | 0.4286 | 0.5000 |

Sul dataset utilizzato, Jaccard ottiene risultati migliori.

Levenshtein risulta utile per variazioni ortografiche e differenze
a livello di caratteri, ma presenta difficoltà quando i termini sono
differenti o vengono disposti in un ordine diverso.

Un esempio significativo è:

`birth_date` ↔ `date_of_birth`

Jaccard riconosce le parole `birth` e `date` presenti in entrambi
i nomi, mentre Levenshtein è penalizzato dal diverso ordine dei caratteri.

---

## Arricchimento degli schemi

Gli schemi iniziali contenevano soltanto il nome degli attributi.

Successivamente sono state aggiunte tre informazioni:

- tipo del dato;
- descrizione dell'attributo;
- valore di esempio.

Le nuove informazioni permettono di analizzare meglio il significato
degli attributi e di evidenziare casi in cui il solo nome non è sufficiente.

Ad esempio:

- `customer_id` e `client_code` hanno nomi molto diversi, ma descrizioni
  che indicano entrambi un identificativo univoco del cliente;
- `signup_date` e `account_creation_date` hanno entrambi tipo `DATE`,
  ma le descrizioni indicano eventi differenti.

Le baseline Jaccard e Levenshtein non utilizzano ancora queste
informazioni aggiuntive e continuano a confrontare esclusivamente
il nome degli attributi.

Dopo l'arricchimento degli schemi, i risultati delle due baseline
sono rimasti invariati.

## Secondo dataset - Employees

Per verificare se i risultati ottenuti sul primo dataset fossero
dipendenti dalle caratteristiche specifiche dei nomi degli attributi,
le due baseline sono state testate anche su una seconda coppia di schemi.

Il secondo dataset riguarda attributi relativi ai dipendenti e contiene
7 corrispondenze nella ground truth.

Alcuni esempi sono:

- `emp_id` ↔ `employee_number`
- `fname` ↔ `first_name`
- `lname` ↔ `last_name`
- `dept` ↔ `department`
- `annual_salary` ↔ `compensation`
- `hire_date` ↔ `start_date`
- `office_loc` ↔ `work_location`

Anche su questo dataset sono state utilizzate le soglie:

- 0.20
- 0.30
- 0.33
- 0.50
- 0.70

### Risultati Jaccard - Employees

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.30 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.33 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.50 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

Jaccard riesce a riconoscere soltanto:

`hire_date` ↔ `start_date`

perché i due nomi condividono il token `date`.

Corrispondenze come `fname` ↔ `first_name` oppure
`dept` ↔ `department` non vengono invece riconosciute,
perché il metodo richiede la presenza di token esattamente uguali.

Questo mostra un limite importante della baseline Jaccard
in presenza di abbreviazioni.

### Risultati Levenshtein - Employees

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 6 | 10 | 1 | 0.3750 | 0.8571 | 0.5217 |
| 0.30 | 4 | 7 | 3 | 0.3636 | 0.5714 | 0.4444 |
| 0.33 | 4 | 4 | 3 | 0.5000 | 0.5714 | 0.5333 |
| 0.50 | 3 | 1 | 4 | 0.7500 | 0.4286 | 0.5455 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

Levenshtein riesce a riconoscere alcune abbreviazioni che Jaccard
non individua, ad esempio:

- `fname` ↔ `first_name`
- `lname` ↔ `last_name`

Tuttavia il confronto basato sui caratteri può generare anche
corrispondenze errate.

Un esempio osservato con soglia 0.50 è:

`hire_date` ↔ `first_name`

che ottiene una similarità sufficiente pur rappresentando concetti
completamente differenti.

Inoltre la corrispondenza:

`annual_salary` ↔ `compensation`

non viene individuata neanche da Levenshtein, perché i due nomi
sono semanticamente collegati ma lessicalmente molto diversi.

---

## Confronto tra i due dataset

Considerando il valore di F1 più alto osservato tra le soglie testate:

| Dataset | Metodo | Soglia | Precision | Recall | F1-score |
|---|---|---:|---:|---:|---:|
| Customers | Jaccard | 0.33 | 0.6667 | 0.8571 | 0.7500 |
| Customers | Levenshtein | 0.50 | 0.6000 | 0.4286 | 0.5000 |
| Employees | Jaccard | 0.33 | 1.0000 | 0.1429 | 0.2500 |
| Employees | Levenshtein | 0.50 | 0.7500 | 0.4286 | 0.5455 |

I risultati mostrano che le prestazioni dei metodi lessicali
dipendono dalle caratteristiche dei nomi degli attributi.

Nel dataset Customers, Jaccard ottiene risultati migliori perché
diverse corrispondenze condividono token completi.

Nel dataset Employees, Levenshtein ottiene invece risultati migliori
tra le configurazioni testate, perché riesce a riconoscere alcune
abbreviazioni e variazioni a livello di caratteri.

Nessuno dei due metodi riesce però a gestire in modo affidabile
corrispondenze basate principalmente sul significato, come
`annual_salary` ↔ `compensation`.

Questa osservazione motiva il successivo studio di metodi
di schema matching basati su rappresentazioni semantiche.



## Baseline con filtro sui tipi

Dopo aver mantenuto le configurazioni originali come baseline
`name-only`, è stata aggiunta una seconda configurazione che utilizza
anche il tipo degli attributi.

Il tipo non viene concatenato al nome e non modifica direttamente
il valore di similarità.

Viene utilizzato invece come filtro preliminare:

- se i due attributi hanno lo stesso tipo, viene calcolata la similarità
  lessicale sul nome;
- se i tipi sono differenti, la coppia viene esclusa prima del confronto.

La regola utilizzata è quindi:

`tipo_a == tipo_b`

In questa prima variante viene utilizzata l'uguaglianza esatta tra i tipi.

Questa scelta permette di valutare separatamente il contributo
dell'informazione sul tipo rispetto alle baseline `name-only`.

---

### Jaccard con filtro sui tipi

Nel dataset Customers, su 81 possibili coppie di attributi,
55 vengono escluse perché hanno tipi differenti.

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 6 | 5 | 1 | 0.5455 | 0.8571 | 0.6667 |
| 0.30 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 |
| 0.33 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 |
| 0.50 | 2 | 0 | 5 | 1.0000 | 0.2857 | 0.4444 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

Rispetto alla configurazione `name-only`, il filtro sui tipi
riduce alcuni falsi positivi.

Un esempio è:

`postal_code` ↔ `client_code`

La similarità Jaccard sui nomi è sufficiente per superare alcune
soglie, ma i due attributi hanno tipi differenti:

- `postal_code` → `TEXT`
- `client_code` → `INTEGER`

La coppia viene quindi esclusa prima del confronto.

Con soglia 0.33, il numero di falsi positivi passa da 3 nella
configurazione `name-only` a 2 con il filtro sui tipi,
mentre il numero di true positive rimane invariato.

---

### Jaccard con filtro sui tipi - Employees

Nel dataset Employees vengono escluse 30 delle 49 possibili coppie.

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.30 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.33 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.50 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

In questo caso il filtro sui tipi non modifica i risultati principali
di Jaccard.

Il limite rimane infatti legato al confronto sui token:
corrispondenze come `fname` ↔ `first_name` oppure
`dept` ↔ `department` non condividono token esattamente uguali.

Il tipo può quindi eliminare coppie incompatibili, ma non può
recuperare corrispondenze che il confronto lessicale non riconosce.

---

### Levenshtein con filtro sui tipi

Nel dataset Customers vengono escluse 55 delle 81 possibili coppie.

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 5 | 12 | 2 | 0.2941 | 0.7143 | 0.4167 |
| 0.30 | 5 | 5 | 2 | 0.5000 | 0.7143 | 0.5882 |
| 0.33 | 5 | 4 | 2 | 0.5556 | 0.7143 | 0.6250 |
| 0.50 | 3 | 2 | 4 | 0.6000 | 0.4286 | 0.5000 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

L'effetto del filtro è particolarmente evidente con Levenshtein.

Ad esempio, con soglia 0.33:

- configurazione `name-only`: 5 TP e 12 FP;
- configurazione con filtro sul tipo: 5 TP e 4 FP.

Il numero di true positive rimane quindi invariato,
mentre vengono eliminati diversi falsi positivi.

Questo avviene perché Levenshtein può assegnare una similarità
relativamente elevata a nomi ortograficamente simili anche quando
gli attributi rappresentano concetti differenti.

---

### Levenshtein con filtro sui tipi - Employees

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 6 | 4 | 1 | 0.6000 | 0.8571 | 0.7059 |
| 0.30 | 4 | 4 | 3 | 0.5000 | 0.5714 | 0.5333 |
| 0.33 | 4 | 2 | 3 | 0.6667 | 0.5714 | 0.6154 |
| 0.50 | 3 | 0 | 4 | 1.0000 | 0.4286 | 0.6000 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

Un esempio significativo riguarda:

`hire_date` ↔ `first_name`

Nella configurazione `name-only`, Levenshtein assegna alla coppia
una similarità pari a 0.50.

La coppia è però errata dal punto di vista semantico.

Con il filtro sui tipi viene eliminata perché:

- `hire_date` → `DATE`
- `first_name` → `TEXT`

Questo permette, con soglia 0.50, di passare da:

- 3 TP e 1 FP nella configurazione `name-only`;

a:

- 3 TP e 0 FP con il filtro sui tipi.

---

## Confronto tra name-only e filtro sui tipi

Alcuni risultati significativi sono:

| Dataset | Metodo | Configurazione | Soglia | Precision | Recall | F1-score |
|---|---|---|---:|---:|---:|---:|
| Customers | Jaccard | Name-only | 0.33 | 0.6667 | 0.8571 | 0.7500 |
| Customers | Jaccard | Nome + tipo | 0.33 | 0.7500 | 0.8571 | 0.8000 |
| Customers | Levenshtein | Name-only | 0.33 | 0.2941 | 0.7143 | 0.4167 |
| Customers | Levenshtein | Nome + tipo | 0.33 | 0.5556 | 0.7143 | 0.6250 |
| Employees | Jaccard | Name-only | 0.33 | 1.0000 | 0.1429 | 0.2500 |
| Employees | Jaccard | Nome + tipo | 0.33 | 1.0000 | 0.1429 | 0.2500 |
| Employees | Levenshtein | Name-only | 0.50 | 0.7500 | 0.4286 | 0.5455 |
| Employees | Levenshtein | Nome + tipo | 0.50 | 1.0000 | 0.4286 | 0.6000 |

Il filtro sul tipo non modifica direttamente la similarità lessicale
e non permette di trovare nuove corrispondenze.

Il suo contributo principale consiste nell'eliminare coppie
chiaramente incompatibili, riducendo in alcuni casi il numero
di falsi positivi.

L'effetto è particolarmente evidente con Levenshtein,
che può attribuire una similarità elevata a nomi simili dal punto
di vista dei caratteri ma non dal punto di vista semantico.

Il filtro sui tipi non risolve invece casi come:

`annual_salary` ↔ `compensation`

I due attributi hanno tipi compatibili, ma i loro nomi sono
lessicalmente molto differenti.

Per affrontare questo tipo di corrispondenza sarà necessario
utilizzare anche informazioni semantiche, come le descrizioni
degli attributi.



## Baseline con nome e descrizione

Dopo le configurazioni `name-only` e `nome + filtro sul tipo`,
è stata aggiunta una terza configurazione che utilizza anche
la descrizione degli attributi.

Nome e descrizione vengono confrontati separatamente.

Per ciascuna coppia vengono quindi calcolati:

- uno score sul nome;
- uno score sulla descrizione.

I due valori vengono poi combinati utilizzando:

score_finale = 0.70 * score_nome + 0.30 * score_descrizione

Il nome mantiene quindi un peso maggiore rispetto alla descrizione.

I pesi 0.70 e 0.30 sono stati fissati prima dell'analisi dei risultati
e non sono stati modificati successivamente per adattarsi al test.

I valori di esempio presenti negli schemi non vengono ancora utilizzati.

---

### Jaccard - Nome + descrizione - Customers

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 7 | 6 | 0 | 0.5385 | 1.0000 | 0.7000 |
| 0.30 | 7 | 4 | 0 | 0.6364 | 1.0000 | 0.7778 |
| 0.33 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 |
| 0.50 | 6 | 0 | 1 | 1.0000 | 0.8571 | 0.9231 |
| 0.70 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |

L'aggiunta della descrizione permette di recuperare corrispondenze
che la baseline basata solo sul nome non riusciva a individuare.

Un esempio significativo è:

`customer_id` ↔ `client_code`

Con Jaccard sui soli nomi la similarità è pari a 0, mentre le due
descrizioni sono identiche. La similarità della descrizione è quindi
pari a 1 e contribuisce ad aumentare lo score finale.

Con soglia 0.50 vengono individuate 6 delle 7 corrispondenze corrette
senza falsi positivi.

---

### Jaccard - Nome + descrizione - Employees

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 7 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| 0.30 | 7 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| 0.33 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.50 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

Su questo dataset la descrizione ha un impatto particolarmente forte.

Corrispondenze come:

`annual_salary` ↔ `compensation`

non condividono token nel nome, ma presentano descrizioni identiche.

Con score del nome pari a 0 e score della descrizione pari a 1,
lo score finale diventa:

0.70 * 0 + 0.30 * 1 = 0.30

Questo spiega perché la coppia viene individuata con soglia 0.30,
ma non con soglia 0.33.

I risultati molto elevati devono però essere interpretati con cautela:
nel dataset Employees molte coppie corrette hanno descrizioni
esattamente identiche. Il test è quindi particolarmente favorevole
alla componente basata sulla descrizione e potrebbe non rappresentare
la difficoltà di uno scenario reale.

---

### Levenshtein - Nome + descrizione - Customers

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 7 | 56 | 0 | 0.1111 | 1.0000 | 0.2000 |
| 0.30 | 7 | 21 | 0 | 0.2500 | 1.0000 | 0.4000 |
| 0.33 | 7 | 15 | 0 | 0.3182 | 1.0000 | 0.4828 |
| 0.50 | 5 | 2 | 2 | 0.7143 | 0.7143 | 0.7143 |
| 0.70 | 2 | 0 | 5 | 1.0000 | 0.2857 | 0.4444 |

Levenshtein applicato alle descrizioni riesce a recuperare alcune
corrispondenze grazie alla somiglianza dei testi, ma a soglie basse
produce molti falsi positivi.

Questo avviene perché descrizioni relative a concetti differenti
possono comunque condividere numerosi caratteri o parti della frase.

---

### Levenshtein - Nome + descrizione - Employees

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 7 | 39 | 0 | 0.1522 | 1.0000 | 0.2642 |
| 0.30 | 7 | 14 | 0 | 0.3333 | 1.0000 | 0.5000 |
| 0.33 | 7 | 10 | 0 | 0.4118 | 1.0000 | 0.5833 |
| 0.50 | 4 | 3 | 3 | 0.5714 | 0.5714 | 0.5714 |
| 0.70 | 1 | 0 | 6 | 1.0000 | 0.1429 | 0.2500 |

La descrizione permette a Levenshtein di recuperare anche
corrispondenze difficili come:

`annual_salary` ↔ `compensation`

Tuttavia continuano a comparire falsi positivi dovuti alla somiglianza
ortografica tra descrizioni relative a concetti differenti.

---

## Confronto delle tre configurazioni

Le tre configurazioni analizzate sono:

`name-only`

`nome + filtro sul tipo`

`nome + descrizione`

Il filtro sul tipo agisce principalmente eliminando coppie
incompatibili e quindi riducendo i falsi positivi.

La descrizione, invece, può fornire anche un'evidenza positiva
e permettere di recuperare corrispondenze che il solo nome non
riesce a individuare.

I risultati mostrano però che l'efficacia della descrizione dipende
fortemente dalla qualità e dalla formulazione del testo disponibile.

In particolare, descrizioni identiche rendono il problema molto più
semplice rispetto a descrizioni semanticamente equivalenti ma scritte
in modi differenti.

Questo aspetto dovrà essere considerato nell'interpretazione finale
dei risultati e motiva il successivo studio di tecniche semantiche
più avanzate.


## Vecchia sperimentazione con nome e descrizione

In una prima fase è stata introdotta una configurazione che combina
la similarità del nome e della descrizione degli attributi.

Per ogni coppia vengono calcolati separatamente:

- uno score sul nome;
- uno score sulla descrizione.

I due punteggi vengono combinati tramite:

score_finale = 0.70 * score_nome + 0.30 * score_descrizione

In questa prima versione, diverse coppie corrette presentavano descrizioni
identiche o molto simili.

Questo ha prodotto risultati particolarmente elevati, soprattutto sul
dataset EMPLOYEES.

Ad esempio, alcune coppie come:

`annual_salary` ↔ `compensation`

avevano descrizioni esattamente uguali.

Questa prima sperimentazione è stata mantenuta nel repository perché
rappresenta una fase del percorso di sviluppo, ma i risultati non devono
essere considerati come valutazione finale del metodo.

I risultati completi di questa prima versione sono riportati nei file:

- `risultati_jaccard_description.csv`
- `risultati_levenshtein_description.csv`


## Revisione con descrizioni più realistiche

Dopo una revisione metodologica, le descrizioni dei due schemi sono state
riscritte in modo indipendente.

Le descrizioni delle coppie corrette rimangono semanticamente equivalenti,
ma non sono più copie dello stesso testo.

Ad esempio:

`annual_salary`

> Retribuzione lorda prevista su base annua

`compensation`

> Importo della retribuzione complessiva riferita a un anno

Questa modifica rende l'esperimento più realistico perché il matcher non
può più basarsi semplicemente sulla presenza di descrizioni identiche.


### Attributi senza corrispondenza e casi ambigui

Il dataset EMPLOYEES è stato ampliato da 7 a 10 attributi per schema.

La ground truth continua a contenere 7 corrispondenze corrette, mentre
sono stati aggiunti attributi senza corrispondenza.

Alcuni casi sono stati scelti volutamente per essere semanticamente vicini
ma non equivalenti, ad esempio:

`annual_salary` ↔ `monthly_salary`

`office_loc` ↔ `office_city`

`home_city` ↔ `office_city`

`contract_type` ↔ `employment_status`

Questi casi permettono di valutare non soltanto la capacità del matcher
di trovare corrispondenze corrette, ma anche la capacità di evitare
corrispondenze tra concetti simili ma differenti.


## Selezione dei parametri e valutazione finale

Per evitare di scegliere i parametri direttamente sul dataset di test,
i due dataset sono stati utilizzati con ruoli differenti.

`CUSTOMERS` è stato utilizzato come development set.

`EMPLOYEES` è stato utilizzato come test set finale.

Il procedimento seguito è stato:

CUSTOMERS
→ selezione dei parametri
→ parametri bloccati
→ EMPLOYEES
→ valutazione finale

Una volta osservati i risultati su EMPLOYEES, i parametri non sono stati
modificati.

### Parametri selezionati su CUSTOMERS

| Algoritmo | Peso nome | Peso descrizione | Soglia | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|---:|---:|
| Jaccard | 0.80 | 0.20 | 0.30 | 0.7500 | 0.8571 | 0.8000 |
| Levenshtein | 0.80 | 0.20 | 0.50 | 0.7500 | 0.4286 | 0.5455 |

### Valutazione finale su EMPLOYEES

| Algoritmo | Peso nome | Peso descrizione | Soglia | TP | FP | FN | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jaccard | 0.80 | 0.20 | 0.30 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |
| Levenshtein | 0.80 | 0.20 | 0.50 | 2 | 3 | 5 | 0.4000 | 0.2857 | 0.3333 |


### Analisi della revisione

Con le descrizioni più realistiche, Jaccard non individua nessuna
corrispondenza sul test set.

Questo mostra che la versione precedente era favorita dalla presenza
di descrizioni identiche e che Jaccard ha difficoltà quando le stesse
informazioni vengono espresse con parole differenti.

Levenshtein riesce invece a individuare alcune corrispondenze corrette,
come:

`lname` ↔ `last_name`

`hire_date` ↔ `start_date`

ma produce anche falsi positivi come:

`annual_salary` ↔ `monthly_salary`

`office_loc` ↔ `office_city`

`home_city` ↔ `office_city`

Questi errori mostrano che una forte similarità lessicale o ortografica
non implica necessariamente una corrispondenza semantica.

I risultati della revisione sono considerati quelli di riferimento per
la valutazione finale della configurazione basata su nome e descrizione.


## Confronto finale delle baseline lessicali

Dopo la revisione metodologica dei dataset, è stato completato un confronto sistematico tra quattro configurazioni lessicali:

- solo nome;
- sola descrizione;
- nome + descrizione;
- nome + filtro sul tipo.

Il confronto è stato eseguito sia con Jaccard sia con Levenshtein.

Per mantenere separata la fase di sviluppo dalla valutazione finale, è stato utilizzato il seguente protocollo:

`CUSTOMERS` → selezione dei parametri  
`EMPLOYEES` → valutazione finale con parametri bloccati

Le soglie e, nel caso della configurazione nome + descrizione, anche i pesi sono stati selezionati esclusivamente sul dataset `CUSTOMERS`.

Una volta scelti, i parametri non sono stati modificati dopo aver osservato i risultati su `EMPLOYEES`.

---

### Configurazioni analizzate

#### Solo nome

La similarità viene calcolata utilizzando esclusivamente il nome degli attributi.

Esempi:

`first_name` ↔ `given_name`

`annual_salary` ↔ `compensation`

Questa configurazione rappresenta la baseline lessicale più semplice.

#### Sola descrizione

La similarità viene calcolata utilizzando esclusivamente la descrizione testuale associata all'attributo.

Le descrizioni dei due schemi sono state scritte in modo indipendente e possono quindi rappresentare lo stesso concetto utilizzando parole differenti.

#### Nome + descrizione

Nome e descrizione vengono confrontati separatamente e i due punteggi vengono combinati tramite una media pesata.

Sono state considerate tre combinazioni di pesi:

- 0.80 nome + 0.20 descrizione;
- 0.70 nome + 0.30 descrizione;
- 0.60 nome + 0.40 descrizione.

#### Nome + filtro sul tipo

La similarità viene calcolata sul nome, ma vengono escluse prima del confronto le coppie con tipi differenti.

Il filtro utilizzato è rigido:

```python
if tipo_a != tipo_b:
    continue
  ```

## Selezione dei parametri su CUSTOMERS

Per ogni configurazione sono state testate le seguenti soglie:

`0.20`, `0.30`, `0.33`, `0.50`, `0.70`

La scelta della configurazione migliore è stata effettuata utilizzando il seguente criterio:

1. F1-score più alto;
2. in caso di parità, precision più alta;
3. per la configurazione `nome + descrizione`, in caso di ulteriore parità, peso maggiore assegnato al nome;
4. se necessario, soglia più alta.

I risultati completi della fase di selezione sono salvati nel file:

`selezione_parametri_lessicali.csv`

I parametri scelti sono invece salvati nel file:

`parametri_lessicali_selezionati.csv`

### Parametri selezionati

| Algoritmo | Configurazione | Soglia | Peso nome | Peso descrizione | F1 su CUSTOMERS |
|---|---|---:|---:|---:|---:|
| Jaccard | Solo nome | 0.33 | - | - | 0.7500 |
| Jaccard | Sola descrizione | 0.20 | - | - | 0.4211 |
| Jaccard | Nome + descrizione | 0.30 | 0.80 | 0.20 | 0.8000 |
| Jaccard | Nome + filtro tipo | 0.33 | - | - | 0.8000 |
| Levenshtein | Solo nome | 0.50 | - | - | 0.5000 |
| Levenshtein | Sola descrizione | 0.50 | - | - | 0.4000 |
| Levenshtein | Nome + descrizione | 0.50 | 0.80 | 0.20 | 0.5455 |
| Levenshtein | Nome + filtro tipo | 0.33 | - | - | 0.6250 |

---

## Valutazione finale su EMPLOYEES

Dopo la selezione su `CUSTOMERS`, i parametri sono stati bloccati e applicati senza ulteriori modifiche al dataset `EMPLOYEES`.

Il dataset di test contiene:

- 10 attributi nello schema A;
- 10 attributi nello schema B;
- 7 corrispondenze nella ground truth.

### Risultati finali

| Algoritmo | Configurazione | TP | FP | FN | Precision | Recall | F1-score |
|---|---|---:|---:|---:|---:|---:|---:|
| Jaccard | Solo nome | 1 | 3 | 6 | 0.2500 | 0.1429 | 0.1818 |
| Jaccard | Sola descrizione | 1 | 5 | 6 | 0.1667 | 0.1429 | 0.1538 |
| Jaccard | Nome + descrizione | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |
| Jaccard | Nome + filtro tipo | 1 | 3 | 6 | 0.2500 | 0.1429 | 0.1818 |
| Levenshtein | Solo nome | 3 | 4 | 4 | 0.4286 | 0.4286 | 0.4286 |
| Levenshtein | Sola descrizione | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |
| Levenshtein | Nome + descrizione | 2 | 3 | 5 | 0.4000 | 0.2857 | 0.3333 |
| Levenshtein | Nome + filtro tipo | 4 | 5 | 3 | 0.4444 | 0.5714 | 0.5000 |

La configurazione lessicale con il miglior risultato finale è:

`Levenshtein + nome + filtro sul tipo`

con:

- **Precision = 0.4444**
- **Recall = 0.5714**
- **F1-score = 0.5000**

---

## Analisi dei risultati

Il confronto finale mostra che l'aggiunta di informazioni non produce automaticamente un miglioramento.

### Jaccard

Con Jaccard, la configurazione `solo nome` e quella `nome + filtro sul tipo` producono lo stesso risultato finale.

I principali falsi positivi sono:

- `annual_salary` ↔ `monthly_salary`
- `home_city` ↔ `office_city`
- `office_loc` ↔ `office_city`

Queste coppie hanno tipi compatibili e quindi il filtro sul tipo non può eliminarle.

Ho osservato quindi che il tipo è utile solo quando l'errore coinvolge attributi strutturalmente incompatibili, ma non risolve ambiguità tra attributi dello stesso tipo.

La configurazione `nome + descrizione` ottiene invece un F1-score pari a `0`.

Questo risultato mostra che Jaccard ha difficoltà quando nomi e descrizioni semanticamente equivalenti utilizzano parole differenti.

### Levenshtein

Levenshtein applicato al solo nome ottiene un F1-score pari a:

`0.4286`

La configurazione con filtro sul tipo migliora il risultato fino a:

`0.5000`

Le corrispondenze corrette individuate sono:

- `dept` ↔ `department`
- `fname` ↔ `first_name`
- `hire_date` ↔ `start_date`
- `lname` ↔ `last_name`

Il filtro sul tipo riesce quindi a ridurre parte del rumore prodotto dalla similarità ortografica.

Rimangono comunque alcuni falsi positivi, ad esempio:

- `annual_salary` ↔ `monthly_salary`
- `home_city` ↔ `office_city`
- `office_loc` ↔ `office_city`

Questi casi mostrano un limite importante dell'approccio: attributi semanticamente differenti possono risultare molto simili a livello lessicale e avere anche lo stesso tipo.

---

## Considerazioni personali

Da questo confronto ho osservato che la configurazione che generalizza meglio non è necessariamente quella che ottiene il miglior risultato sul development set.

La configurazione:

`Levenshtein + nome + filtro tipo`

non aveva il miglior F1-score assoluto su `CUSTOMERS`, ma risulta la migliore su `EMPLOYEES`.

Questo conferma l'importanza di mantenere separati development set e test set.

Un altro risultato che considero particolarmente importante riguarda le descrizioni.

Dopo averle rese più realistiche, il loro utilizzo con semplici metriche lessicali non ha prodotto un miglioramento generale.

In alcuni casi ha addirittura ridotto le prestazioni rispetto all'utilizzo del solo nome.

Questo mi ha fatto capire che aggiungere più informazione non significa automaticamente migliorare il matcher: è necessario anche utilizzare una tecnica di similarità adatta al tipo di informazione utilizzata.

Gli errori osservati mostrano inoltre due limiti opposti delle baseline lessicali:

- attributi semanticamente equivalenti possono essere molto diversi lessicalmente, ad esempio `annual_salary` ↔ `compensation`;
- attributi semanticamente differenti possono essere molto simili lessicalmente, ad esempio `annual_salary` ↔ `monthly_salary`.

Queste osservazioni motivano il passaggio successivo verso una baseline semantica basata su embeddings.


## Baseline semantica con embeddings

Dopo il confronto tra le baseline lessicali, è stata implementata una prima baseline semantica basata su embeddings.

È stato utilizzato il modello pre-addestrato:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Il modello trasforma ogni testo in un vettore numerico di 384 dimensioni.

La similarità tra due attributi viene calcolata tramite **cosine similarity** tra i rispettivi embeddings.

L'obiettivo è verificare se una rappresentazione semantica riesce a riconoscere corrispondenze tra attributi che esprimono lo stesso concetto anche quando utilizzano parole differenti.

---

### Configurazioni analizzate

Sono state confrontate tre configurazioni.

#### Solo nome

Viene generato l'embedding utilizzando esclusivamente il nome dell'attributo.

Prima della generazione dell'embedding, il carattere `_` viene sostituito con uno spazio.

Ad esempio:

`annual_salary`

diventa:

`annual salary`

#### Sola descrizione

Viene utilizzata esclusivamente la descrizione testuale dell'attributo.

Questa configurazione permette di verificare se gli embeddings riescono a sfruttare meglio delle metriche lessicali descrizioni semanticamente equivalenti ma formulate con parole differenti.

#### Nome + descrizione

Nome e descrizione vengono combinati in un unico testo prima della generazione dell'embedding.

Ad esempio:

`annual salary. Retribuzione lorda prevista su base annua`

In questo modo il modello può utilizzare contemporaneamente il nome dell'attributo e il contesto fornito dalla descrizione.

---

## Selezione delle soglie su CUSTOMERS

Anche per gli embeddings è stato mantenuto lo stesso protocollo sperimentale utilizzato per le baseline lessicali:

`CUSTOMERS` → selezione della soglia  
`EMPLOYEES` → valutazione finale con soglia bloccata

Le soglie sono state selezionate esclusivamente sul development set `CUSTOMERS`.

Sono state analizzate le seguenti soglie:

`0.10`, `0.20`, `0.30`, `0.40`, `0.50`, `0.55`, `0.60`, `0.65`, `0.70`, `0.75`, `0.80`, `0.85`, `0.90`

La scelta è stata effettuata utilizzando il seguente criterio:

1. F1-score più alto;
2. in caso di parità, precision più alta;
3. in caso di ulteriore parità, soglia più alta.

Una volta selezionate le soglie, queste non sono state modificate dopo aver osservato i risultati su `EMPLOYEES`.

### Soglie selezionate

| Configurazione | Soglia | TP | FP | FN | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|---:|---:|---:|
| Solo nome | 0.80 | 4 | 1 | 3 | 0.8000 | 0.5714 | 0.6667 |
| Sola descrizione | 0.65 | 7 | 6 | 0 | 0.5385 | 1.0000 | 0.7000 |
| Nome + descrizione | 0.75 | 5 | 1 | 2 | 0.8333 | 0.7143 | 0.7692 |

La configurazione con il miglior F1-score sul development set è risultata:

`nome + descrizione`

con F1-score pari a `0.7692`.

---

## Valutazione finale degli embeddings su EMPLOYEES

Le soglie selezionate su `CUSTOMERS` sono state successivamente bloccate e applicate senza ulteriori modifiche al dataset `EMPLOYEES`.

### Risultati finali

| Configurazione | Soglia | TP | FP | FN | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|---:|---:|---:|
| Solo nome | 0.80 | 0 | 2 | 7 | 0.0000 | 0.0000 | 0.0000 |
| Sola descrizione | 0.65 | 6 | 17 | 1 | 0.2609 | 0.8571 | 0.4000 |
| Nome + descrizione | 0.75 | 3 | 3 | 4 | 0.5000 | 0.4286 | 0.4615 |

La migliore configurazione semantica sul test set è risultata:

`nome + descrizione`

con:

- **Precision = 0.5000**
- **Recall = 0.4286**
- **F1-score = 0.4615**

---

## Analisi dei risultati degli embeddings

### Solo nome

La configurazione basata esclusivamente sul nome non individua nessuna delle 7 corrispondenze corrette sul test set.

Produce invece due falsi positivi:

- `annual_salary` ↔ `monthly_salary` con score `0.8970`
- `office_loc` ↔ `office_city` con score `0.8226`

Alcune coppie corrette ottengono invece valori molto inferiori alla soglia:

- `annual_salary` ↔ `compensation` = `0.5018`
- `emp_id` ↔ `employee_number` = `0.4318`
- `fname` ↔ `first_name` = `0.4226`

Ho osservato quindi che utilizzare soltanto nomi molto brevi non fornisce sempre al modello abbastanza contesto per riconoscere correttamente il significato dell'attributo.

Inoltre, nomi molto simili possono ottenere una similarità elevata anche quando rappresentano concetti differenti.

---

### Sola descrizione

L'utilizzo della sola descrizione permette di individuare 6 delle 7 corrispondenze corrette.

Il recall raggiunge quindi:

`0.8571`

Questo risultato è particolarmente interessante rispetto alle baseline lessicali, nelle quali le descrizioni realistiche avevano prodotto risultati molto più bassi.

Gli embeddings riescono quindi a sfruttare meglio descrizioni che esprimono lo stesso concetto utilizzando parole differenti.

La configurazione produce però 17 falsi positivi.

Questo mostra che il modello tende a considerare simili anche descrizioni appartenenti allo stesso contesto generale, ad esempio attributi relativi a dipendenti, reparti o sedi lavorative, pur rappresentando concetti differenti.

---

### Nome + descrizione

La combinazione di nome e descrizione rappresenta il miglior compromesso tra le configurazioni basate su embeddings.

Ottiene:

- TP = 3
- FP = 3
- FN = 4
- Precision = 0.5000
- Recall = 0.4286
- F1-score = 0.4615

Le corrispondenze corrette individuate sono:

- `dept` ↔ `department`
- `hire_date` ↔ `start_date`
- `office_loc` ↔ `work_location`

Rimangono però alcuni falsi positivi significativi:

- `annual_salary` ↔ `monthly_salary`
- `office_loc` ↔ `department`
- `office_loc` ↔ `office_city`

Il caso più interessante è:

`annual_salary` ↔ `monthly_salary`

che ottiene uno score pari a `0.7685` e supera la soglia di `0.75`.

La corrispondenza corretta:

`annual_salary` ↔ `compensation`

ottiene invece uno score pari a `0.7021` e rimane sotto la soglia.

Questo mostra che gli embeddings riescono a riconoscere la vicinanza semantica tra concetti, ma possono ancora avere difficoltà nel distinguere concetti fortemente correlati ma non equivalenti.

---

## Confronto tra baseline lessicale e embeddings

La migliore configurazione lessicale sul test set è:

`Levenshtein + nome + filtro sul tipo`

con:

`F1-score = 0.5000`

La migliore configurazione basata su embeddings è invece:

`Embeddings + nome + descrizione`

con:

`F1-score = 0.4615`

Gli embeddings non superano quindi la migliore baseline lessicale nel risultato complessivo.

Ho osservato però una differenza importante nel comportamento dei metodi.

La configurazione embeddings basata sulla sola descrizione riesce a recuperare 6 corrispondenze corrette su 7, mostrando una maggiore capacità di sfruttare informazioni semanticamente equivalenti espresse con parole differenti.

D'altra parte, produce anche molti falsi positivi tra concetti appartenenti allo stesso dominio.

Questo risultato mostra che una rappresentazione semantica non elimina automaticamente tutti gli errori dello schema matching e che può essere utile combinare l'informazione semantica con ulteriori vincoli o strategie di selezione.

---

## Considerazioni personali sugli embeddings

Prima di questo esperimento mi aspettavo che gli embeddings potessero migliorare nettamente le prestazioni rispetto alle metriche lessicali.

I risultati mostrano invece una situazione più complessa.

Ho osservato che gli embeddings sono effettivamente più adatti a confrontare descrizioni formulate con parole differenti, ma possono assegnare score elevati anche a concetti correlati che non devono essere considerati corrispondenti.

Il caso `annual_salary` ↔ `monthly_salary` è particolarmente significativo: il modello riconosce correttamente che entrambi gli attributi riguardano una retribuzione, ma non attribuisce abbastanza importanza alla differenza tra valore annuale e mensile.

Questo risultato mi ha fatto capire che riconoscere una vicinanza semantica non equivale necessariamente a riconoscere una corrispondenza di schema.

Questa osservazione può essere utilizzata come punto di partenza per una successiva estensione sperimentale.

---

## Estensioni sperimentali proposte

Dopo aver analizzato gli errori prodotti dalla baseline semantica basata su embeddings, ho individuato due possibili limiti dell'approccio attuale che vorrei analizzare con due esperimenti separati.

L'obiettivo non è modificare il modello utilizzato per generare gli embeddings, ma verificare se alcune informazioni o strategie aggiuntive possono migliorare la fase di selezione delle corrispondenze.

Il modello di riferimento rimane:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

con similarità coseno.

Le soglie già selezionate sul dataset `CUSTOMERS` verranno mantenute invariate, in modo da isolare il più possibile l'effetto delle due estensioni.

Le due possibilità che verranno analizzate sono:

1. selezione delle corrispondenze tramite miglior match reciproco;
2. integrazione di un filtro basato sul tipo degli attributi.

---

## Esperimento 1 - Miglior match reciproco

### Problema individuato

Nella baseline embeddings attuale ogni coppia di attributi viene valutata indipendentemente.

Se la similarità supera la soglia, la coppia viene accettata come corrispondenza.

Questo significa che uno stesso attributo può essere associato contemporaneamente a più attributi dell'altro schema.

Durante la valutazione su `EMPLOYEES` ho osservato, ad esempio, che `office_loc` viene associato a più candidati:

- `office_loc` ↔ `work_location`
- `office_loc` ↔ `department`
- `office_loc` ↔ `office_city`

La prima coppia rappresenta una corrispondenza corretta, mentre le altre sono falsi positivi.

Questo suggerisce che il problema non dipenda necessariamente soltanto dagli score prodotti dagli embeddings, ma anche dal fatto che il metodo attuale accetta tutte le coppie che superano la soglia senza confrontarle tra loro.

### Ipotesi

La mia ipotesi è che una strategia di selezione più restrittiva possa ridurre il numero di falsi positivi.

In particolare, una corrispondenza potrebbe essere considerata più affidabile quando i due attributi rappresentano reciprocamente il miglior candidato disponibile.

### Soluzione proposta

Verrà sperimentata una strategia di **miglior match reciproco**.

Una coppia:

`A ↔ B`

verrà accettata soltanto se:

1. lo score supera la soglia già selezionata su `CUSTOMERS`;
2. `B` è il candidato con similarità più alta per `A`;
3. `A` è il candidato con similarità più alta per `B`.

In questo modo non verranno più accettate automaticamente tutte le coppie sopra soglia.

### Limite atteso

Questa strategia non garantisce necessariamente un miglioramento.

In alcuni casi il candidato con score più alto può essere proprio quello sbagliato.

Ad esempio, nella configurazione embeddings `nome + descrizione`:

`annual_salary` ↔ `monthly_salary`

ottiene uno score più alto rispetto a:

`annual_salary` ↔ `compensation`

anche se la seconda coppia rappresenta la corrispondenza presente nella ground truth.

L'esperimento permetterà quindi di capire se il problema principale riguarda la selezione delle corrispondenze oppure gli score prodotti dal modello stesso.

---

## Esperimento 2 - Embeddings con filtro sul tipo

### Problema individuato

Gli embeddings vengono calcolati utilizzando informazioni testuali, ma non utilizzano direttamente il tipo strutturale degli attributi.

Di conseguenza, due attributi possono ottenere una similarità semantica elevata anche quando i rispettivi tipi sono incompatibili.

Nelle baseline lessicali ho già osservato che il filtro sul tipo può ridurre alcuni falsi positivi, soprattutto quando viene utilizzato insieme a Levenshtein.

Vorrei quindi verificare se lo stesso principio può essere utile anche con gli embeddings.

### Ipotesi

La mia ipotesi è che l'informazione sul tipo possa essere utilizzata come vincolo aggiuntivo per eliminare alcune corrispondenze semanticamente plausibili ma strutturalmente incompatibili.

In questo modo gli embeddings fornirebbero l'informazione semantica, mentre il tipo fornirebbe un controllo strutturale aggiuntivo.

### Soluzione proposta

Prima di accettare una coppia verrà verificata la compatibilità dei tipi.

La prima versione dell'esperimento utilizzerà lo stesso filtro rigido già impiegato nelle baseline lessicali:

```python
if tipo_a != tipo_b:
    continue
  ```

Solo le coppie con tipo uguale potranno quindi essere valutate come possibili corrispondenze.

Le soglie già selezionate per le configurazioni embeddings resteranno invariate.

### Limite atteso

Il filtro sul tipo può eliminare soltanto errori che coinvolgono attributi con tipi differenti.

Non può invece risolvere casi come:

`annual_salary` ↔ `monthly_salary`

perché entrambi gli attributi sono di tipo `FLOAT`.

---

## Protocollo sperimentale

Per entrambi gli esperimenti verrà mantenuta invariata la baseline embeddings originale.

In particolare non verranno modificati:

- il modello `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
- la similarità coseno;
- le tre configurazioni `solo nome`, `sola descrizione` e `nome + descrizione`;
- le soglie già selezionate sul dataset `CUSTOMERS`.

Le due estensioni verranno analizzate separatamente, in modo da poter osservare il contributo specifico di ciascuna modifica.

Il confronto sarà quindi effettuato tra:

- baseline embeddings originale;
- embeddings + miglior match reciproco;
- embeddings + filtro sul tipo.

---

## Criterio di valutazione

Per valutare le due estensioni verranno utilizzate le stesse metriche impiegate negli esperimenti precedenti:

- True Positive (TP);
- False Positive (FP);
- False Negative (FN);
- Precision;
- Recall;
- F1-score.

Oltre alle metriche complessive, verranno analizzate anche le singole corrispondenze aggiunte, eliminate o mantenute dalle nuove strategie.

Presterò particolare attenzione ad alcuni errori già osservati nella baseline embeddings, come:

- `annual_salary` ↔ `monthly_salary`;
- `annual_salary` ↔ `compensation`;
- `office_loc` ↔ `work_location`;
- `office_loc` ↔ `office_city`;
- `home_city` ↔ `office_city`.

Per il miglior match reciproco verificherò soprattutto se la riduzione del numero di corrispondenze candidate permette di diminuire i falsi positivi senza causare una perdita eccessiva di veri positivi.

Per il filtro sul tipo verificherò invece quanti falsi positivi vengono eliminati grazie all'informazione strutturale e quali errori rimangono perché coinvolgono attributi dello stesso tipo.

Un eventuale peggioramento delle metriche verrà comunque considerato un risultato utile, perché permetterà di capire meglio se il limite dipende dalla fase di selezione, dall'assenza di informazioni strutturali oppure direttamente dagli score prodotti dagli embeddings.

## Obiettivo dell'analisi

Con questi due esperimenti voglio capire meglio da dove derivano i falsi positivi osservati nella baseline embeddings.

In particolare, voglio distinguere tra:

1. errori dovuti al fatto che vengono accettate contemporaneamente troppe coppie sopra soglia;
2. errori che potrebbero essere eliminati utilizzando informazioni strutturali come il tipo;
3. errori dovuti direttamente alla rappresentazione semantica, quando il modello assegna uno score maggiore a una coppia semanticamente vicina ma non equivalente.

L'obiettivo non è necessariamente ottenere un miglioramento in entrambi gli esperimenti, ma capire quale componente del metodo contribuisce maggiormente agli errori osservati.

## File aggiunti per la baseline embeddings

- `selezione_parametri_embeddings.py`: selezione delle soglie sul development set `CUSTOMERS`;
- `selezione_parametri_embeddings.csv`: risultati completi delle soglie provate;
- `parametri_embeddings_selezionati.csv`: soglie selezionate per le tre configurazioni;
- `score_embeddings_customers.csv`: score di similarità di tutte le coppie del development set;
- `valutazione_finale_embeddings.py`: valutazione finale su `EMPLOYEES` con soglie bloccate;
- `valutazione_finale_embeddings.csv`: risultati riassuntivi del test finale;
- `dettagli_valutazione_embeddings.csv`: dettaglio delle predizioni e degli score sul test set.

---

## Esecuzione della baseline embeddings

Per selezionare le soglie sul development set:

```bash
py selezione_parametri_embeddings.py
```

Per eseguire la valutazione finale sul test set:

```bash
py valutazione_finale_embeddings.py
```


## File del progetto

- `baseline.py`: baseline basata sulla similarità di Jaccard.
- `baseline_levenshtein.py`: seconda baseline basata su Levenshtein.
- `schema_a.csv`: primo schema.
- `schema_b.csv`: secondo schema.
- `ground_truth.csv`: ground truth definita manualmente.
- `risultati_baseline.csv`: risultati del primo esperimento con soglia 0.50.
- `risultati_soglie.csv`: risultati della baseline Jaccard con più soglie.
- `risultati_levenshtein.csv`: risultati della baseline Levenshtein.
- `baseline_jaccard_type.py`: variante Jaccard con filtro preliminare sui tipi.
- `baseline_levenshtein_type.py`: variante Levenshtein con filtro preliminare sui tipi.
- `risultati_jaccard_type.csv`: risultati di Jaccard con filtro sui tipi.
- `risultati_levenshtein_type.csv`: risultati di Levenshtein con filtro sui tipi.
- `baseline_jaccard_description.py`: Jaccard su nome e descrizione.
- `baseline_levenshtein_description.py`: Levenshtein su nome e descrizione.
- `risultati_jaccard_description.csv`: risultati della configurazione Jaccard con descrizioni.
- `risultati_levenshtein_description.csv`: risultati della configurazione Levenshtein con descrizioni.
- `selezione_parametri_description.py`: selezione di pesi e soglie sul development set CUSTOMERS.
- `selezione_parametri_description.csv`: risultati delle configurazioni provate durante la selezione dei parametri.
- `valutazione_finale_description.py`: valutazione con parametri bloccati sul test set EMPLOYEES.
- `valutazione_finale_description.csv`: risultati finali della valutazione su EMPLOYEES.
- selezione_parametri_lessicali.py: selezione delle soglie e dei parametri sul development set CUSTOMERS;
- selezione_parametri_lessicali.csv: risultati completi della fase di selezione;
- parametri_lessicali_selezionati.csv: parametri scelti per ogni configurazione;
- valutazione_finale_lessicale.py: valutazione finale con parametri bloccati su EMPLOYEES;
- valutazione_finale_lessicale.csv: tabella riassuntiva dei risultati finali;
- dettagli_valutazione_lessicale.csv: dettaglio delle coppie predette, con score ed esito.

---

## Requisiti

È richiesto Python 3.

Non vengono utilizzate librerie Python esterne.

---

## Esecuzione

Per eseguire Jaccard:

```bash
py baseline.py


Per eseguire Levenshtein :
``` bash
py baseline_levenshtein.py


Per eseguire Jaccard con filtro sui tipi:

```bash
py baseline_jaccard_type.py



Per eseguire Levenshtein con filtro sui tipi:
``` bash
py baseline_levenshtein_type.py



Per eseguire Jaccard con nome e descrizione:

```bash
py baseline_jaccard_description.py




Per eseguire Levenshtein con nome e descrizione:

```bash
py baseline_levenshtein_description.py


### Selezione dei parametri sul development set

```bash
py selezione_parametri_description.py



### Valutazione dei parametri sul test set

```bash
py valutazione_finale_description.py



Selezione dei parametri sul development set

py selezione_parametri_lessicali.py


Valutazione finale sul test set

py valutazione_finale_lessicale.py