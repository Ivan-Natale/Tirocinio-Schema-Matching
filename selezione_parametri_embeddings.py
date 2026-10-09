import csv

from sentence_transformers import (
    SentenceTransformer,
    util
)


# ==================================================
# DATASET DI SVILUPPO
# ==================================================

FILE_SCHEMA_A = "schema_a.csv"
FILE_SCHEMA_B = "schema_b.csv"
FILE_GROUND_TRUTH = "ground_truth.csv"


# ==================================================
# MODELLO
# ==================================================

NOME_MODELLO = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ==================================================
# SOGLIE DA TESTARE
# ==================================================

SOGLIE = [
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
    0.85,
    0.90
]


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
                "nome":
                    riga["attribute"].strip(),

                "descrizione":
                    riga["description"].strip()
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
# PREPARAZIONE DEL TESTO
# ==================================================

def normalizza_nome(nome):

    nome = nome.replace(
        "_",
        " "
    )

    return nome


def crea_testo(
    attributo,
    configurazione
):

    nome = normalizza_nome(
        attributo["nome"]
    )

    descrizione = attributo[
        "descrizione"
    ]


    if configurazione == "solo_nome":

        return nome


    elif configurazione == "sola_descrizione":

        return descrizione


    elif configurazione == "nome_descrizione":

        return (
            nome
            + ". "
            + descrizione
        )


    else:

        raise ValueError(
            "Configurazione non valida"
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

        precision = (
            tp
            /
            (tp + fp)
        )

    else:
        precision = 0


    if tp + fn > 0:

        recall = (
            tp
            /
            (tp + fn)
        )

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
# CALCOLO SCORE
# ==================================================

def calcola_score(
    modello,
    schema_a,
    schema_b,
    configurazione
):

    testi_a = []

    testi_b = []


    for attributo in schema_a:

        testi_a.append(
            crea_testo(
                attributo,
                configurazione
            )
        )


    for attributo in schema_b:

        testi_b.append(
            crea_testo(
                attributo,
                configurazione
            )
        )


    # Tutti gli embeddings dello schema A
    embeddings_a = modello.encode(
        testi_a,
        convert_to_tensor=True
    )


    # Tutti gli embeddings dello schema B
    embeddings_b = modello.encode(
        testi_b,
        convert_to_tensor=True
    )


    # Matrice di similarità
    matrice_similarita = util.cos_sim(
        embeddings_a,
        embeddings_b
    )


    score_coppie = []


    for indice_a, attributo_a in enumerate(
        schema_a
    ):

        for indice_b, attributo_b in enumerate(
            schema_b
        ):

            score = (
                matrice_similarita[
                    indice_a
                ][
                    indice_b
                ]
                .item()
            )


            score_coppie.append({
                "attributo_a":
                    attributo_a["nome"],

                "attributo_b":
                    attributo_b["nome"],

                "score":
                    score
            })


    return score_coppie


# ==================================================
# VALUTAZIONE DI UNA SOGLIA
# ==================================================

def valuta_soglia(
    score_coppie,
    ground_truth,
    soglia
):

    predizioni = set()


    for elemento in score_coppie:

        if elemento["score"] >= soglia:

            predizioni.add(
                (
                    elemento["attributo_a"],
                    elemento["attributo_b"]
                )
            )


    return calcola_metriche(
        predizioni,
        ground_truth
    )


# ==================================================
# SCELTA DELLA SOGLIA
# ==================================================

def scegli_migliore(risultati):

    risultati_ordinati = sorted(
        risultati,
        key=lambda x: (
            x["f1_score"],
            x["precision"],
            x["soglia"]
        ),
        reverse=True
    )

    return risultati_ordinati[0]


# ==================================================
# CARICAMENTO DATI
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
    "SELEZIONE PARAMETRI EMBEDDINGS"
)

print(
    "DATASET DI SVILUPPO: CUSTOMERS"
)

print()

print(
    "Modello:",
    NOME_MODELLO
)

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
# CARICAMENTO MODELLO
# ==================================================

print()
print("Caricamento modello...")

modello = SentenceTransformer(
    NOME_MODELLO
)

print("Modello caricato.")


# ==================================================
# ESPERIMENTI
# ==================================================

configurazioni = [
    "solo_nome",
    "sola_descrizione",
    "nome_descrizione"
]


tutti_risultati = []
parametri_selezionati = []
tutti_score = []


for configurazione in configurazioni:

    print()
    print(
        "=============================================="
    )

    print(
        "CONFIGURAZIONE:",
        configurazione
    )

    print(
        "=============================================="
    )


    # Gli embeddings vengono calcolati una sola volta
    # per questa configurazione.

    score_coppie = calcola_score(
        modello,
        schema_a,
        schema_b,
        configurazione
    )


    # Salviamo anche gli score
    # di tutte le coppie.

    for elemento in score_coppie:

        tutti_score.append({
            "configurazione":
                configurazione,

            "attributo_a":
                elemento["attributo_a"],

            "attributo_b":
                elemento["attributo_b"],

            "score":
                round(
                    elemento["score"],
                    4
                ),

            "ground_truth":
                1
                if (
                    elemento["attributo_a"],
                    elemento["attributo_b"]
                )
                in ground_truth
                else 0
        })


    risultati_configurazione = []


    for soglia in SOGLIE:

        (
            tp,
            fp,
            fn,
            precision,
            recall,
            f1
        ) = valuta_soglia(
            score_coppie,
            ground_truth,
            soglia
        )


        risultato = {
            "configurazione":
                configurazione,

            "soglia":
                soglia,

            "tp":
                tp,

            "fp":
                fp,

            "fn":
                fn,

            "precision":
                round(
                    precision,
                    4
                ),

            "recall":
                round(
                    recall,
                    4
                ),

            "f1_score":
                round(
                    f1,
                    4
                )
        }


        tutti_risultati.append(
            risultato
        )

        risultati_configurazione.append(
            risultato
        )


        print(
            "Soglia:",
            soglia,
            "| TP:",
            tp,
            "| FP:",
            fp,
            "| FN:",
            fn,
            "| Precision:",
            round(
                precision,
                4
            ),
            "| Recall:",
            round(
                recall,
                4
            ),
            "| F1:",
            round(
                f1,
                4
            )
        )


    migliore = scegli_migliore(
        risultati_configurazione
    )


    parametri_selezionati.append(
        migliore
    )


# ==================================================
# RISULTATI SELEZIONATI
# ==================================================

print()
print()
print(
    "=============================================="
)

print(
    "SOGLIE SELEZIONATE SU CUSTOMERS"
)

print(
    "=============================================="
)


for risultato in parametri_selezionati:

    print()

    print(
        "Configurazione:",
        risultato["configurazione"]
    )

    print(
        "Soglia:",
        risultato["soglia"]
    )

    print(
        "Precision:",
        risultato["precision"]
    )

    print(
        "Recall:",
        risultato["recall"]
    )

    print(
        "F1:",
        risultato["f1_score"]
    )


# ==================================================
# CSV 1 - TUTTE LE SOGLIE
# ==================================================

with open(
    "selezione_parametri_embeddings.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "configurazione",
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

    for risultato in tutti_risultati:

        scrittore.writerow(
            risultato
        )


# ==================================================
# CSV 2 - SOGLIE SCELTE
# ==================================================

with open(
    "parametri_embeddings_selezionati.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "configurazione",
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

    for risultato in parametri_selezionati:

        scrittore.writerow(
            risultato
        )


# ==================================================
# CSV 3 - SCORE DI TUTTE LE COPPIE
# ==================================================

with open(
    "score_embeddings_customers.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "configurazione",
        "attributo_a",
        "attributo_b",
        "score",
        "ground_truth"
    ]

    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )

    scrittore.writeheader()

    for elemento in tutti_score:

        scrittore.writerow(
            elemento
        )


print()
print(
    "Risultati salvati in:",
    "selezione_parametri_embeddings.csv"
)

print(
    "Parametri scelti salvati in:",
    "parametri_embeddings_selezionati.csv"
)

print(
    "Score delle coppie salvati in:",
    "score_embeddings_customers.csv"
)