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

## File del progetto

- `baseline.py`: baseline basata sulla similarità di Jaccard.
- `baseline_levenshtein.py`: seconda baseline basata su Levenshtein.
- `schema_a.csv`: primo schema.
- `schema_b.csv`: secondo schema.
- `ground_truth.csv`: ground truth definita manualmente.
- `risultati_baseline.csv`: risultati del primo esperimento con soglia 0.50.
- `risultati_soglie.csv`: risultati della baseline Jaccard con più soglie.
- `risultati_levenshtein.csv`: risultati della baseline Levenshtein.

---

## Requisiti

È richiesto Python 3.

Non vengono utilizzate librerie Python esterne.

---

## Esecuzione

Per eseguire Jaccard:

```bash
py baseline.py