# Piano esperimento esplorativo: fusione delle graduatorie di retrieval

## 1. Obiettivo

L'obiettivo di questo esperimento esplorativo è verificare se sia possibile combinare efficacemente le due rappresentazioni:

- `nome + descrizione`;
- `contesto della tabella`.

Negli esperimenti precedenti le due rappresentazioni hanno mostrato comportamenti differenti e la loro unione delle top-10 permette di recuperare più corrispondenze corrette.

Una semplice unione, però, può produrre fino a 20 candidati per ogni attributo sorgente.

L'obiettivo di questo esperimento è quindi costruire una graduatoria combinata mantenendo un budget effettivo massimo di 10 candidati per ogni attributo MIMIC.


## 2. Rappresentazioni considerate

Verranno confrontate le seguenti rappresentazioni.

### Nome + descrizione

Testo:

`<ColumnName>. <ColumnDesc>`

Se la descrizione è mancante viene utilizzato soltanto il nome della colonna.


### Contesto della tabella

Testo:

`Table: <TableName>. Column: <ColumnName>. Description: <ColumnDesc>`

Se la descrizione è mancante vengono utilizzati nome della tabella e nome della colonna.


### Controllo senza tabella

Per verificare il contributo specifico del nome della tabella verrà aggiunta una rappresentazione con lo stesso formato testuale della configurazione precedente, ma senza il contesto della tabella.

Testo:

`Column: <ColumnName>. Description: <ColumnDesc>`

Se la descrizione è mancante verrà utilizzato:

`Column: <ColumnName>`

Il confronto tra questa configurazione e `contesto della tabella` permetterà di distinguere l'effetto del nome della tabella dall'effetto delle etichette testuali `Column:` e `Description:`.


## 3. Fusione delle due graduatorie

Per combinare le graduatorie di `nome + descrizione` e `contesto della tabella` utilizzerò una strategia basata sul rango.

Per ogni target OMOP verrà considerata la posizione ottenuta nelle due graduatorie.

Il punteggio combinato sarà calcolato attraverso una Reciprocal Rank Fusion:

`score_fusione = 1 / (60 + rango_nome_descrizione) + 1 / (60 + rango_contesto)`

Un candidato che compare in posizione alta in entrambe le graduatorie riceverà quindi un punteggio maggiore.

La fusione utilizza i ranghi e non confronta direttamente i valori di similarità delle due rappresentazioni.

Dopo il calcolo dello score di fusione, tutti i target verranno ordinati e verranno mantenuti al massimo i primi 10 candidati.


## 4. Motivazione della regola di fusione

Ho scelto una fusione basata sui ranghi perché le due rappresentazioni producono score di similarità che non devono necessariamente avere la stessa distribuzione.

Utilizzare direttamente la media delle due similarità potrebbe quindi dare un peso maggiore alla rappresentazione che produce valori numericamente più elevati.

La fusione dei ranghi permette invece di combinare le due graduatorie considerando principalmente la posizione relativa dei candidati.

L'ipotesi è che un target che occupa una buona posizione in entrambe le rappresentazioni sia un candidato più affidabile rispetto a un target che compare in posizione elevata soltanto in una delle due.


## 5. Gestione delle parità

Nell'esperimento precedente più candidati con lo stesso punteggio potevano ricevere lo stesso rango.

Di conseguenza, una top-10 poteva contenere più di 10 candidati effettivi.

In questo esperimento ogni graduatoria dovrà invece contenere al massimo 10 candidati.

I candidati verranno ordinati utilizzando questa regola:

1. punteggio principale decrescente;
2. in caso di parità, punteggio secondario decrescente;
3. se la parità rimane, identificatore completo del target in ordine alfabetico.

Per le rappresentazioni singole:

- il punteggio principale è la similarità cosine;
- in caso di identica similarità viene utilizzato l'identificatore del target in ordine alfabetico.

Per la graduatoria combinata:

- il punteggio principale è lo score di fusione;
- in caso di parità viene utilizzata la media delle similarità ottenute da `nome + descrizione` e `contesto della tabella`;
- se rimane ancora una parità viene utilizzato l'identificatore del target in ordine alfabetico.

In questo modo il risultato è deterministico e ogni attributo sorgente presenta al massimo 10 candidati.


## 6. Metriche

Per ogni rappresentazione verranno calcolati:

- Recall@1;
- Recall@5;
- Recall@10.

Il recall continuerà a essere calcolato rispetto all'intera ground truth di 153 corrispondenze.

La top-k sarà definita sul numero effettivo di candidati e non sul numero di ranghi.

Di conseguenza:

- Recall@1 considera esattamente il primo candidato;
- Recall@5 considera al massimo i primi 5 candidati;
- Recall@10 considera al massimo i primi 10 candidati.


## 7. Confronti previsti

Verranno confrontati:

1. `nome + descrizione`;
2. `contesto della tabella`;
3. `controllo senza tabella`;
4. `fusione nome_descrizione + contesto_tabella`.

Le rappresentazioni singole verranno ricalcolate utilizzando la nuova gestione deterministica delle parità, in modo che il confronto utilizzi lo stesso budget effettivo di candidati.


## 8. Analisi dei casi guadagnati e persi

Oltre alle metriche aggregate verranno analizzate le corrispondenze modificate dalla fusione.

Saranno considerati:

### Casi guadagnati

Corrispondenze corrette che non erano presenti nella top-k di una rappresentazione di riferimento ma entrano nella graduatoria combinata.

### Casi persi

Corrispondenze corrette presenti nella top-k di almeno una rappresentazione singola ma escluse dalla graduatoria combinata a causa del limite massimo di candidati.

Questa analisi permetterà di capire se la fusione produce un miglioramento reale o se il maggiore recall viene ottenuto sacrificando altri casi utili.


## 9. Miglioramento atteso

Mi aspetto che la fusione permetta di sfruttare la complementarità tra `nome + descrizione` e `contesto della tabella`.

Non mi aspetto necessariamente un miglioramento di Recall@1, perché la fusione è pensata soprattutto per costruire una lista di candidati.

L'aspettativa principale riguarda quindi Recall@5 e Recall@10.

L'obiettivo è verificare se sia possibile recuperare più corrispondenze corrette rispetto alle rappresentazioni singole mantenendo comunque un massimo di 10 candidati per ogni attributo sorgente.


## 10. Natura dell'esperimento

Il benchmark MIMIC-OMOP è già stato analizzato nelle fasi precedenti.

Questo esperimento viene quindi considerato esclusivamente esplorativo.

I risultati non verranno utilizzati per modificare retroattivamente le rappresentazioni o ottimizzare parametri sulla stessa ground truth.

## 11. Seconda strategia esplorativa: fusione basata sul miglior rango

Dopo la prima esecuzione con Reciprocal Rank Fusion è stato osservato che RRF può penalizzare candidati che si trovano in una posizione molto alta in una delle due graduatorie ma molto bassa nell'altra.

Per esempio, una corrispondenza può essere classificata al primo posto dalla rappresentazione con contesto della tabella ma essere molto più distante nella graduatoria nome + descrizione. La fusione RRF, premiando soprattutto l'accordo tra le due graduatorie, può far scendere questo candidato fuori dalla top-10.

A partire da questa osservazione ho deciso di sperimentare una seconda strategia di fusione che dia maggiore importanza al metodo che assegna al candidato il rango migliore.

Per ogni target considero:

`best_rank = min(rango_nome_descrizione, rango_contesto_tabella)`

La graduatoria viene quindi ordinata utilizzando:

1. il miglior rango tra le due rappresentazioni;
2. in caso di parità, il rango ottenuto nell'altra rappresentazione;
3. in caso di ulteriore parità, la media delle due similarità cosine;
4. infine, l'identificatore del target in ordine alfabetico.

L'obiettivo è evitare che una corrispondenza molto forte secondo una delle due rappresentazioni venga penalizzata eccessivamente dall'altra.

Questa seconda tecnica viene considerata un'estensione esplorativa post-hoc, perché è stata proposta dopo aver osservato il comportamento della fusione RRF. Non viene quindi presentata come una strategia definita a priori né utilizzata per reinterpretare gli esperimenti precedenti.