import csv
from functools import lru_cache


# Soglie da testare
SOGLIE = [0.20, 0.30, 0.33, 0.50, 0.70]


# Pesi scelti prima dell'esperimento
PESO_NOME = 0.70
PESO_DESCRIZIONE = 0.30


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


# Legge nome e descrizione
def leggi_schema(nome_file):

    attributi = []

    with open(nome_file, "r", encoding="utf-8-sig") as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            attributo = {
                "nome": riga["attribute"],
                "descrizione": riga["description"]
            }

            attributi.append(attributo)

    return attributi


# Legge ground truth
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


# Distanza di Levenshtein
@lru_cache(maxsize=None)
def distanza_levenshtein(a, b):

    if len(a) == 0:
        return len(b)

    if len(b) == 0:
        return len(a)

    if a[0] == b[0]:

        return distanza_levenshtein(
            a[1:],
            b[1:]
        )


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


    return 1 + min(
        cancellazione,
        inserimento,
        sostituzione
    )


# Converte la distanza in similarità
def similarita_levenshtein(a, b):

    a = a.lower()
    b = b.lower()

    distanza = distanza_levenshtein(
        a,
        b
    )

    lunghezza_massima = max(
        len(a),
        len(b)
    )

    if lunghezza_massima == 0:
        return 1.0

    return 1 - (
        distanza / lunghezza_massima
    )


# Esegue esperimento
def esegui_dataset(
    nome_dataset,
    file_a,
    file_b,
    file_ground_truth
):

    schema_a = leggi_schema(file_a)
    schema_b = leggi_schema(file_b)
    ground_truth = leggi_ground_truth(file_ground_truth)

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


    for soglia in SOGLIE:

        predizioni = set()

        print()
        print("========================================")
        print("SOGLIA:", soglia)
        print("========================================")


        for attributo_a in schema_a:

            for attributo_b in schema_b:

                nome_a = attributo_a["nome"]
                nome_b = attributo_b["nome"]

                descrizione_a = attributo_a["descrizione"]
                descrizione_b = attributo_b["descrizione"]


                # Similarità del nome
                score_nome = similarita_levenshtein(
                    nome_a,
                    nome_b
                )


                # Similarità della descrizione
                score_descrizione = similarita_levenshtein(
                    descrizione_a,
                    descrizione_b
                )


                # Combinazione dei punteggi
                score_finale = (
                    PESO_NOME * score_nome
                    +
                    PESO_DESCRIZIONE * score_descrizione
                )


                if score_finale >= soglia:

                    coppia = (
                        nome_a,
                        nome_b
                    )

                    predizioni.add(coppia)

                    print(
                        nome_a,
                        "<->",
                        nome_b,
                        "| nome:",
                        round(score_nome, 4),
                        "| descrizione:",
                        round(score_descrizione, 4),
                        "| finale:",
                        round(score_finale, 4)
                    )


        # Metriche
        tp = len(predizioni & ground_truth)
        fp = len(predizioni - ground_truth)
        fn = len(ground_truth - predizioni)


        if tp + fp > 0:
            precision = tp / (tp + fp)
        else:
            precision = 0


        if tp + fn > 0:
            recall = tp / (tp + fn)
        else:
            recall = 0


        if precision + recall > 0:

            f1 = (
                2
                * precision
                * recall
                / (precision + recall)
            )

        else:
            f1 = 0


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


        print()
        print("CORRISPONDENZE NON INDIVIDUATE:")

        for coppia in ground_truth - predizioni:

            print(
                coppia[0],
                "<->",
                coppia[1]
            )


        print()
        print("CORRISPONDENZE ERRATE:")

        for coppia in predizioni - ground_truth:

            print(
                coppia[0],
                "<->",
                coppia[1]
            )


print("SCHEMA MATCHING - LEVENSHTEIN NOME + DESCRIZIONE")


for dataset in DATASETS:

    esegui_dataset(
        dataset["nome"],
        dataset["schema_a"],
        dataset["schema_b"],
        dataset["ground_truth"]
    )