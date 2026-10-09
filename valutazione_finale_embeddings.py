import csv

from sentence_transformers import (
    SentenceTransformer,
    util
)


# ==================================================
# DATASET DI TEST
# ==================================================

FILE_SCHEMA_A = "employees_schema_a.csv"
FILE_SCHEMA_B = "employees_schema_b.csv"
FILE_GROUND_TRUTH = "employees_ground_truth.csv"


# ==================================================
# MODELLO
# ==================================================

NOME_MODELLO = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ==================================================
# SOGLIE BLOCCATE SU CUSTOMERS
# ==================================================

SOGLIE = {
    "solo_nome": 0.80,
    "sola_descrizione": 0.65,
    "nome_descrizione": 0.75
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
# PREPARAZIONE TESTO
# ==================================================

def normalizza_nome(nome):

    return nome.replace(
        "_",
        " "
    )


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

    testi_a = [
        crea_testo(
            attributo,
            configurazione
        )
        for attributo in schema_a
    ]

    testi_b = [
        crea_testo(
            attributo,
            configurazione
        )
        for attributo in schema_b
    ]


    embeddings_a = modello.encode(
        testi_a,
        convert_to_tensor=True
    )

    embeddings_b = modello.encode(
        testi_b,
        convert_to_tensor=True
    )


    matrice = util.cos_sim(
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
                matrice[
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
# VALUTAZIONE
# ==================================================

def valuta(
    configurazione,
    score_coppie,
    ground_truth,
    soglia
):

    predizioni = set()

    dettagli = []


    for elemento in score_coppie:

        coppia = (
            elemento["attributo_a"],
            elemento["attributo_b"]
        )

        score = elemento["score"]


        if score >= soglia:

            predizioni.add(
                coppia
            )

            if coppia in ground_truth:
                esito = "TP"
            else:
                esito = "FP"

            dettagli.append({
                "configurazione":
                    configurazione,

                "attributo_a":
                    coppia[0],

                "attributo_b":
                    coppia[1],

                "score":
                    round(
                        score,
                        4
                    ),

                "soglia":
                    soglia,

                "esito":
                    esito
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
        "CONFIGURAZIONE:",
        configurazione
    )

    print(
        "=============================================="
    )

    print(
        "Soglia bloccata:",
        soglia
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

        score = next(
            elemento["score"]
            for elemento in score_coppie
            if (
                elemento["attributo_a"],
                elemento["attributo_b"]
            )
            == coppia
        )

        print(
            coppia[0],
            "<->",
            coppia[1],
            "| score:",
            round(score, 4)
        )


    print()
    print("FALSI POSITIVI:")

    for coppia in sorted(
        predizioni
        -
        ground_truth
    ):

        score = next(
            elemento["score"]
            for elemento in score_coppie
            if (
                elemento["attributo_a"],
                elemento["attributo_b"]
            )
            == coppia
        )

        print(
            coppia[0],
            "<->",
            coppia[1],
            "| score:",
            round(score, 4)
        )


    print()
    print("FALSI NEGATIVI:")

    for coppia in sorted(
        ground_truth
        -
        predizioni
    ):

        score = next(
            elemento["score"]
            for elemento in score_coppie
            if (
                elemento["attributo_a"],
                elemento["attributo_b"]
            )
            == coppia
        )

        print(
            coppia[0],
            "<->",
            coppia[1],
            "| score:",
            round(score, 4)
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


    return (
        risultato,
        dettagli
    )


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
    "VALUTAZIONE FINALE EMBEDDINGS"
)

print(
    "TEST SET: EMPLOYEES"
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
# MODELLO
# ==================================================

print()
print("Caricamento modello...")

modello = SentenceTransformer(
    NOME_MODELLO
)

print("Modello caricato.")


# ==================================================
# TEST FINALE
# ==================================================

configurazioni = [
    "solo_nome",
    "sola_descrizione",
    "nome_descrizione"
]


risultati_finali = []
dettagli_finali = []


for configurazione in configurazioni:

    score_coppie = calcola_score(
        modello,
        schema_a,
        schema_b,
        configurazione
    )


    risultato, dettagli = valuta(
        configurazione,
        score_coppie,
        ground_truth,
        SOGLIE[configurazione]
    )


    risultati_finali.append(
        risultato
    )

    dettagli_finali.extend(
        dettagli
    )


# ==================================================
# CSV RISULTATI
# ==================================================

with open(
    "valutazione_finale_embeddings.csv",
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

    for risultato in risultati_finali:

        scrittore.writerow(
            risultato
        )


# ==================================================
# CSV DETTAGLI
# ==================================================

with open(
    "dettagli_valutazione_embeddings.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
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
    "valutazione_finale_embeddings.csv"
)

print(
    "Dettagli salvati in:",
    "dettagli_valutazione_embeddings.csv"
)