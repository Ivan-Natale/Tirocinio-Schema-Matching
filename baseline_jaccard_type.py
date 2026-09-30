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


# Legge nome e tipo degli attributi
def leggi_schema(nome_file):

    attributi = []

    with open(nome_file, "r", encoding="utf-8-sig") as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            attributo = {
                "nome": riga["attribute"],
                "tipo": riga["type"]
            }

            attributi.append(attributo)

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


# Calcola la similarità di Jaccard sui nomi
def jaccard(nome1, nome2):

    parole1 = set(nome1.lower().split("_"))
    parole2 = set(nome2.lower().split("_"))

    intersezione = parole1 & parole2
    unione = parole1 | parole2

    if len(unione) == 0:
        return 0

    similarita = len(intersezione) / len(unione)

    return similarita


# Esegue l'esperimento su un dataset
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


    # Prova tutte le soglie
    for soglia in SOGLIE:

        predizioni = set()
        coppie_escluse_tipo = 0

        print()
        print("========================================")
        print("SOGLIA:", soglia)
        print("========================================")


        # Confronta tutti gli attributi
        for attributo_a in schema_a:

            for attributo_b in schema_b:

                nome_a = attributo_a["nome"]
                nome_b = attributo_b["nome"]

                tipo_a = attributo_a["tipo"]
                tipo_b = attributo_b["tipo"]


                # FILTRO SUL TIPO
                # Se i tipi sono diversi,
                # la coppia viene esclusa
                if tipo_a != tipo_b:

                    coppie_escluse_tipo += 1
                    continue


                # Se i tipi sono uguali,
                # confrontiamo i nomi con Jaccard
                similarita = jaccard(
                    nome_a,
                    nome_b
                )


                if similarita >= soglia:

                    coppia = (
                        nome_a,
                        nome_b
                    )

                    predizioni.add(coppia)

                    print(
                        nome_a,
                        "<->",
                        nome_b,
                        "tipo:",
                        tipo_a,
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


        print()
        print(
            "RISULTATI",
            nome_dataset,
            "- SOGLIA",
            soglia
        )

        print(
            "Coppie escluse per tipo:",
            coppie_escluse_tipo
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


print("SCHEMA MATCHING - JACCARD + FILTRO TIPO")


# Esegue la baseline sui due dataset
for dataset in DATASETS:

    esegui_dataset(
        dataset["nome"],
        dataset["schema_a"],
        dataset["schema_b"],
        dataset["ground_truth"]
    )