# Nota esplorativa sulla fusione delle graduatorie di retrieval

## 1. Obiettivo

L'obiettivo di questa iterazione è stato verificare se le due rappresentazioni `nome + descrizione` e `contesto della tabella` potessero essere combinate efficacemente mantenendo un budget massimo effettivo di 10 candidati per ogni attributo sorgente.

Sono state inoltre introdotte:

- una gestione deterministica delle parità;
- una rappresentazione di controllo con lo stesso formato testuale del contesto, ma senza il nome della tabella;
- due strategie di fusione: Reciprocal Rank Fusion e una seconda fusione basata sul miglior rango.

L'attività rimane esplorativa, perché il benchmark MIMIC-OMOP è già stato analizzato nelle iterazioni precedenti.

## 2. Gestione delle parità

Negli esperimenti precedenti candidati con lo stesso punteggio potevano condividere lo stesso rango. Di conseguenza, una top-10 poteva contenere più di 10 candidati effettivi.

In questa iterazione ogni graduatoria contiene invece al massimo 10 candidati.

Per le rappresentazioni singole i candidati vengono ordinati per:

1. similarità cosine decrescente;
2. in caso di parità, identificatore del target in ordine alfabetico.

In questo modo vengono assegnate posizioni uniche da 1 a 425 e Recall@10 considera realmente al massimo dieci candidati per sorgente.

## 3. Controllo senza contesto della tabella

Per distinguere il contributo del nome della tabella da quello del formato testuale è stata aggiunta una rappresentazione di controllo.

La rappresentazione con contesto utilizza:

`Table: <TableName>. Column: <ColumnName>. Description: <ColumnDesc>`

La rappresentazione di controllo utilizza invece:

`Column: <ColumnName>. Description: <ColumnDesc>`

Viene quindi mantenuto lo stesso formato con le etichette `Column:` e `Description:`, rimuovendo soltanto il nome della tabella.

## 4. Prima fusione: Reciprocal Rank Fusion

La prima strategia utilizzata è Reciprocal Rank Fusion, con:

`score = 1 / (60 + rank_nome_descrizione) + 1 / (60 + rank_contesto)`

La costante 60 è stata fissata prima dell'esecuzione e non ottimizzata sul benchmark.

RRF tende a premiare i candidati che occupano buone posizioni in entrambe le graduatorie.

In caso di parità nello score RRF vengono utilizzati:

1. media delle due similarità;
2. identificatore del target in ordine alfabetico.

## 5. Seconda fusione: miglior rango

Dopo la prima esecuzione con RRF ho osservato che questa strategia poteva penalizzare fortemente candidati classificati molto bene da una rappresentazione ma molto male dall'altra.

Per questo ho introdotto una seconda strategia esplorativa basata sull'idea di dare maggiore importanza al metodo che assegna al candidato la posizione migliore.

Per ogni candidato viene calcolato:

`best_rank = min(rank_nome_descrizione, rank_contesto)`

L'ordinamento utilizza quindi:

1. miglior rango tra le due rappresentazioni;
2. rango ottenuto nell'altra rappresentazione;
3. media delle due similarità;
4. identificatore del target in ordine alfabetico.

L'obiettivo è evitare che un candidato molto forte secondo una delle due rappresentazioni venga escluso perché l'altra lo posiziona molto più in basso.

Questa seconda strategia è stata introdotta dopo aver osservato i risultati di RRF e viene quindi considerata esplicitamente un'analisi post-hoc esplorativa.

## 6. Risultati

| Configurazione | Hit@1 | Recall@1 | Hit@5 | Recall@5 | Hit@10 | Recall@10 |
|---|---:|---:|---:|---:|---:|---:|
| Nome + descrizione | 14 | **0.0915** | 32 | 0.2092 | 50 | 0.3268 |
| Contesto tabella | 10 | 0.0654 | 41 | 0.2680 | **63** | **0.4118** |
| Senza contesto | 13 | 0.0850 | 35 | 0.2288 | 50 | 0.3268 |
| Fusione RRF | 11 | 0.0719 | 38 | 0.2484 | 57 | 0.3725 |
| Fusione Best-Rank | 13 | 0.0850 | **42** | **0.2745** | 58 | 0.3791 |

Il risultato migliore a Recall@10 rimane quello della rappresentazione con contesto della tabella, che recupera 63 delle 153 corrispondenze corrette.

La fusione RRF recupera 57 corrispondenze, mentre la fusione Best-Rank ne recupera 58.

La Best-Rank ottiene però il miglior risultato a Recall@5, recuperando 42 corrispondenze rispetto alle 41 del contesto della tabella.

## 7. Contributo del nome della tabella

Il confronto tra `senza_contesto` e `contesto_tabella` mostra una differenza significativa.

A Recall@10:

- senza contesto: 50/153, pari a 0.3268;
- con contesto della tabella: 63/153, pari a 0.4118.

Anche a Recall@5 il contesto migliora da 35 a 41 corrispondenze recuperate.

Questo suggerisce che il miglioramento osservato non dipenda soltanto dalle etichette testuali `Column:` e `Description:`, ma che il nome della tabella fornisca effettivamente informazione utile al retrieval.

## 8. Confronto tra RRF e Best-Rank

Rispetto a RRF, la Best-Rank:

- guadagna 9 corrispondenze nella top-10;
- ne perde 8;
- produce quindi un saldo netto di +1 corrispondenza.

La differenza principale è nel tipo di candidati favoriti.

RRF tende a premiare l'accordo tra le due graduatorie, mentre Best-Rank tende a conservare candidati molto forti in almeno una delle due rappresentazioni.

## 9. Casi recuperati dalla Best-Rank

Un caso particolarmente significativo è:

`D_ITEMS.LABEL → CONCEPT.CONCEPT_NAME`

I ranghi sono:

- nome + descrizione: 161;
- contesto tabella: 1;
- RRF: 27;
- Best-Rank: 2.

La rappresentazione con contesto individua perfettamente il target, ma RRF lo penalizza fortemente a causa del rango molto basso nell'altra graduatoria. Best-Rank riesce invece a conservare quasi completamente l'informazione del metodo migliore.

Un comportamento simile si osserva in:

`D_LABITEMS.LOINC_CODE → CONCEPT.CONCEPT_CODE`

con:

- nome + descrizione: 3;
- contesto: 67;
- RRF: 12;
- Best-Rank: 5.

Anche in questo caso la Best-Rank mantiene nella top-10 un candidato molto forte secondo una sola rappresentazione.

Altri esempi recuperati efficacemente sono:

`PROCEDUREEVENTS_MV.SUBJECT_ID → PROCEDURE_OCCURRENCE.PERSON_ID`

che passa dal rango 11 di RRF al rango 3 con Best-Rank, e:

`PROCEDUREEVENTS_MV.STARTTIME → PROCEDURE_OCCURRENCE.PROCEDURE_DATETIME`

che passa dal rango 11 di RRF al rango 4 con Best-Rank.

Questi casi confermano l'idea alla base della seconda strategia.

## 10. Casi favoriti da RRF

Esistono però anche situazioni in cui RRF funziona meglio.

Per:

`PRESCRIPTIONS.DRUG → DRUG_EXPOSURE.DRUG_SOURCE_VALUE`

il target corretto si trova al rango 12 in entrambe le rappresentazioni singole.

RRF premia l'accordo tra i due ranking e porta il target al rango 9, mentre Best-Rank lo posiziona al rango 15.

Un altro esempio è:

`DATETIMEEVENTS.VALUE → OBSERVATION.VALUE_AS_DATETIME`

con:

- nome + descrizione: 38;
- contesto: 12;
- RRF: 2;
- Best-Rank: 23.

In questo caso RRF sfrutta meglio l'informazione combinata delle due graduatorie.

## 11. Casi guadagnati e persi

Rispetto a `nome + descrizione`, RRF guadagna 10 corrispondenze e ne perde 3.

Rispetto al `contesto della tabella`, RRF ne guadagna 6 ma ne perde 12.

Best-Rank, rispetto a `nome + descrizione`, guadagna 13 corrispondenze e ne perde 5.

Rispetto al `contesto della tabella`, invece, guadagna 3 corrispondenze ma ne perde 8.

Questo mostra che nessuna delle due fusioni riesce a mantenere contemporaneamente tutti i vantaggi delle due rappresentazioni singole con un budget massimo di dieci candidati.

## 12. Conclusioni

L'esperimento mostra che le due rappresentazioni contengono informazioni complementari, ma combinarle efficacemente con un budget ristretto di dieci candidati non è immediato.

RRF migliora rispetto a `nome + descrizione`, ma non supera la rappresentazione con contesto della tabella.

L'analisi degli errori di RRF ha portato all'introduzione della strategia Best-Rank, pensata per proteggere i candidati molto forti secondo almeno una delle due rappresentazioni.

Questa modifica migliora i risultati rispetto a RRF in tutte e tre le metriche e raggiunge il miglior Recall@5 dell'esperimento, pari a 0.2745.

A Recall@10, tuttavia, il contesto della tabella rimane la configurazione migliore con 0.4118, contro 0.3791 della Best-Rank.

I risultati suggeriscono quindi che, con un budget di dieci candidati, il contesto della tabella rappresenti ancora la scelta più efficace complessivamente, mentre la Best-Rank può essere utile quando l'obiettivo è costruire una shortlist più corta e preservare candidati molto forti individuati da una singola rappresentazione.

Poiché la Best-Rank è stata introdotta dopo aver osservato i risultati di RRF, il suo risultato viene considerato esclusivamente esplorativo e non come una nuova configurazione ottimizzata o validata sul benchmark.