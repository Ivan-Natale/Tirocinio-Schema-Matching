# Schema Matching 

Prima sperimentazione di schema matching .

## Obiettivo

Confrontare gli attributi di due schemi tabellari utilizzando una baseline
lessicale basata sulla similarità di Jaccard.

## Metodo

I nomi degli attributi vengono suddivisi in parole utilizzando il carattere `_`.

La similarità di Jaccard è calcolata come:

numero di parole in comune / numero totale di parole diverse

In questa prima versione viene utilizzata una soglia pari a 0.50.

## File

- `baseline.py`: implementazione della baseline.
- `schema_a.csv`: primo schema.
- `schema_b.csv`: secondo schema.
- `ground_truth.csv`: corrispondenze corrette definite manualmente.
- `risultati_baseline.csv`: risultati ottenuti dalla baseline.

## Esecuzione

È richiesto Python 3.

Dal terminale:

```bash
py baseline.py