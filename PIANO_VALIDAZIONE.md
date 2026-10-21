# Piano di validazione esterna

## 1. Obiettivo

L'obiettivo della validazione esterna è verificare quanto i metodi sviluppati
nelle fasi precedenti generalizzino su un benchmark pubblico e più complesso,
senza modificare soglie o parametri dopo aver osservato i risultati.

I parametri sono stati scelti esclusivamente sul dataset di sviluppo CUSTOMERS.
EMPLOYEES è stato utilizzato come primo dataset di test e per l'analisi degli
errori, quindi non viene più utilizzato per ulteriori ottimizzazioni.

La validazione esterna viene eseguita sul benchmark MIMIC-III → OMOP.


## 2. Fonte del benchmark

Il benchmark è stato ottenuto dal repository pubblico:

`meniData1/MIMIC_2_OMOP`

Il repository contiene:

- lo schema MIMIC-III;
- lo schema OMOP;
- una gold-standard mapping tra i due schemi.

Il dataset è quello utilizzato nel lavoro:

E. Sheetrit, M. Brief, M. Mishaeli, O. Elisha,  
"ReMatch: Retrieval Enhanced Schema Matching with LLMs",  
arXiv:2403.01567, 2024.

Il repository non presenta una release numerata.

Per questo lavoro è stato utilizzato lo snapshot del branch `main`
scaricato per la validazione.

I tre file utilizzati sono:

- `data_validation/MIMIC_III_Schema.csv`
- `data_validation/OMOP_Schema.csv`
- `data_validation/MIMIC_to_OMOP_Mapping.csv`

Gli hash SHA256 dei file vengono riportati per identificare in modo
riproducibile la versione effettivamente utilizzata.


### Hash SHA256 dei file utilizzati

- `MIMIC_III_Schema.csv`  
  `9BAB4EB99742BCC08870A0231771B398AFCC6610ABA92F935A1D9EB2606F7FF8`

- `OMOP_Schema.csv`  
  `2784634D85B32F4F187ECADCF311BC57B04AA3BADD8552BF746CA65766D6A32A`

- `MIMIC_to_OMOP_Mapping.csv`  
  `6C685424EC44A65F716D94248A4B4B30A096004B6273E3FA0C997C039BE86A5A`


## 3. Motivazione della scelta

Ho scelto MIMIC-III → OMOP perché è un benchmark pubblico con una ground truth
disponibile e rappresenta un caso più realistico rispetto ai piccoli schemi
utilizzati durante lo sviluppo.

Il benchmark contiene nomi, descrizioni e tipi degli attributi ed è quindi
adatto al confronto tra:

- metodi lessicali;
- embeddings;
- filtri basati sui tipi;
- strategie di selezione dei match.

Inoltre, la presenza di schemi di dimensioni maggiori permette di verificare
la capacità dei metodi di generalizzare quando aumenta lo spazio dei candidati.


## 4. Dati effettivamente valutati

Dopo la lettura dei file:

- attributi MIMIC completi: 298;
- attributi MIMIC presenti nel mapping e valutati: 268;
- attributi OMOP validi: 425;
- corrispondenze positive della ground truth utilizzabili: 153;
- mapping positivi non risolti: 2.

I due mapping non risolti sono conservati separatamente nel file
`mapping_non_risolti.csv` e non vengono modificati manualmente.


## 5. Parametri fissati prima della validazione

I parametri utilizzati derivano dagli esperimenti precedenti e non vengono
modificati sulla base dei risultati ottenuti su MIMIC-OMOP.


### Levenshtein + filtro tipo esatto

- soglia: 0.33


### Embeddings

Modello:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Configurazioni e soglie:

- solo nome: 0.80
- sola descrizione: 0.65
- nome + descrizione: 0.75

Le soglie rimangono fisse durante tutta la validazione.


## 6. Metodi valutati

Vengono confrontati:

1. Levenshtein sul nome con filtro di tipo esatto;
2. embeddings solo nome;
3. embeddings sola descrizione;
4. embeddings nome + descrizione;
5. embeddings con filtro di tipo esatto;
6. embeddings con match reciproco;
7. embeddings con compatibilità per famiglie di tipi.

La compatibilità per famiglie di tipi è l'estensione aggiuntiva definita prima
della validazione esterna.

Le famiglie considerate sono:

- numerici;
- testuali;
- temporali;
- booleani;
- altri tipi.


## 7. Metriche

Per ogni configurazione vengono calcolati:

- True Positive (TP);
- False Positive (FP);
- False Negative (FN);
- Precision;
- Recall;
- F1-score.

La ground truth non viene modificata in funzione della disponibilità delle
descrizioni o delle possibilità del metodo.


## 8. Controllo delle descrizioni

Durante la revisione della pipeline è stato effettuato un censimento esplicito
delle descrizioni mancanti e duplicate.


### MIMIC

- colonne valutate: 268;
- descrizioni mancanti: 41;
- descrizioni presenti: 227;
- gruppi di descrizioni duplicate: 30;
- colonne coinvolte in descrizioni duplicate: 108.


### OMOP

- colonne valutate: 425;
- descrizioni mancanti: 116;
- descrizioni presenti: 309;
- gruppi di descrizioni duplicate: 5;
- colonne coinvolte in descrizioni duplicate: 11.

I risultati sono salvati nei file:

- `censimento_descrizioni.csv`;
- `descrizioni_mancanti.csv`;
- `descrizioni_duplicate.csv`.


## 9. Gestione delle descrizioni mancanti

Nella configurazione `sola_descrizione` una coppia di attributi viene valutata
soltanto se entrambe le descrizioni sono presenti.

Se almeno una delle due descrizioni è vuota:

- la coppia non viene confrontata per produrre un match;
- non viene generata una predizione positiva.

Non vengono aggiunte o ricostruite artificialmente descrizioni mancanti.

La ground truth rimane invece invariata.

Di conseguenza, se una corrispondenza corretta contiene almeno una descrizione
mancante, il metodo non può predirla e la coppia rimane un falso negativo.

In questo modo il recall continua a essere calcolato sull'intera ground truth.


## 10. Gestione delle parità nel match reciproco

Il match reciproco richiede che:

- il target sia tra i migliori candidati della sorgente;
- la sorgente sia tra i migliori candidati del target;
- la similarità superi la soglia fissata.

Nel caso in cui più candidati abbiano lo stesso punteggio massimo, non viene
scelto arbitrariamente il primo elemento incontrato nel CSV.

Tutti i candidati con score massimo entro una tolleranza di `1e-7` vengono
considerati a pari merito.

Le parità individuate vengono salvate nel file:

`parita_match_reciproco.csv`

Questa scelta evita che il risultato dipenda dall'ordine delle righe del file.


## 11. Limite del match reciproco nei mapping molti-a-uno

La gestione delle parità non risolve un limite più generale del criterio
reciproco.

La ground truth contiene casi in cui più attributi MIMIC corrispondono allo
stesso attributo OMOP.

Per esempio:

- `CHARTEVENTS.ITEMID`
- `LABEVENTS.ITEMID`
- `OUTPUTEVENTS.ITEMID`

possono convergere verso:

`MEASUREMENT.MEASUREMENT_CONCEPT_ID`

Se il target assegna punteggi differenti alle diverse sorgenti, il match
reciproco tende a mantenere soltanto quella con il punteggio maggiore.

Di conseguenza, una corrispondenza molti-a-uno corretta può essere eliminata
anche se rappresenta un mapping valido.

Il match reciproco deve quindi essere interpretato come una strategia utile
per aumentare la selettività, ma con un possibile costo in termini di recall.


## 12. Analisi qualitativa di mapping reali

La ground truth mostra che il benchmark comprende relazioni di natura diversa.


### Equivalenze dirette

`NOTEEVENTS.TEXT → NOTE.NOTE_TEXT`

I due attributi rappresentano direttamente il testo della nota.


`ADMISSIONS.ADMITTIME → VISIT_OCCURRENCE.VISIT_START_DATETIME`

Entrambi rappresentano il momento iniziale dell'ammissione o della visita.


`CHARTEVENTS.VALUENUM → MEASUREMENT.VALUE_AS_NUMBER`

Entrambi rappresentano il valore numerico di una misurazione.


### Mapping che richiedono trasformazioni o ricodifiche

`ADMISSIONS.ETHNICITY → PERSON.ETHNICITY_CONCEPT_ID`

La sorgente contiene una categoria relativa all'etnia, mentre OMOP richiede
l'identificatore di un concetto standard. È quindi necessaria una ricodifica.


`CHARTEVENTS.VALUEUOM → MEASUREMENT.UNIT_CONCEPT_ID`

L'unità della sorgente deve essere trasformata nel corrispondente concetto
standard OMOP.


`CHARTEVENTS.ITEMID → MEASUREMENT.MEASUREMENT_CONCEPT_ID`

L'identificatore interno utilizzato da MIMIC deve essere associato a un
concetto standard OMOP.

Questi esempi mostrano che il benchmark non contiene soltanto semplici
rinominazioni di attributi, ma anche corrispondenze che implicano una
trasformazione semantica o una ricodifica.


## 13. Scelte effettivamente adottate dopo il controllo della pipeline

Dopo il primo esperimento è stato individuato un problema nella gestione delle
descrizioni vuote.

La correzione non ha comportato alcuna modifica delle soglie.

Sono state adottate esclusivamente le seguenti modifiche metodologiche:

- censimento esplicito delle descrizioni mancanti e duplicate;
- esclusione delle coppie con descrizione mancante nella sola configurazione
  `sola_descrizione`;
- mantenimento dell'intera ground truth per il calcolo del recall;
- gestione esplicita delle parità nel match reciproco;
- documentazione dei mapping non risolti;
- analisi qualitativa di mapping diretti e mapping che richiedono trasformazioni.

Non sono stati introdotti nuovi modelli né sono stati modificati i parametri
per migliorare i risultati sul benchmark.


## 14. Risultati dopo la correzione

Tutte le configurazioni sono state rieseguite mantenendo le soglie già fissate
prima della validazione.

La correzione ha modificato in particolare i risultati della configurazione
`sola_descrizione`, mentre le configurazioni basate sul nome sono rimaste
invariate.


### Embeddings sola descrizione

- TP: 6
- FP: 111
- FN: 147
- Precision: 0.0513
- Recall: 0.0392
- F1: 0.0444


### Embeddings sola descrizione + filtro tipo esatto

- TP: 0
- FP: 10
- FN: 153
- F1: 0.0000


### Embeddings sola descrizione + match reciproco

- TP: 4
- FP: 25
- FN: 149
- F1: 0.0440


### Embeddings sola descrizione + famiglie di tipi

- TP: 6
- FP: 49
- FN: 147
- F1: 0.0577


## 15. Revisione delle conclusioni

Il risultato iniziale della configurazione `sola_descrizione` era fortemente
influenzato dal confronto tra descrizioni mancanti.

Dopo la correzione, i falsi positivi degli embeddings standard basati soltanto
sulla descrizione sono passati da 4864 a 111.

Non è quindi corretto attribuire l'elevato numero iniziale di falsi positivi
principalmente alla complessità semantica del dominio clinico.

Tuttavia, anche dopo la correzione, le prestazioni rimangono basse.

Rimangono quindi sostenute le seguenti osservazioni:

- le soglie selezionate sul dataset di sviluppo generalizzano poco al nuovo
  benchmark;
- nelle configurazioni embeddings, il filtro di tipo esatto risulta troppo
  rigido e non recupera alcun true positive;
- la compatibilità per famiglie di tipi è meno rigida del confronto esatto e,
  nella configurazione sola descrizione, riduce i falsi positivi da 111 a 49
  senza perdere ulteriori true positive;
- il match reciproco riduce sensibilmente i falsi positivi, ma può ridurre
  anche il recall;
- la ground truth comprende sia equivalenze dirette sia mapping che richiedono
  trasformazioni o ricodifiche, che non sono necessariamente catturabili con
  la sola similarità testuale.

Le precedenti conclusioni che attribuivano il forte peggioramento principalmente
alla similarità semantica tra descrizioni del dominio clinico vengono quindi
riviste.


## 16. Possibili sviluppi successivi

Prima di introdurre nuovi modelli, questa validazione viene considerata un
controllo della correttezza della pipeline esistente.

Come possibile sviluppo futuro, gli embeddings potrebbero essere utilizzati
come primo strumento di retrieval per individuare pochi candidati plausibili.

Nei casi ambigui, in cui più candidati presentano punteggi elevati o molto
vicini, un metodo più costoso potrebbe successivamente analizzare le singole
coppie.

Una seconda fase potrebbe utilizzare, per esempio, un cross-encoder o un
modello linguistico come reranker.

Questo consentirebbe di utilizzare il metodo più costoso soltanto sui casi
difficili e potrebbe essere particolarmente utile nei mapping molti-a-uno,
senza imporre direttamente una relazione uno-a-uno.