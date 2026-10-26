# Piano esperimento esplorativo: retrieval con embeddings

## 1. Obiettivo

Questa attività ha carattere esplorativo, perché il benchmark MIMIC-III → OMOP
è già stato analizzato nelle fasi precedenti.

L'obiettivo non è utilizzare gli embeddings per decidere direttamente il match
finale, ma verificare se riescano almeno a recuperare il target corretto tra
i primi candidati più simili.

Per ogni attributo sorgente MIMIC verranno quindi ordinati gli attributi target
OMOP in base alla similarità cosine, senza applicare alcuna soglia.

Verrà poi verificato se ogni corrispondenza della ground truth compare:

- al primo posto;
- nei primi 5 candidati;
- nei primi 10 candidati.

Le metriche utilizzate saranno quindi:

- Recall@1;
- Recall@5;
- Recall@10.


## 2. Ground truth

La valutazione utilizza la stessa ground truth della validazione precedente:

- 153 corrispondenze positive utilizzabili.

Ogni corrispondenza della ground truth viene considerata individualmente.

Il denominatore del recall rimane sempre pari a 153, anche quando una
configurazione non dispone delle informazioni necessarie per valutare una
determinata corrispondenza.


## 3. Rappresentazioni già disponibili

Verranno confrontate tre rappresentazioni già utilizzate negli esperimenti
precedenti.


### Solo nome

Testo fornito al modello:

`ColumnName`

Esempio:

`value num`


### Sola descrizione

Testo fornito al modello:

`ColumnDesc`

La gestione delle descrizioni mancanti rimane quella definita nella revisione
precedente.

Se manca la descrizione dell'attributo sorgente, non è possibile produrre una
classifica valida per quella sorgente nella configurazione `sola_descrizione`.

Se manca la descrizione di un attributo target, quel target non viene
considerato tra i candidati basati sulla sola descrizione.

La ground truth rimane comunque invariata e le corrispondenze non recuperabili
continuano quindi a incidere sul recall.


### Nome + descrizione

Testo fornito al modello:

`ColumnName + ". " + ColumnDesc`

Se la descrizione è assente, viene utilizzato il solo nome della colonna,
come già avveniva nella pipeline precedente.


## 4. Nuova rappresentazione con contesto della tabella

Come nuova rappresentazione propongo di combinare:

- nome della tabella;
- nome della colonna;
- descrizione della colonna.

Il testo sarà costruito nella forma:

`Table: <TableName>. Column: <ColumnName>. Description: <ColumnDesc>`

Per esempio:

`Table: CHARTEVENTS. Column: VALUENUM. Description: Numeric value of the event.`

Se la descrizione della colonna è mancante, verranno comunque utilizzati il
nome della tabella e il nome della colonna:

`Table: <TableName>. Column: <ColumnName>`


## 5. Motivazione della nuova rappresentazione

Ho scelto di aggiungere il nome della tabella perché alcuni attributi del
benchmark hanno nomi molto generici, come `VALUE`, `ID`, `DATE`, `CODE`
o nomi simili.

Il nome della colonna da solo può quindi non essere sufficiente a distinguere
il ruolo dell'attributo.

La tabella di appartenenza fornisce un'informazione aggiuntiva sul contesto
in cui la colonna viene utilizzata.

Per esempio, una colonna chiamata `VALUE` all'interno di una tabella relativa
a misurazioni cliniche può avere un significato diverso da una colonna con lo
stesso nome presente in un'altra parte dello schema.


## 6. Miglioramento atteso

Mi aspetto che l'aggiunta del contesto della tabella possa essere utile
soprattutto nei casi in cui il nome della colonna è poco informativo o
ambiguo.

Non mi aspetto necessariamente che il target corretto diventi sempre il primo
candidato.

L'ipotesi principale è che il contesto possa aumentare la probabilità che il
target corretto compaia almeno nei primi 5 o 10 candidati.

Per questo considero particolarmente importanti Recall@5 e Recall@10.

Se questi valori risultassero sensibilmente più alti di Recall@1, gli embeddings
potrebbero essere utili come primo stadio di retrieval, anche se non sono
sufficientemente precisi per prendere autonomamente la decisione finale.


## 7. Modello

Verrà mantenuto lo stesso modello utilizzato negli esperimenti precedenti:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Non verrà introdotto un nuovo modello.


## 8. Similarità

Per tutte le rappresentazioni verrà utilizzata la similarità cosine tra gli
embeddings.

Non verrà applicata alcuna soglia.

Per ogni attributo sorgente verranno considerati i target in ordine decrescente
di similarità.


## 9. Gestione delle parità nel ranking

Per evitare che il risultato dipenda dall'ordine delle righe del CSV, le
parità verranno gestite utilizzando una tolleranza di `1e-7`.

Il rango di un target sarà determinato dal numero di candidati che possiedono
un punteggio realmente superiore.

In questo modo, due target con punteggio equivalente entro la tolleranza
riceveranno lo stesso rango.

Una corrispondenza sarà quindi considerata recuperata a Recall@k se il rango
del target corretto è minore o uguale a k.

Questa scelta evita di decidere arbitrariamente quale candidato inserire o
escludere quando una parità cade esattamente al limite della top-k.


## 10. Metriche

Per ciascuna delle quattro rappresentazioni verranno calcolati:

- Recall@1;
- Recall@5;
- Recall@10.

La formula utilizzata sarà:

`Recall@k = corrispondenze corrette con rango <= k / 153`

La valutazione rimarrà quindi riferita all'intera ground truth.


## 11. Limite della configurazione sola descrizione

Delle 153 corrispondenze della ground truth, 54 coinvolgono almeno una
descrizione mancante.

Queste corrispondenze non possono essere recuperate correttamente utilizzando
esclusivamente le descrizioni.

La configurazione `sola_descrizione` presenta quindi un limite strutturale
indipendente dalla qualità del modello.

Questo limite verrà mantenuto nella valutazione, senza eliminare tali
corrispondenze dal denominatore del recall.


## 12. Output previsti

L'esperimento produrrà:

- un CSV riepilogativo con Recall@1, Recall@5 e Recall@10 per ogni
  rappresentazione;
- un CSV con il rango del target corretto per ogni corrispondenza della
  ground truth;
- un CSV con i primi 10 candidati per ogni attributo sorgente e per ogni
  rappresentazione;
- una breve analisi qualitativa di almeno cinque corrispondenze.

L'analisi qualitativa comprenderà sia casi in cui il target corretto viene
recuperato nei primi candidati sia casi in cui rimane fuori dalla top-10.


## 13. Interpretazione prevista

L'esperimento non verrà utilizzato per ottimizzare ulteriormente i parametri
sul benchmark MIMIC-OMOP.

L'obiettivo è esclusivamente esplorativo.

Se Recall@5 o Recall@10 risultassero sufficientemente superiori a Recall@1,
questo suggerirebbe che gli embeddings possono essere utilizzati come primo
stadio di retrieval.

In un eventuale sviluppo successivo, i pochi candidati recuperati potrebbero
essere sottoposti a un metodo più preciso e più costoso, come un cross-encoder
o un modello linguistico, per effettuare la selezione finale.