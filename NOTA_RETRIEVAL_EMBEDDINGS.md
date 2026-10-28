# Nota esplorativa sul retrieval con embeddings

## Risultati complessivi

L'esperimento è stato svolto senza applicare soglie di similarità. Per ogni attributo MIMIC sono stati ordinati tutti i target OMOP in base alla similarità cosine e si è verificato se la corrispondenza corretta comparisse al primo posto, nei primi 5 candidati o nei primi 10.

I risultati ottenuti sono:

| Rappresentazione | Recall@1 | Recall@5 | Recall@10 |
|---|---:|---:|---:|
| Solo nome | 0.0327 (5/153) | 0.2614 (40/153) | 0.3007 (46/153) |
| Sola descrizione | 0.0588 (9/153) | 0.1438 (22/153) | 0.2092 (32/153) |
| Nome + descrizione | 0.0915 (14/153) | 0.2092 (32/153) | 0.3268 (50/153) |
| Contesto tabella | 0.0654 (10/153) | 0.2680 (41/153) | 0.4118 (63/153) |

La rappresentazione `nome + descrizione` ottiene il Recall@1 più elevato, recuperando 14 delle 153 corrispondenze corrette al primo posto.

La rappresentazione che include il contesto della tabella ottiene invece i risultati migliori a Recall@5 e Recall@10. In particolare, recupera 41 corrispondenze nei primi 5 candidati e 63 nei primi 10.

Rispetto a `nome + descrizione`, il contesto della tabella porta quindi 13 corrispondenze corrette aggiuntive nella top-10, passando da 50 a 63.

Questo risultato suggerisce che l'aggiunta del nome della tabella non rende necessariamente più precisa la prima scelta, ma può essere utile per portare il target corretto all'interno di un insieme ristretto di candidati.

## Limite della configurazione sola descrizione

Delle 153 corrispondenze della ground truth, 54 coinvolgono almeno una descrizione mancante.

La configurazione `sola_descrizione` può quindi valutare completamente soltanto 99 delle 153 corrispondenze.

Il recall viene comunque calcolato sull'intera ground truth, come stabilito nella revisione precedente.

Di conseguenza, anche in condizioni ideali, la configurazione basata esclusivamente sulle descrizioni presenta un limite strutturale, perché 54 corrispondenze non dispongono delle informazioni necessarie per essere recuperate.

Il massimo teorico di recall per questa configurazione, considerando questa limitazione, sarebbe pari a:

`99 / 153 = 0.6471`

Questo valore non rappresenta un risultato ottenuto dal modello, ma soltanto il limite massimo imposto dalla disponibilità delle descrizioni.

## Analisi qualitativa di corrispondenze recuperate

### 1. NOTEEVENTS.TEXT → NOTE.NOTE_TEXT

Questa corrispondenza viene recuperata al rango 1 con tutte le rappresentazioni:

- solo nome: rango 1;
- sola descrizione: rango 1;
- nome + descrizione: rango 1;
- contesto tabella: rango 1.

Con il contesto della tabella la similarità raggiunge 0.960222.

Si tratta quindi di un caso in cui il legame tra sorgente e target è abbastanza evidente da essere riconosciuto anche senza informazioni strutturali aggiuntive.

Questo esempio mostra che alcune corrispondenze dirette possono essere individuate correttamente già al primo stadio di retrieval.

### 2. D_ITEMS.LABEL → CONCEPT.CONCEPT_NAME

Questo caso mostra invece un forte effetto positivo del contesto della tabella.

I ranghi sono:

- solo nome: 43;
- sola descrizione: 44;
- nome + descrizione: 161;
- contesto tabella: 1.

Con la nuova rappresentazione il target corretto passa quindi da posizioni molto basse al primo posto.

La similarità con `CONCEPT.CONCEPT_NAME` è pari a 0.743928.

Questo è uno degli esempi più chiari in cui l'informazione relativa alla tabella sembra fornire al modello un contesto utile per interpretare correttamente una colonna con un nome relativamente generico come `LABEL`.

### 3. LABEVENTS.ITEMID → MEASUREMENT.MEASUREMENT_CONCEPT_ID

Anche questo caso migliora con l'aggiunta del contesto.

I ranghi ottenuti sono:

- solo nome: 218;
- sola descrizione: 46;
- nome + descrizione: 12;
- contesto tabella: 8.

La nuova rappresentazione porta quindi per la prima volta il target corretto all'interno della top-10.

Tra i candidati con score superiore compaiono diversi attributi legati a `SPECIMEN` e `MEASUREMENT`, quindi gli embeddings sembrano individuare l'area semantica corretta ma non riescono a scegliere immediatamente il target esatto.

Questo è precisamente il tipo di situazione in cui il retrieval potrebbe essere utile: il target corretto è presente tra pochi candidati e potrebbe essere successivamente valutato da un metodo più preciso.

### 4. ADMISSIONS.ETHNICITY → PERSON.ETHNICITY_CONCEPT_ID

Questa corrispondenza viene recuperata molto bene da diverse rappresentazioni:

- solo nome: rango 1;
- sola descrizione: rango 146;
- nome + descrizione: rango 1;
- contesto tabella: rango 2.

Con il contesto della tabella il primo candidato diventa `PERSON.RACE_CONCEPT_ID`, mentre il target corretto `PERSON.ETHNICITY_CONCEPT_ID` compare subito dopo.

Questo caso è interessante perché mostra un limite degli embeddings: concetti semanticamente vicini, come race ed ethnicity, possono ricevere punteggi molto simili anche se non rappresentano esattamente la stessa corrispondenza.

Il retrieval è comunque utile, perché il target corretto compare tra i primi candidati e potrebbe essere distinto in una seconda fase.

## Analisi di corrispondenze rimaste fuori dalla top-10

### 5. CHARTEVENTS.ITEMID → MEASUREMENT.MEASUREMENT_CONCEPT_ID

I ranghi sono:

- solo nome: 218;
- sola descrizione: 46;
- nome + descrizione: 12;
- contesto tabella: 19.

Il target corretto rimane quindi fuori dalla top-10 anche con il contesto della tabella.

È interessante confrontarlo con `LABEVENTS.ITEMID`, che verso lo stesso target raggiunge invece il rango 8 con il contesto.

Questo mostra che la stessa tipologia di mapping può essere più o meno facile da recuperare a seconda della tabella sorgente.

Nel caso di `CHARTEVENTS.ITEMID`, diversi attributi semanticamente collegati a concetti, identificatori e misurazioni ricevono score superiori al target corretto.

### 6. CHARTEVENTS.VALUENUM → MEASUREMENT.VALUE_AS_NUMBER

In questo caso il contesto della tabella peggiora il ranking.

I risultati sono:

- solo nome: rango 2;
- sola descrizione: rango 10;
- nome + descrizione: rango 1;
- contesto tabella: rango 16.

Questa corrispondenza dimostra che aggiungere più contesto non produce sempre un miglioramento.

Con `nome + descrizione` il target corretto viene individuato al primo posto, mentre la rappresentazione con la tabella introduce informazioni aggiuntive che modificano la rappresentazione semantica e fanno salire altri candidati.

Il contesto deve quindi essere considerato utile in media per il retrieval, ma non universalmente migliore per ogni singola corrispondenza.

### 7. ADMISSIONS.ADMITTIME → VISIT_OCCURRENCE.VISIT_START_DATETIME

Questa corrispondenza rimane fuori dalla top-10 in tutte le configurazioni disponibili:

- solo nome: rango 122;
- sola descrizione: non valutabile;
- nome + descrizione: rango 51;
- contesto tabella: rango 29.

La configurazione `sola_descrizione` non può valutarla perché la descrizione del target è mancante.

Con il contesto della tabella il rango migliora rispetto a solo nome e nome + descrizione, ma rimane comunque lontano dalla top-10.

Tra i primi candidati compaiono però attributi come `VISIT_START_DATE`, `VISIT_END_DATE` e altri campi temporali relativi alle visite.

Questo suggerisce che il modello individua correttamente l'area semantica temporale e relativa alle visite, ma non riesce a distinguere con sufficiente precisione il campo `DATETIME` corretto.

## Interpretazione

L'esperimento mostra che gli embeddings hanno una capacità limitata di individuare direttamente il target corretto al primo posto.

Il miglior Recall@1 è infatti pari a 0.0915.

Il comportamento cambia però considerando un insieme più ampio di candidati.

La rappresentazione con il contesto della tabella raggiunge:

- Recall@5 = 0.2680;
- Recall@10 = 0.4118.

Questo significa che 63 delle 153 corrispondenze corrette si trovano entro i primi 10 candidati.

Il risultato non è sufficiente per utilizzare gli embeddings come unico sistema di schema matching, perché 90 corrispondenze restano comunque fuori dalla top-10.

Tuttavia, il miglioramento osservato a Recall@10 indica che gli embeddings possono avere un ruolo utile come primo stadio di retrieval.

In particolare, nei casi in cui il target corretto compare tra pochi candidati semanticamente vicini, una seconda fase più precisa potrebbe confrontare individualmente queste coppie.

Un possibile sviluppo successivo sarebbe quindi:

`attributo sorgente → embeddings → primi k candidati → metodo di selezione più preciso`

Il secondo metodo potrebbe essere più costoso perché verrebbe applicato soltanto a un numero limitato di candidati e non a tutte le 425 colonne OMOP.

L'esperimento rimane comunque esplorativo, poiché il benchmark MIMIC-OMOP era già stato analizzato nelle fasi precedenti e i risultati non vengono utilizzati per modificare o ottimizzare retroattivamente le rappresentazioni.