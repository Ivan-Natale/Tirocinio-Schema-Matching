import csv


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


# Calcola la similarità di Jaccard
def jaccard(nome1, nome2):

    # Divide i nomi usando _
    parole1 = set(nome1.lower().split("_"))
    parole2 = set(nome2.lower().split("_"))

    # Parole presenti in entrambi i nomi
    intersezione = parole1 & parole2

    # Tutte le parole diverse presenti nei due nomi
    unione = parole1 | parole2

    if len(unione) == 0:
        return 0

    similarita = len(intersezione) / len(unione)

    return similarita


# Esegue l'esperimento su un dataset
def esegui_dataset(nome_dataset, file_a, file_b, file_ground_truth):

    # Legge i file
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

    # Prova tutte le soglie
    for soglia in SOGLIE:

        predizioni = set()

        print()
        print("========================================")
        print("SOGLIA:", soglia)
        print("========================================")

        # Confronta ogni attributo dello schema A
        # con ogni attributo dello schema B
        for attributo_a in schema_a:

            for attributo_b in schema_b:

                similarita = jaccard(
                    attributo_a,
                    attributo_b
                )

                # Se supera la soglia,
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


print("SCHEMA MATCHING - BASELINE JACCARD")


# Esegue la baseline su tutti i dataset
for dataset in DATASETS:

    esegui_dataset(
        dataset["nome"],
        dataset["schema_a"],
        dataset["schema_b"],
        dataset["ground_truth"]
    )