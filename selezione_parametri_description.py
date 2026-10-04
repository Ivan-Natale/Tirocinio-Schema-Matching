import csv
from functools import lru_cache


# --------------------------------------------------
# CONFIGURAZIONI DA PROVARE SUL DATASET DI SVILUPPO
# --------------------------------------------------

PESI = [
    (0.80, 0.20),
    (0.70, 0.30),
    (0.60, 0.40)
]

SOGLIE = [0.20, 0.30, 0.33, 0.50, 0.70]


# Usiamo SOLO CUSTOMERS per scegliere i parametri
FILE_SCHEMA_A = "schema_a.csv"
FILE_SCHEMA_B = "schema_b.csv"
FILE_GROUND_TRUTH = "ground_truth.csv"


# --------------------------------------------------
# LETTURA DEI FILE
# --------------------------------------------------

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
# CALCOLO METRICHE
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
# VALUTAZIONE DI UNA CONFIGURAZIONE
# --------------------------------------------------

def valuta_configurazione(
    schema_a,
    schema_b,
    ground_truth,
    algoritmo,
    peso_nome,
    peso_descrizione,
    soglia
):

    predizioni = set()

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

                predizioni.add(
                    (
                        nome_a,
                        nome_b
                    )
                )

    return calcola_metriche(
        predizioni,
        ground_truth
    )


# --------------------------------------------------
# CARICAMENTO CUSTOMERS
# --------------------------------------------------

schema_a = leggi_schema(FILE_SCHEMA_A)
schema_b = leggi_schema(FILE_SCHEMA_B)

ground_truth = leggi_ground_truth(
    FILE_GROUND_TRUTH
)

print()
print("GROUND TRUTH LETTA:")
for coppia in ground_truth:
    print(coppia)

print()
print(
    "TEST customer_id-client_code:",
    ("customer_id", "client_code") in ground_truth
)

print(
    "TEST first_name-given_name:",
    ("first_name", "given_name") in ground_truth
)

print(
    "TEST birth_date-date_of_birth:",
    ("birth_date", "date_of_birth") in ground_truth
)


print()
print("SELEZIONE PARAMETRI - DATASET DI SVILUPPO CUSTOMERS")
print()

print("Attributi schema A:", len(schema_a))
print("Attributi schema B:", len(schema_b))
print("Ground truth:", len(ground_truth))


# Qui salviamo tutti i risultati
risultati = []


# --------------------------------------------------
# PROVA DELLE CONFIGURAZIONI
# --------------------------------------------------

for algoritmo in ["JACCARD", "LEVENSHTEIN"]:

    print()
    print("##################################################")
    print("ALGORITMO:", algoritmo)
    print("##################################################")

    for peso_nome, peso_descrizione in PESI:

        for soglia in SOGLIE:

            (
                tp,
                fp,
                fn,
                precision,
                recall,
                f1
            ) = valuta_configurazione(
                schema_a,
                schema_b,
                ground_truth,
                algoritmo,
                peso_nome,
                peso_descrizione,
                soglia
            )

            risultato = {
                "algoritmo": algoritmo,
                "peso_nome": peso_nome,
                "peso_descrizione": peso_descrizione,
                "soglia": soglia,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            }

            risultati.append(risultato)

            print(
                "Nome:",
                peso_nome,
                "| Descrizione:",
                peso_descrizione,
                "| Soglia:",
                soglia,
                "| TP:",
                tp,
                "| FP:",
                fp,
                "| FN:",
                fn,
                "| Precision:",
                round(precision, 4),
                "| Recall:",
                round(recall, 4),
                "| F1:",
                round(f1, 4)
            )


# --------------------------------------------------
# SALVATAGGIO DEI RISULTATI
# --------------------------------------------------

with open(
    "selezione_parametri_description.csv",
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

    for risultato in risultati:

        riga = risultato.copy()

        riga["precision"] = round(
            riga["precision"],
            4
        )

        riga["recall"] = round(
            riga["recall"],
            4
        )

        riga["f1_score"] = round(
            riga["f1_score"],
            4
        )

        scrittore.writerow(riga)


print()
print(
    "Risultati salvati in:",
    "selezione_parametri_description.csv"
)