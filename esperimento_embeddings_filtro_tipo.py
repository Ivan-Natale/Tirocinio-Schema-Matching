import csv

from sentence_transformers import SentenceTransformer, util


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
# LETTURA SCHEMI
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


# ==================================================
# LETTURA GROUND TRUTH
# ==================================================

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

    return nome.replace("_", " ")


def crea_testo(attributo, configurazione):

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

        return nome + ". " + descrizione

    else:

        raise ValueError(
            "Configurazione non valida"
        )


# ==================================================
# CALCOLO METRICHE
# ==================================================

def calcola_metriche(
    predizioni,
    ground_truth
):

    tp = len(
        predizioni & ground_truth
    )

    fp = len(
        predizioni - ground_truth
    )

    fn = len(
        ground_truth - predizioni
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
            * precision
            * recall
            / (precision + recall)
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


    matrice = util.cos_sim(
        embeddings_a,
        embeddings_b
    )

    return matrice


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
# EMBEDDINGS + FILTRO TIPO
# ==================================================

def predizioni_filtro_tipo(
    matrice,
    schema_a,
    schema_b,
    soglia
):

    predizioni = set()

    coppie_escluse_tipo = 0


    for i, attributo_a in enumerate(
        schema_a
    ):

        for j, attributo_b in enumerate(
            schema_b
        ):

            tipo_a = attributo_a[
                "tipo"
            ]

            tipo_b = attributo_b[
                "tipo"
            ]


            # Se i tipi sono diversi,
            # la coppia viene esclusa.

            if tipo_a != tipo_b:

                coppie_escluse_tipo += 1
                continue


            score = matrice[i][j].item()


            if score >= soglia:

                predizioni.add(
                    (
                        attributo_a["nome"],
                        attributo_b["nome"]
                    )
                )


    return (
        predizioni,
        coppie_escluse_tipo
    )


# ==================================================
# DETTAGLI DELLE COPPIE
# ==================================================

def crea_dettagli(
    matrice,
    schema_a,
    schema_b,
    soglia,
    ground_truth,
    predizioni_filtro,
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

            tipo_a = attributo_a[
                "tipo"
            ]

            tipo_b = attributo_b[
                "tipo"
            ]

            tipi_compatibili = (
                tipo_a == tipo_b
            )


            # Salviamo le coppie che nella
            # baseline originale superavano
            # la soglia.

            if score >= soglia:

                coppia = (
                    attributo_a["nome"],
                    attributo_b["nome"]
                )


                if coppia in ground_truth:

                    gt = 1

                else:

                    gt = 0


                if coppia in predizioni_filtro:

                    selezionata = "SI"

                else:

                    selezionata = "NO"


                dettagli.append({
                    "configurazione":
                        configurazione,

                    "attributo_a":
                        attributo_a["nome"],

                    "tipo_a":
                        tipo_a,

                    "attributo_b":
                        attributo_b["nome"],

                    "tipo_b":
                        tipo_b,

                    "score":
                        round(score, 4),

                    "ground_truth":
                        gt,

                    "tipi_compatibili":
                        "SI"
                        if tipi_compatibili
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
    "ESPERIMENTO - EMBEDDINGS + FILTRO TIPO"
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
    # FILTRO SUL TIPO
    # ==============================================

    (
        filtro_tipo,
        coppie_escluse_tipo
    ) = predizioni_filtro_tipo(
        matrice,
        schema_a,
        schema_b,
        soglia
    )


    (
        tp_tipo,
        fp_tipo,
        fn_tipo,
        precision_tipo,
        recall_tipo,
        f1_tipo
    ) = calcola_metriche(
        filtro_tipo,
        ground_truth
    )


    # ==============================================
    # STAMPA RISULTATI
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
    print(
        "BASELINE ORIGINALE"
    )

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
        "EMBEDDINGS + FILTRO TIPO"
    )

    print(
        "TP:",
        tp_tipo,
        "| FP:",
        fp_tipo,
        "| FN:",
        fn_tipo
    )

    print(
        "Precision:",
        round(
            precision_tipo,
            4
        )
    )

    print(
        "Recall:",
        round(
            recall_tipo,
            4
        )
    )

    print(
        "F1:",
        round(
            f1_tipo,
            4
        )
    )

    print(
        "Coppie escluse per tipo:",
        coppie_escluse_tipo
    )


    print()
    print(
        "COPPIE SELEZIONATE:"
    )


    for coppia in sorted(
        filtro_tipo
    ):

        i = next(
            indice
            for indice, attributo
            in enumerate(schema_a)
            if attributo["nome"]
            == coppia[0]
        )

        j = next(
            indice
            for indice, attributo
            in enumerate(schema_b)
            if attributo["nome"]
            == coppia[1]
        )

        score = matrice[i][j].item()

        tipo_a = schema_a[i][
            "tipo"
        ]

        tipo_b = schema_b[j][
            "tipo"
        ]


        if coppia in ground_truth:

            esito = "TP"

        else:

            esito = "FP"


        print(
            coppia[0],
            "(",
            tipo_a,
            ")",
            "<->",
            coppia[1],
            "(",
            tipo_b,
            ")",
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
            ),

        "coppie_escluse_tipo":
            0
    })


    risultati.append({
        "configurazione":
            configurazione,

        "soglia":
            soglia,

        "metodo":
            "filtro_tipo",

        "tp":
            tp_tipo,

        "fp":
            fp_tipo,

        "fn":
            fn_tipo,

        "precision":
            round(
                precision_tipo,
                4
            ),

        "recall":
            round(
                recall_tipo,
                4
            ),

        "f1_score":
            round(
                f1_tipo,
                4
            ),

        "coppie_escluse_tipo":
            coppie_escluse_tipo
    })


    dettagli = crea_dettagli(
        matrice,
        schema_a,
        schema_b,
        soglia,
        ground_truth,
        filtro_tipo,
        configurazione
    )

    tutti_dettagli.extend(
        dettagli
    )


# ==================================================
# SALVATAGGIO RISULTATI
# ==================================================

with open(
    "risultati_embeddings_filtro_tipo.csv",
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
        "f1_score",
        "coppie_escluse_tipo"
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
    "dettagli_embeddings_filtro_tipo.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [
        "configurazione",
        "attributo_a",
        "tipo_a",
        "attributo_b",
        "tipo_b",
        "score",
        "ground_truth",
        "tipi_compatibili",
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
    "risultati_embeddings_filtro_tipo.csv"
)

print(
    "Dettagli salvati in:",
    "dettagli_embeddings_filtro_tipo.csv"
)