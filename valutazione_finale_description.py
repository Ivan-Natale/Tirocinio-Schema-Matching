import csv
from functools import lru_cache


# --------------------------------------------------
# PARAMETRI BLOCCATI SU CUSTOMERS
# --------------------------------------------------

PESO_NOME_JACCARD = 0.80
PESO_DESCRIZIONE_JACCARD = 0.20
SOGLIA_JACCARD = 0.30

PESO_NOME_LEVENSHTEIN = 0.80
PESO_DESCRIZIONE_LEVENSHTEIN = 0.20
SOGLIA_LEVENSHTEIN = 0.50


# --------------------------------------------------
# DATASET DI TEST: EMPLOYEES
# --------------------------------------------------

FILE_SCHEMA_A = "employees_schema_a.csv"
FILE_SCHEMA_B = "employees_schema_b.csv"
FILE_GROUND_TRUTH = "employees_ground_truth.csv"


# --------------------------------------------------
# LETTURA FILE
# --------------------------------------------------

def leggi_schema(nome_file):

    attributi = []

    with open(nome_file, "r", encoding="utf-8-sig") as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            attributo = {
                "nome": riga["attribute"].strip(),
                "descrizione": riga["description"].strip()
            }

            attributi.append(attributo)

    return attributi


def leggi_ground_truth(nome_file):

    corrispondenze = set()

    with open(nome_file, "r", encoding="utf-8-sig") as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            coppia = (
                riga["attribute_a"].strip(),
                riga["attribute_b"].strip()
            )

            corrispondenze.add(coppia)

    return corrispondenze


# --------------------------------------------------
# JACCARD
# --------------------------------------------------

def tokenizza(testo):

    testo = testo.lower()
    testo = testo.replace("_", " ")

    return set(testo.split())


def jaccard(testo1, testo2):

    parole1 = tokenizza(testo1)
    parole2 = tokenizza(testo2)

    intersezione = parole1 & parole2
    unione = parole1 | parole2

    if len(unione) == 0:
        return 0

    return len(intersezione) / len(unione)


# --------------------------------------------------
# LEVENSHTEIN
# --------------------------------------------------

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

    return 1 - (
        distanza / lunghezza_massima
    )


# --------------------------------------------------
# METRICHE
# --------------------------------------------------

def calcola_metriche(predizioni, ground_truth):

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

    return tp, fp, fn, precision, recall, f1


# --------------------------------------------------
# VALUTAZIONE
# --------------------------------------------------

def valuta(
    algoritmo,
    schema_a,
    schema_b,
    ground_truth,
    peso_nome,
    peso_descrizione,
    soglia
):

    predizioni = set()

    print()
    print("############################################")
    print("ALGORITMO:", algoritmo)
    print("############################################")

    print("Peso nome:", peso_nome)
    print("Peso descrizione:", peso_descrizione)
    print("Soglia:", soglia)

    print()
    print("COPPIE PREDICTION:")

    for attributo_a in schema_a:

        for attributo_b in schema_b:

            nome_a = attributo_a["nome"]
            nome_b = attributo_b["nome"]

            descrizione_a = attributo_a["descrizione"]
            descrizione_b = attributo_b["descrizione"]

            if algoritmo == "JACCARD":

                score_nome = jaccard(
                    nome_a,
                    nome_b
                )

                score_descrizione = jaccard(
                    descrizione_a,
                    descrizione_b
                )

            else:

                score_nome = similarita_levenshtein(
                    nome_a,
                    nome_b
                )

                score_descrizione = similarita_levenshtein(
                    descrizione_a,
                    descrizione_b
                )

            score_finale = (
                peso_nome * score_nome
                +
                peso_descrizione * score_descrizione
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

    (
        tp,
        fp,
        fn,
        precision,
        recall,
        f1
    ) = calcola_metriche(
        predizioni,
        ground_truth
    )

    print()
    print("RISULTATI FINALI")

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

    return {
        "algoritmo": algoritmo,
        "peso_nome": peso_nome,
        "peso_descrizione": peso_descrizione,
        "soglia": soglia,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4)
    }


# --------------------------------------------------
# CARICAMENTO DEL TEST SET
# --------------------------------------------------

schema_a = leggi_schema(FILE_SCHEMA_A)
schema_b = leggi_schema(FILE_SCHEMA_B)

ground_truth = leggi_ground_truth(
    FILE_GROUND_TRUTH
)


print()
print("VALUTAZIONE FINALE - TEST SET EMPLOYEES")

print("Attributi schema A:", len(schema_a))
print("Attributi schema B:", len(schema_b))
print("Ground truth:", len(ground_truth))


# --------------------------------------------------
# TEST JACCARD
# --------------------------------------------------

risultato_jaccard = valuta(
    "JACCARD",
    schema_a,
    schema_b,
    ground_truth,
    PESO_NOME_JACCARD,
    PESO_DESCRIZIONE_JACCARD,
    SOGLIA_JACCARD
)


# --------------------------------------------------
# TEST LEVENSHTEIN
# --------------------------------------------------

risultato_levenshtein = valuta(
    "LEVENSHTEIN",
    schema_a,
    schema_b,
    ground_truth,
    PESO_NOME_LEVENSHTEIN,
    PESO_DESCRIZIONE_LEVENSHTEIN,
    SOGLIA_LEVENSHTEIN
)


# --------------------------------------------------
# SALVATAGGIO RISULTATI
# --------------------------------------------------

with open(
    "valutazione_finale_description.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "algoritmo",
        "peso_nome",
        "peso_descrizione",
        "soglia",
        "tp",
        "fp",
        "fn",
        "precision",
        "recall",
        "f1_score"
    ]

    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )

    scrittore.writeheader()

    scrittore.writerow(
        risultato_jaccard
    )

    scrittore.writerow(
        risultato_levenshtein
    )


print()
print(
    "Risultati salvati in:",
    "valutazione_finale_description.csv"
)