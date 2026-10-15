# Piano di validazione esterna

## Obiettivo

Dopo gli esperimenti svolti sui dataset sintetici `CUSTOMERS` ed `EMPLOYEES`, voglio verificare se i metodi sviluppati riescono a generalizzare su un dataset pubblico esterno.

Il dataset `EMPLOYEES` non verrà più utilizzato per modificare soglie, parametri o regole, perché è già stato analizzato durante lo sviluppo delle estensioni sperimentali.

Per questo motivo, in questa fase tutti i parametri già scelti vengono considerati fissati prima dell'esecuzione sul nuovo dataset.

---

## Dataset scelto

Ho scelto il dataset pubblico **MIMIC-III → OMOP**.

Il repository pubblico mette a disposizione gli schemi completi di MIMIC-III e OMOP e una gold-standard mapping tra i due schemi.

La scelta è motivata dal fatto che il dataset:

- è pubblico e indipendente dai dataset sintetici utilizzati durante lo sviluppo;
- dispone di una ground truth già definita;
- permette quindi di valutare i matcher senza costruire manualmente le corrispondenze corrette;
- rappresenta uno scenario più realistico e complesso rispetto a `CUSTOMERS` ed `EMPLOYEES`;
- è stato utilizzato in lavori di ricerca sullo schema matching.

Il mio obiettivo non è scegliere un dataset che favorisca gli embeddings, ma utilizzare un benchmark esterno per verificare se i metodi e i parametri definiti in precedenza riescono a generalizzare.

---

## Protocollo sperimentale

Il dataset MIMIC-III → OMOP verrà utilizzato come dataset di validazione esterna.

Le soglie e i parametri sviluppati sui dataset precedenti non verranno modificati dopo aver osservato i risultati.

La ground truth verrà utilizzata soltanto per il calcolo delle metriche finali.

I metodi verranno quindi eseguiti con gli stessi parametri definiti in precedenza.

---

## Metodi da confrontare

### 1. Migliore baseline lessicale

La migliore baseline lessicale ottenuta negli esperimenti precedenti è:

`Levenshtein + filtro sul tipo`

Soglia fissata:

`0.33`

La similarità viene calcolata sui nomi degli attributi.

Una coppia viene considerata soltanto se i due attributi hanno lo stesso tipo.

---

### 2. Embeddings - solo nome

Modello utilizzato:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Rappresentazione:

solo il nome dell'attributo.

Soglia fissata:

`0.80`

---

### 3. Embeddings - sola descrizione

Modello utilizzato:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Rappresentazione:

solo la descrizione dell'attributo.

Soglia fissata:

`0.65`

---

### 4. Embeddings - nome + descrizione

Modello utilizzato:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Rappresentazione:

nome dell'attributo seguito dalla descrizione.

Soglia fissata:

`0.75`

---

### 5. Embeddings + filtro sul tipo

Alle configurazioni con embeddings verrà applicato anche il filtro rigido sul tipo già utilizzato negli esperimenti precedenti.

La regola è:

```python
if tipo_a != tipo_b:
    continue
```