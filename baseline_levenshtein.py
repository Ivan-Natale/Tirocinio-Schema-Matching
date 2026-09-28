import csv
from functools import lru_cache


# Soglie da testare
SOGLIE = [0.20, 0.30, 0.33, 0.50, 0.70]


# Legge gli attributi di uno schema
def leggi_schema(nome_file):
    attributi = []

    with open(nome_file, "r", encoding="utf-8-sig") as file:
        lettore = csv.DictReader(file)

        for riga in lettore:
            attributi.append(riga["attribute"])

    return attributi


# Legge la ground truth
def leggi_ground_truth(nome_file):
    corrispondenze = set()

    with open(nome_file, "r", encoding="utf-8-sig") as file:
        lettore = csv.DictReader(file)

        for riga in lettore:
            coppia = (
                riga["attribute_a"],
                riga["attribute_b"]
            )

            corrispondenze.add(coppia)

    return corrispondenze


# Calcola la distanza di Levenshtein
# usando una versione ricorsiva senza matrice
@lru_cache(maxsize=None)
def distanza_levenshtein(a, b):

    # Se la prima stringa è vuota,
    # bisogna inserire tutti i caratteri della seconda
    if len(a) == 0:
        return len(b)

    # Se la seconda stringa è vuota,
    # bisogna cancellare tutti i caratteri della prima
    if len(b) == 0:
        return len(a)

    # Se il primo carattere è uguale,
    # non serve fare nessuna modifica
    if a[0] == b[0]:
        return distanza_levenshtein(
            a[1:],
            b[1:]
        )

    # Proviamo le tre possibili operazioni

    # 1. Cancellazione di un carattere dalla prima stringa
    cancellazione = distanza_levenshtein(
        a[1:],
        b
    )

    # 2. Inserimento di un carattere
    inserimento = distanza_levenshtein(
        a,
        b[1:]
    )

    # 3. Sostituzione di un carattere
    sostituzione = distanza_levenshtein(
        a[1:],
        b[1:]
    )

    # Scegliamo l'operazione che richiede meno modifiche
    return 1 + min(
        cancellazione,
        inserimento,
        sostituzione
    )


# Trasforma la distanza di Levenshtein
# in una similarità compresa tra 0 e 1
def similarita_levenshtein(a, b):

    # Convertiamo tutto in minuscolo
    a = a.lower()
    b = b.lower()

    # Calcoliamo la distanza
    distanza = distanza_levenshtein(a, b)

    # Prendiamo la lunghezza della stringa più lunga
    lunghezza_massima = max(
        len(a),
        len(b)
    )

    # Caso speciale: due stringhe vuote
    if lunghezza_massima == 0:
        return 1.0

    # Conversione distanza -> similarità
    similarita = 1 - (
        distanza / lunghezza_massima
    )

    return similarita


# Legge i file CSV
schema_a = leggi_schema("schema_a.csv")
schema_b = leggi_schema("schema_b.csv")
ground_truth = leggi_ground_truth("ground_truth.csv")


print("SCHEMA MATCHING - BASELINE LEVENSHTEIN")
print()

print("Attributi schema A:", len(schema_a))
print("Attributi schema B:", len(schema_b))
print(
    "Corrispondenze nella ground truth:",
    len(ground_truth)
)


# Prova tutte le soglie
for soglia in SOGLIE:

    # Per ogni soglia partiamo da un insieme vuoto
    predizioni = set()

    print()
    print("========================================")
    print("SOGLIA:", soglia)
    print("========================================")

    # Confronta ogni attributo dello schema A
    # con ogni attributo dello schema B
    for attributo_a in schema_a:

        for attributo_b in schema_b:

            similarita = similarita_levenshtein(
                attributo_a,
                attributo_b
            )

            # Se la similarità supera la soglia,
            # la coppia viene considerata una corrispondenza
            if similarita >= soglia:

                coppia = (
                    attributo_a,
                    attributo_b
                )

                predizioni.add(coppia)

                print(
                    attributo_a,
                    "<->",
                    attributo_b,
                    "similarità:",
                    round(similarita, 4)
                )


    # Calcolo dei True Positive
    tp = len(
        predizioni & ground_truth
    )

    # Calcolo dei False Positive
    fp = len(
        predizioni - ground_truth
    )

    # Calcolo dei False Negative
    fn = len(
        ground_truth - predizioni
    )


    # Precision
    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0


    # Recall
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0


    # F1-score
    if precision + recall > 0:

        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
        )

    else:
        f1 = 0


    # Stampa dei risultati
    print()
    print("RISULTATI SOGLIA", soglia)

    print("TP:", tp)
    print("FP:", fp)
    print("FN:", fn)

    print(
        "Precision:",
        round(precision, 4)
    )

    print(
        "Recall:",
        round(recall, 4)
    )

    print(
        "F1-score:",
        round(f1, 4)
    )


    # Corrispondenze corrette
    # che il programma non ha trovato
    print()
    print("CORRISPONDENZE NON INDIVIDUATE:")

    for coppia in ground_truth - predizioni:

        print(
            coppia[0],
            "<->",
            coppia[1]
        )


    # Corrispondenze proposte dal programma
    # ma non presenti nella ground truth
    print()
    print("CORRISPONDENZE ERRATE:")

    for coppia in predizioni - ground_truth:

        print(
            coppia[0],
            "<->",
            coppia[1]
        )