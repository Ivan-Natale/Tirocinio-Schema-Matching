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
# SOGLIE GIA' SELEZIONATE SU CUSTOMERS
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
# MATRICE DI SIMILARITA'
# ==================================================

def calcola_matrice(
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


    return util.cos_sim(
        embeddings_a,
        embeddings_b
    )


# ==================================================
# BASELINE ORIGINALE
# ==================================================

def predizioni_baseline(
    matrice,
    schema_a,
    schema_b,
    soglia
):

    predizioni = set()


    for i, attributo_a in enumerate(
        schema_a
    ):

        for j, attributo_b in enumerate(
            schema_b
        ):

            score = matrice[i][j].item()

            if score >= soglia:

                predizioni.add(
                    (
                        attributo_a["nome"],
                        attributo_b["nome"]
                    )
                )


    return predizioni


# ==================================================
# MIGLIOR MATCH RECIPROCO
# ==================================================

def predizioni_reciproche(
    matrice,
    schema_a,
    schema_b,
    soglia
):

    predizioni = set()
    dettagli = []


    # ------------------------------------------------
    # Per ogni attributo A troviamo il miglior B
    # ------------------------------------------------

    migliori_b_per_a = {}

    for i in range(
        len(schema_a)
    ):

        indice_migliore_b = (
            matrice[i]
            .argmax()
            .item()
        )

        migliori_b_per_a[i] = (
            indice_migliore_b
        )


    # ------------------------------------------------
    # Per ogni attributo B troviamo il miglior A
    # ------------------------------------------------

    migliori_a_per_b = {}

    for j in range(
        len(schema_b)
    ):

        indice_migliore_a = (
            matrice[:, j]
            .argmax()
            .item()
        )

        migliori_a_per_b[j] = (
            indice_migliore_a
        )


    # ------------------------------------------------
    # Verifica reciprocita'
    # ------------------------------------------------

    for i, attributo_a in enumerate(
        schema_a
    ):

        j = migliori_b_per_a[i]

        attributo_b = schema_b[j]

        score = matrice[i][j].item()


        # B è il migliore per A
        # e A è il migliore per B

        reciproco = (
            migliori_a_per_b[j]
            ==
            i
        )


        if (
            reciproco
            and
            score >= soglia
        ):

            coppia = (
                attributo_a["nome"],
                attributo_b["nome"]
            )

            predizioni.add(
                coppia
            )


            dettagli.append({
                "attributo_a":
                    attributo_a["nome"],

                "attributo_b":
                    attributo_b["nome"],

                "score":
                    round(
                        score,
                        4
                    ),

                "reciproco":
                    "SI",

                "sopra_soglia":
                    "SI",

                "selezionata":
                    "SI"
            })


    return (
        predizioni,
        dettagli,
        migliori_b_per_a,
        migliori_a_per_b
    )


# ==================================================
# DETTAGLI DELLE COPPIE SOPRA SOGLIA
# ==================================================

def crea_dettagli_completi(
    matrice,
    schema_a,
    schema_b,
    soglia,
    ground_truth,
    predizioni_reciproche_finali,
    migliori_b_per_a,
    migliori_a_per_b,
    configurazione
):

    dettagli = []


    for i, attributo_a in enumerate(
        schema_a
    ):

        for j, attributo_b in enumerate(
            schema_b
        ):

            score = matrice[i][j].item()


            # Salviamo soltanto le coppie
            # che nella baseline originale
            # superavano la soglia.

            if score >= soglia:

                coppia = (
                    attributo_a["nome"],
                    attributo_b["nome"]
                )


                reciproco = (
                    migliori_b_per_a[i] == j
                    and
                    migliori_a_per_b[j] == i
                )


                if coppia in ground_truth:
                    ground_truth_valore = 1
                else:
                    ground_truth_valore = 0


                if coppia in predizioni_reciproche_finali:
                    selezionata = "SI"
                else:
                    selezionata = "NO"


                dettagli.append({
                    "configurazione":
                        configurazione,

                    "attributo_a":
                        attributo_a["nome"],

                    "attributo_b":
                        attributo_b["nome"],

                    "score":
                        round(
                            score,
                            4
                        ),

                    "ground_truth":
                        ground_truth_valore,

                    "migliore_per_a":
                        "SI"
                        if migliori_b_per_a[i] == j
                        else "NO",

                    "migliore_per_b":
                        "SI"
                        if migliori_a_per_b[j] == i
                        else "NO",

                    "reciproco":
                        "SI"
                        if reciproco
                        else "NO",

                    "selezionata":
                        selezionata
                })


    return dettagli


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
    "ESPERIMENTO - MIGLIOR MATCH RECIPROCO"
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


risultati = []
tutti_dettagli = []


for configurazione in configurazioni:

    soglia = SOGLIE[
        configurazione
    ]


    matrice = calcola_matrice(
        modello,
        schema_a,
        schema_b,
        configurazione
    )


    # ==============================================
    # BASELINE ORIGINALE
    # ==============================================

    baseline = predizioni_baseline(
        matrice,
        schema_a,
        schema_b,
        soglia
    )


    (
        tp_base,
        fp_base,
        fn_base,
        precision_base,
        recall_base,
        f1_base
    ) = calcola_metriche(
        baseline,
        ground_truth
    )


    # ==============================================
    # MATCH RECIPROCO
    # ==============================================

    (
        reciproche,
        _,
        migliori_b_per_a,
        migliori_a_per_b
    ) = predizioni_reciproche(
        matrice,
        schema_a,
        schema_b,
        soglia
    )


    (
        tp_rec,
        fp_rec,
        fn_rec,
        precision_rec,
        recall_rec,
        f1_rec
    ) = calcola_metriche(
        reciproche,
        ground_truth
    )


    # ==============================================
    # OUTPUT
    # ==============================================

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
        "Soglia:",
        soglia
    )


    print()
    print("BASELINE ORIGINALE")

    print(
        "TP:",
        tp_base,
        "| FP:",
        fp_base,
        "| FN:",
        fn_base
    )

    print(
        "Precision:",
        round(
            precision_base,
            4
        )
    )

    print(
        "Recall:",
        round(
            recall_base,
            4
        )
    )

    print(
        "F1:",
        round(
            f1_base,
            4
        )
    )


    print()
    print(
        "MIGLIOR MATCH RECIPROCO"
    )

    print(
        "TP:",
        tp_rec,
        "| FP:",
        fp_rec,
        "| FN:",
        fn_rec
    )

    print(
        "Precision:",
        round(
            precision_rec,
            4
        )
    )

    print(
        "Recall:",
        round(
            recall_rec,
            4
        )
    )

    print(
        "F1:",
        round(
            f1_rec,
            4
        )
    )


    print()
    print(
        "COPPIE SELEZIONATE:"
    )

    for coppia in sorted(
        reciproche
    ):

        i = next(
            indice
            for indice, attributo
            in enumerate(schema_a)
            if attributo["nome"]
            ==
            coppia[0]
        )

        j = next(
            indice
            for indice, attributo
            in enumerate(schema_b)
            if attributo["nome"]
            ==
            coppia[1]
        )

        score = (
            matrice[i][j]
            .item()
        )

        if coppia in ground_truth:
            esito = "TP"
        else:
            esito = "FP"

        print(
            coppia[0],
            "<->",
            coppia[1],
            "| score:",
            round(
                score,
                4
            ),
            "|",
            esito
        )


    # ==============================================
    # RISULTATI CSV
    # ==============================================

    risultati.append({
        "configurazione":
            configurazione,

        "soglia":
            soglia,

        "metodo":
            "baseline_originale",

        "tp":
            tp_base,

        "fp":
            fp_base,

        "fn":
            fn_base,

        "precision":
            round(
                precision_base,
                4
            ),

        "recall":
            round(
                recall_base,
                4
            ),

        "f1_score":
            round(
                f1_base,
                4
            )
    })


    risultati.append({
        "configurazione":
            configurazione,

        "soglia":
            soglia,

        "metodo":
            "match_reciproco",

        "tp":
            tp_rec,

        "fp":
            fp_rec,

        "fn":
            fn_rec,

        "precision":
            round(
                precision_rec,
                4
            ),

        "recall":
            round(
                recall_rec,
                4
            ),

        "f1_score":
            round(
                f1_rec,
                4
            )
    })


    dettagli = crea_dettagli_completi(
        matrice,
        schema_a,
        schema_b,
        soglia,
        ground_truth,
        reciproche,
        migliori_b_per_a,
        migliori_a_per_b,
        configurazione
    )


    tutti_dettagli.extend(
        dettagli
    )


# ==================================================
# SALVATAGGIO RISULTATI
# ==================================================

with open(
    "risultati_match_reciproco.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "configurazione",
        "soglia",
        "metodo",
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

        scrittore.writerow(
            risultato
        )


# ==================================================
# SALVATAGGIO DETTAGLI
# ==================================================

with open(
    "dettagli_match_reciproco.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "configurazione",
        "attributo_a",
        "attributo_b",
        "score",
        "ground_truth",
        "migliore_per_a",
        "migliore_per_b",
        "reciproco",
        "selezionata"
    ]

    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )

    scrittore.writeheader()

    for dettaglio in tutti_dettagli:

        scrittore.writerow(
            dettaglio
        )


print()
print(
    "Risultati salvati in:",
    "risultati_match_reciproco.csv"
)

print(
    "Dettagli salvati in:",
    "dettagli_match_reciproco.csv"
)