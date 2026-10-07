import csv
from functools import lru_cache


# --------------------------------------------------
# DATASET DI SVILUPPO
# --------------------------------------------------

FILE_SCHEMA_A = "schema_a.csv"
FILE_SCHEMA_B = "schema_b.csv"
FILE_GROUND_TRUTH = "ground_truth.csv"


# --------------------------------------------------
# PARAMETRI DA TESTARE
# --------------------------------------------------

SOGLIE = [
    0.20,
    0.30,
    0.33,
    0.50,
    0.70
]

PESI = [
    (0.80, 0.20),
    (0.70, 0.30),
    (0.60, 0.40)
]


# --------------------------------------------------
# LETTURA SCHEMI
# --------------------------------------------------

def leggi_schema(nome_file):

    attributi = []

    with open(
        nome_file,
        "r",
        encoding="utf-8-sig"
    ) as file:

        lettore = csv.DictReader(file)

        for riga in lettore:

            attributo = {
                "nome": riga["attribute"].strip(),
                "tipo": riga["type"].strip(),
                "descrizione": riga["description"].strip()
            }

            attributi.append(attributo)

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


# --------------------------------------------------
# METRICHE
# --------------------------------------------------

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


# --------------------------------------------------
# SIMILARITA'
# --------------------------------------------------

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

    else:

        return similarita_levenshtein(
            testo_a,
            testo_b
        )


# --------------------------------------------------
# VALUTAZIONE DI UNA CONFIGURAZIONE
# --------------------------------------------------

def valuta(
    algoritmo,
    configurazione,
    schema_a,
    schema_b,
    ground_truth,
    soglia,
    peso_nome=None,
    peso_descrizione=None
):

    predizioni = set()

    coppie_escluse_tipo = 0

    for attributo_a in schema_a:

        for attributo_b in schema_b:

            nome_a = attributo_a["nome"]
            nome_b = attributo_b["nome"]

            descrizione_a = attributo_a["descrizione"]
            descrizione_b = attributo_b["descrizione"]

            tipo_a = attributo_a["tipo"]
            tipo_b = attributo_b["tipo"]


            # --------------------------------------
            # SOLO NOME
            # --------------------------------------

            if configurazione == "solo_nome":

                score = calcola_similarita(
                    algoritmo,
                    nome_a,
                    nome_b
                )


            # --------------------------------------
            # SOLA DESCRIZIONE
            # --------------------------------------

            elif configurazione == "sola_descrizione":

                score = calcola_similarita(
                    algoritmo,
                    descrizione_a,
                    descrizione_b
                )


            # --------------------------------------
            # NOME + DESCRIZIONE
            # --------------------------------------

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


            # --------------------------------------
            # NOME + FILTRO TIPO
            # --------------------------------------

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

                predizioni.add(
                    (
                        nome_a,
                        nome_b
                    )
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


    return {
        "algoritmo": algoritmo,
        "configurazione": configurazione,
        "peso_nome": peso_nome,
        "peso_descrizione": peso_descrizione,
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


# --------------------------------------------------
# SELEZIONE MIGLIORE CONFIGURAZIONE
# --------------------------------------------------

def scegli_migliore(
    risultati,
    configurazione
):

    candidati = [
        risultato
        for risultato in risultati
        if risultato["configurazione"]
        ==
        configurazione
    ]

    if configurazione == "nome_descrizione":

        candidati.sort(
            key=lambda x: (
                x["f1_score"],
                x["precision"],
                x["peso_nome"],
                x["soglia"]
            ),
            reverse=True
        )

    else:

        candidati.sort(
            key=lambda x: (
                x["f1_score"],
                x["precision"],
                x["soglia"]
            ),
            reverse=True
        )

    return candidati[0]


# --------------------------------------------------
# CARICAMENTO DATASET
# --------------------------------------------------

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
    "SELEZIONE PARAMETRI - CONFRONTO LESSICALE"
)

print(
    "DATASET DI SVILUPPO: CUSTOMERS"
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


# --------------------------------------------------
# ESPERIMENTI
# --------------------------------------------------

risultati = []


for algoritmo in [
    "JACCARD",
    "LEVENSHTEIN"
]:

    print()
    print(
        "##################################################"
    )

    print(
        "ALGORITMO:",
        algoritmo
    )

    print(
        "##################################################"
    )


    # ----------------------------------------------
    # SOLO NOME
    # ----------------------------------------------

    print()
    print("CONFIGURAZIONE: SOLO NOME")

    for soglia in SOGLIE:

        risultato = valuta(
            algoritmo,
            "solo_nome",
            schema_a,
            schema_b,
            ground_truth,
            soglia
        )

        risultati.append(
            risultato
        )

        print(
            "Soglia:",
            soglia,
            "| TP:",
            risultato["tp"],
            "| FP:",
            risultato["fp"],
            "| FN:",
            risultato["fn"],
            "| Precision:",
            risultato["precision"],
            "| Recall:",
            risultato["recall"],
            "| F1:",
            risultato["f1_score"]
        )


    # ----------------------------------------------
    # SOLA DESCRIZIONE
    # ----------------------------------------------

    print()
    print(
        "CONFIGURAZIONE: SOLA DESCRIZIONE"
    )

    for soglia in SOGLIE:

        risultato = valuta(
            algoritmo,
            "sola_descrizione",
            schema_a,
            schema_b,
            ground_truth,
            soglia
        )

        risultati.append(
            risultato
        )

        print(
            "Soglia:",
            soglia,
            "| TP:",
            risultato["tp"],
            "| FP:",
            risultato["fp"],
            "| FN:",
            risultato["fn"],
            "| Precision:",
            risultato["precision"],
            "| Recall:",
            risultato["recall"],
            "| F1:",
            risultato["f1_score"]
        )


    # ----------------------------------------------
    # NOME + DESCRIZIONE
    # ----------------------------------------------

    print()
    print(
        "CONFIGURAZIONE: NOME + DESCRIZIONE"
    )

    for peso_nome, peso_descrizione in PESI:

        for soglia in SOGLIE:

            risultato = valuta(
                algoritmo,
                "nome_descrizione",
                schema_a,
                schema_b,
                ground_truth,
                soglia,
                peso_nome,
                peso_descrizione
            )

            risultati.append(
                risultato
            )

            print(
                "Nome:",
                peso_nome,
                "| Descrizione:",
                peso_descrizione,
                "| Soglia:",
                soglia,
                "| TP:",
                risultato["tp"],
                "| FP:",
                risultato["fp"],
                "| FN:",
                risultato["fn"],
                "| Precision:",
                risultato["precision"],
                "| Recall:",
                risultato["recall"],
                "| F1:",
                risultato["f1_score"]
            )


    # ----------------------------------------------
    # NOME + FILTRO TIPO
    # ----------------------------------------------

    print()
    print(
        "CONFIGURAZIONE: NOME + FILTRO TIPO"
    )

    for soglia in SOGLIE:

        risultato = valuta(
            algoritmo,
            "nome_filtro_tipo",
            schema_a,
            schema_b,
            ground_truth,
            soglia
        )

        risultati.append(
            risultato
        )

        print(
            "Soglia:",
            soglia,
            "| TP:",
            risultato["tp"],
            "| FP:",
            risultato["fp"],
            "| FN:",
            risultato["fn"],
            "| Precision:",
            risultato["precision"],
            "| Recall:",
            risultato["recall"],
            "| F1:",
            risultato["f1_score"],
            "| Escluse per tipo:",
            risultato[
                "coppie_escluse_tipo"
            ]
        )


# --------------------------------------------------
# SALVATAGGIO DI TUTTI I RISULTATI
# --------------------------------------------------

with open(
    "selezione_parametri_lessicali.csv",
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

    for risultato in risultati:

        scrittore.writerow(
            risultato
        )


# --------------------------------------------------
# PARAMETRI SELEZIONATI
# --------------------------------------------------

print()
print()
print(
    "=================================================="
)

print(
    "PARAMETRI SELEZIONATI SU CUSTOMERS"
)

print(
    "=================================================="
)


migliori = []


for algoritmo in [
    "JACCARD",
    "LEVENSHTEIN"
]:

    risultati_algoritmo = [
        risultato
        for risultato in risultati
        if risultato["algoritmo"]
        ==
        algoritmo
    ]

    for configurazione in [
        "solo_nome",
        "sola_descrizione",
        "nome_descrizione",
        "nome_filtro_tipo"
    ]:

        migliore = scegli_migliore(
            risultati_algoritmo,
            configurazione
        )

        migliori.append(
            migliore
        )

        print()
        print(
            algoritmo,
            "-",
            configurazione
        )

        print(
            "Soglia:",
            migliore["soglia"]
        )

        if configurazione == "nome_descrizione":

            print(
                "Peso nome:",
                migliore["peso_nome"]
            )

            print(
                "Peso descrizione:",
                migliore[
                    "peso_descrizione"
                ]
            )

        print(
            "Precision:",
            migliore["precision"]
        )

        print(
            "Recall:",
            migliore["recall"]
        )

        print(
            "F1:",
            migliore["f1_score"]
        )


# --------------------------------------------------
# SALVATAGGIO PARAMETRI SELEZIONATI
# --------------------------------------------------

with open(
    "parametri_lessicali_selezionati.csv",
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

    for migliore in migliori:

        scrittore.writerow(
            migliore
        )


print()
print(
    "Risultati completi salvati in:",
    "selezione_parametri_lessicali.csv"
)

print(
    "Parametri scelti salvati in:",
    "parametri_lessicali_selezionati.csv"
)