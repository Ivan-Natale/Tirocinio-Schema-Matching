import csv
from functools import lru_cache


# ==================================================
# DATASET DI TEST
# ==================================================

FILE_SCHEMA_A = "employees_schema_a.csv"
FILE_SCHEMA_B = "employees_schema_b.csv"
FILE_GROUND_TRUTH = "employees_ground_truth.csv"


# ==================================================
# PARAMETRI BLOCCATI SU CUSTOMERS
# ==================================================

PARAMETRI = {
    ("JACCARD", "solo_nome"): {
        "soglia": 0.33
    },

    ("JACCARD", "sola_descrizione"): {
        "soglia": 0.20
    },

    ("JACCARD", "nome_descrizione"): {
        "soglia": 0.30,
        "peso_nome": 0.80,
        "peso_descrizione": 0.20
    },

    ("JACCARD", "nome_filtro_tipo"): {
        "soglia": 0.33
    },

    ("LEVENSHTEIN", "solo_nome"): {
        "soglia": 0.50
    },

    ("LEVENSHTEIN", "sola_descrizione"): {
        "soglia": 0.50
    },

    ("LEVENSHTEIN", "nome_descrizione"): {
        "soglia": 0.50,
        "peso_nome": 0.80,
        "peso_descrizione": 0.20
    },

    ("LEVENSHTEIN", "nome_filtro_tipo"): {
        "soglia": 0.33
    }
}


# ==================================================
# LETTURA FILE
# ==================================================

def leggi_schema(nome_file):

    attributi = []

    with open(
        nome_file,
        "r",
        encoding="utf-8-sig"
    ) as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            attributi.append({
                "nome": riga["attribute"].strip(),
                "tipo": riga["type"].strip(),
                "descrizione": riga["description"].strip()
            })

    return attributi


def leggi_ground_truth(nome_file):

    corrispondenze = set()

    with open(
        nome_file,
        "r",
        encoding="utf-8-sig"
    ) as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            corrispondenze.add(
                (
                    riga["attribute_a"].strip(),
                    riga["attribute_b"].strip()
                )
            )

    return corrispondenze


# ==================================================
# JACCARD
# ==================================================

def tokenizza(testo):

    testo = testo.lower()
    testo = testo.replace("_", " ")

    return set(
        testo.split()
    )


def jaccard(testo1, testo2):

    parole1 = tokenizza(testo1)
    parole2 = tokenizza(testo2)

    intersezione = parole1 & parole2
    unione = parole1 | parole2

    if len(unione) == 0:
        return 0

    return (
        len(intersezione)
        /
        len(unione)
    )


# ==================================================
# LEVENSHTEIN
# ==================================================

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
        distanza
        /
        lunghezza_massima
    )


# ==================================================
# SIMILARITA'
# ==================================================

def calcola_similarita(
    algoritmo,
    testo_a,
    testo_b
):

    if algoritmo == "JACCARD":

        return jaccard(
            testo_a,
            testo_b
        )

    return similarita_levenshtein(
        testo_a,
        testo_b
    )


# ==================================================
# METRICHE
# ==================================================

def calcola_metriche(
    predizioni,
    ground_truth
):

    tp = len(
        predizioni
        &
        ground_truth
    )

    fp = len(
        predizioni
        -
        ground_truth
    )

    fn = len(
        ground_truth
        -
        predizioni
    )

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
            *
            precision
            *
            recall
            /
            (
                precision
                +
                recall
            )
        )

    else:
        f1 = 0

    return (
        tp,
        fp,
        fn,
        precision,
        recall,
        f1
    )


# ==================================================
# VALUTAZIONE
# ==================================================

def valuta(
    algoritmo,
    configurazione,
    schema_a,
    schema_b,
    ground_truth,
    parametri
):

    soglia = parametri["soglia"]

    peso_nome = parametri.get(
        "peso_nome"
    )

    peso_descrizione = parametri.get(
        "peso_descrizione"
    )

    predizioni = set()
    dettagli = []

    coppie_escluse_tipo = 0

    for attributo_a in schema_a:

        for attributo_b in schema_b:

            nome_a = attributo_a["nome"]
            nome_b = attributo_b["nome"]

            descrizione_a = attributo_a[
                "descrizione"
            ]

            descrizione_b = attributo_b[
                "descrizione"
            ]

            tipo_a = attributo_a["tipo"]
            tipo_b = attributo_b["tipo"]


            # ----------------------------------
            # SOLO NOME
            # ----------------------------------

            if configurazione == "solo_nome":

                score = calcola_similarita(
                    algoritmo,
                    nome_a,
                    nome_b
                )


            # ----------------------------------
            # SOLA DESCRIZIONE
            # ----------------------------------

            elif configurazione == "sola_descrizione":

                score = calcola_similarita(
                    algoritmo,
                    descrizione_a,
                    descrizione_b
                )


            # ----------------------------------
            # NOME + DESCRIZIONE
            # ----------------------------------

            elif configurazione == "nome_descrizione":

                score_nome = calcola_similarita(
                    algoritmo,
                    nome_a,
                    nome_b
                )

                score_descrizione = calcola_similarita(
                    algoritmo,
                    descrizione_a,
                    descrizione_b
                )

                score = (
                    peso_nome
                    *
                    score_nome
                    +
                    peso_descrizione
                    *
                    score_descrizione
                )


            # ----------------------------------
            # NOME + FILTRO TIPO
            # ----------------------------------

            elif configurazione == "nome_filtro_tipo":

                if tipo_a != tipo_b:

                    coppie_escluse_tipo += 1

                    continue

                score = calcola_similarita(
                    algoritmo,
                    nome_a,
                    nome_b
                )


            else:

                raise ValueError(
                    "Configurazione non valida"
                )


            if score >= soglia:

                coppia = (
                    nome_a,
                    nome_b
                )

                predizioni.add(
                    coppia
                )

                if coppia in ground_truth:
                    esito = "TP"
                else:
                    esito = "FP"

                dettagli.append({
                    "algoritmo": algoritmo,
                    "configurazione": configurazione,
                    "attributo_a": nome_a,
                    "attributo_b": nome_b,
                    "score": round(score, 4),
                    "soglia": soglia,
                    "esito": esito
                })


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
    print(
        "=============================================="
    )

    print(
        algoritmo,
        "-",
        configurazione
    )

    print(
        "=============================================="
    )

    print(
        "Soglia:",
        soglia
    )

    if configurazione == "nome_descrizione":

        print(
            "Peso nome:",
            peso_nome
        )

        print(
            "Peso descrizione:",
            peso_descrizione
        )

    if configurazione == "nome_filtro_tipo":

        print(
            "Coppie escluse per tipo:",
            coppie_escluse_tipo
        )


    print()
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
        "F1:",
        round(f1, 4)
    )


    print()
    print("MATCH CORRETTI:")

    for coppia in sorted(
        predizioni
        &
        ground_truth
    ):

        print(
            coppia[0],
            "<->",
            coppia[1]
        )


    print()
    print("FALSI POSITIVI:")

    for coppia in sorted(
        predizioni
        -
        ground_truth
    ):

        print(
            coppia[0],
            "<->",
            coppia[1]
        )


    print()
    print("FALSI NEGATIVI:")

    for coppia in sorted(
        ground_truth
        -
        predizioni
    ):

        print(
            coppia[0],
            "<->",
            coppia[1]
        )


    risultato = {
        "algoritmo": algoritmo,
        "configurazione": configurazione,
        "peso_nome":
            peso_nome
            if peso_nome is not None
            else "",
        "peso_descrizione":
            peso_descrizione
            if peso_descrizione is not None
            else "",
        "soglia": soglia,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(
            precision,
            4
        ),
        "recall": round(
            recall,
            4
        ),
        "f1_score": round(
            f1,
            4
        ),
        "coppie_escluse_tipo":
            coppie_escluse_tipo
    }

    return risultato, dettagli


# ==================================================
# CARICAMENTO EMPLOYEES
# ==================================================

schema_a = leggi_schema(
    FILE_SCHEMA_A
)

schema_b = leggi_schema(
    FILE_SCHEMA_B
)

ground_truth = leggi_ground_truth(
    FILE_GROUND_TRUTH
)


print()
print(
    "VALUTAZIONE FINALE LESSICALE"
)

print(
    "TEST SET: EMPLOYEES"
)

print()

print(
    "Attributi schema A:",
    len(schema_a)
)

print(
    "Attributi schema B:",
    len(schema_b)
)

print(
    "Ground truth:",
    len(ground_truth)
)


# ==================================================
# TEST DELLE 8 CONFIGURAZIONI
# ==================================================

risultati_finali = []
dettagli_finali = []


for algoritmo in [
    "JACCARD",
    "LEVENSHTEIN"
]:

    for configurazione in [
        "solo_nome",
        "sola_descrizione",
        "nome_descrizione",
        "nome_filtro_tipo"
    ]:

        parametri = PARAMETRI[
            (
                algoritmo,
                configurazione
            )
        ]

        risultato, dettagli = valuta(
            algoritmo,
            configurazione,
            schema_a,
            schema_b,
            ground_truth,
            parametri
        )

        risultati_finali.append(
            risultato
        )

        dettagli_finali.extend(
            dettagli
        )


# ==================================================
# SALVATAGGIO TABELLA RIASSUNTIVA
# ==================================================

with open(
    "valutazione_finale_lessicale.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "algoritmo",
        "configurazione",
        "peso_nome",
        "peso_descrizione",
        "soglia",
        "tp",
        "fp",
        "fn",
        "precision",
        "recall",
        "f1_score",
        "coppie_escluse_tipo"
    ]

    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )

    scrittore.writeheader()

    for risultato in risultati_finali:

        scrittore.writerow(
            risultato
        )


# ==================================================
# SALVATAGGIO DETTAGLI PREDIZIONI
# ==================================================

with open(
    "dettagli_valutazione_lessicale.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "algoritmo",
        "configurazione",
        "attributo_a",
        "attributo_b",
        "score",
        "soglia",
        "esito"
    ]

    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )

    scrittore.writeheader()

    for dettaglio in dettagli_finali:

        scrittore.writerow(
            dettaglio
        )


print()
print(
    "Risultati salvati in:",
    "valutazione_finale_lessicale.csv"
)

print(
    "Dettagli salvati in:",
    "dettagli_valutazione_lessicale.csv"
)