import csv
from functools import lru_cache


# Soglie da testare
SOGLIE = [0.20, 0.30, 0.33, 0.50, 0.70]


# Dataset da analizzare
DATASETS = [
    {
        "nome": "CUSTOMERS",
        "schema_a": "schema_a.csv",
        "schema_b": "schema_b.csv",
        "ground_truth": "ground_truth.csv"
    },
    {
        "nome": "EMPLOYEES",
        "schema_a": "employees_schema_a.csv",
        "schema_b": "employees_schema_b.csv",
        "ground_truth": "employees_ground_truth.csv"
    }
]


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
# usando la ricorsione
@lru_cache(maxsize=None)
def distanza_levenshtein(a, b):

    # Se la prima stringa è vuota
    if len(a) == 0:
        return len(b)

    # Se la seconda stringa è vuota
    if len(b) == 0:
        return len(a)

    # Se il primo carattere è uguale
    if a[0] == b[0]:

        return distanza_levenshtein(
            a[1:],
            b[1:]
        )

    # Proviamo le tre operazioni

    cancellazione = distanza_levenshtein(
        a[1:],
        b
    )

    inserimento = distanza_levenshtein(
        a,
        b[1:]
    )

    sostituzione = distanza_levenshtein(
        a[1:],
        b[1:]
    )

    # Scegliamo l'operazione meno costosa
    return 1 + min(
        cancellazione,
        inserimento,
        sostituzione
    )


# Trasforma la distanza in similarità tra 0 e 1
def similarita_levenshtein(a, b):

    a = a.lower()
    b = b.lower()

    distanza = distanza_levenshtein(a, b)

    lunghezza_massima = max(
        len(a),
        len(b)
    )

    if lunghezza_massima == 0:
        return 1.0

    similarita = 1 - (
        distanza / lunghezza_massima
    )

    return similarita


# Esegue Levenshtein su un dataset
def esegui_dataset(
    nome_dataset,
    file_a,
    file_b,
    file_ground_truth
):

    # Legge i file
    schema_a = leggi_schema(file_a)
    schema_b = leggi_schema(file_b)
    ground_truth = leggi_ground_truth(
        file_ground_truth
    )

    print()
    print("##################################################")
    print("DATASET:", nome_dataset)
    print("##################################################")

    print("Attributi schema A:", len(schema_a))
    print("Attributi schema B:", len(schema_b))
    print(
        "Corrispondenze nella ground truth:",
        len(ground_truth)
    )


    # Prova tutte le soglie
    for soglia in SOGLIE:

        predizioni = set()

        print()
        print("========================================")
        print("SOGLIA:", soglia)
        print("========================================")


        # Confronta tutti gli attributi
        for attributo_a in schema_a:

            for attributo_b in schema_b:

                similarita = similarita_levenshtein(
                    attributo_a,
                    attributo_b
                )


                # Se supera la soglia
                # viene considerato un match
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


        # True Positive
        tp = len(
            predizioni & ground_truth
        )


        # False Positive
        fp = len(
            predizioni - ground_truth
        )


        # False Negative
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


        # Stampa risultati
        print()
        print(
            "RISULTATI",
            nome_dataset,
            "- SOGLIA",
            soglia
        )

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


        # False Negative
        print()
        print("CORRISPONDENZE NON INDIVIDUATE:")

        for coppia in ground_truth - predizioni:

            print(
                coppia[0],
                "<->",
                coppia[1]
            )


        # False Positive
        print()
        print("CORRISPONDENZE ERRATE:")

        for coppia in predizioni - ground_truth:

            print(
                coppia[0],
                "<->",
                coppia[1]
            )


print("SCHEMA MATCHING - BASELINE LEVENSHTEIN")


# Esegue Levenshtein su entrambi i dataset
for dataset in DATASETS:

    esegui_dataset(
        dataset["nome"],
        dataset["schema_a"],
        dataset["schema_b"],
        dataset["ground_truth"]
    )