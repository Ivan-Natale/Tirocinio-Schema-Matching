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