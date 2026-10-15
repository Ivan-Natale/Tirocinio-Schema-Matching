import csv

from sentence_transformers import SentenceTransformer, util


# ============================================================
# FILE DEL DATASET PUBBLICO
# ============================================================

FILE_MIMIC = "data_validation/MIMIC_III_Schema.csv"
FILE_OMOP = "data_validation/OMOP_Schema.csv"
FILE_MAPPING = "data_validation/MIMIC_to_OMOP_Mapping.csv"


# ============================================================
# MODELLO EMBEDDINGS
# ============================================================

NOME_MODELLO = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# PARAMETRI FISSATI PRIMA DELLA VALIDAZIONE
# ============================================================

SOGLIA_LEVENSHTEIN = 0.33

SOGLIE_EMBEDDINGS = {
    "solo_nome": 0.80,
    "sola_descrizione": 0.65,
    "nome_descrizione": 0.75
}


# ============================================================
# FUNZIONI DI NORMALIZZAZIONE
# ============================================================

def pulisci_testo(testo):

    if testo is None:
        return ""

    return str(testo).strip()


def normalizza_nome(nome):

    nome = pulisci_testo(nome)

    return (
        nome
        .replace("_", " ")
        .lower()
    )


def normalizza_tipo_esatto(tipo):

    """
    Normalizzazione minima per il filtro rigido.

    INTEGER e integer vengono considerati uguali.

    INTEGER e BIGINT rimangono diversi.
    STRING e VARCHAR rimangono diversi.
    """

    return (
        pulisci_testo(tipo)
        .upper()
        .replace(" ", "")
    )


def crea_id(tabella, colonna):

    """
    L'identità di una colonna comprende anche la tabella.

    Esempio:
    ADMISSIONS.SUBJECT_ID
    """

    return (
        pulisci_testo(tabella).upper()
        + "."
        + pulisci_testo(colonna).upper()
    )


# ============================================================
# NUOVA ESTENSIONE:
# FAMIGLIE DI TIPI
# ============================================================

def famiglia_tipo(tipo):

    tipo = (
        pulisci_testo(tipo)
        .lower()
        .strip()
    )

    # Tolgo eventuali dimensioni:
    # varchar(50) -> varchar
    # numeric(10,2) -> numeric

    if "(" in tipo:
        tipo_base = tipo.split("(")[0].strip()
    else:
        tipo_base = tipo


    tipi_numerici = {
        "integer",
        "int",
        "bigint",
        "smallint",
        "float",
        "double",
        "decimal",
        "numeric"
    }

    tipi_testuali = {
        "text",
        "varchar",
        "char",
        "string"
    }

    tipi_temporali = {
        "date",
        "datetime",
        "timestamp"
    }

    tipi_booleani = {
        "boolean",
        "bool"
    }


    if tipo_base in tipi_numerici:
        return "NUMERICO"

    if tipo_base in tipi_testuali:
        return "TESTUALE"

    if tipo_base in tipi_temporali:
        return "TEMPORALE"

    if tipo_base in tipi_booleani:
        return "BOOLEANO"


    # I tipi non previsti nel piano non vengono
    # forzati dentro una famiglia.

    return "ALTRO:" + tipo_base.upper()


# ============================================================
# LETTURA SCHEMI
# ============================================================

def leggi_schema(nome_file):

    attributi = []

    with open(
        nome_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        lettore = csv.DictReader(file)

        colonne_richieste = {
            "TableName",
            "ColumnName",
            "ColumnDesc",
            "ColumnType"
        }

        if not colonne_richieste.issubset(
            set(lettore.fieldnames)
        ):

            raise ValueError(
                f"Colonne mancanti in {nome_file}. "
                f"Trovate: {lettore.fieldnames}"
            )


        for riga in lettore:

            tabella = pulisci_testo(
                riga["TableName"]
            )

            nome = pulisci_testo(
                riga["ColumnName"]
            )

            descrizione = pulisci_testo(
                riga["ColumnDesc"]
            )

            tipo = pulisci_testo(
                riga["ColumnType"]
            )


            # Evitiamo eventuali righe vuote.

            if tabella == "" or nome == "":
                continue


            attributi.append({
                "id": crea_id(
                    tabella,
                    nome
                ),

                "tabella": tabella,

                "nome": nome,

                "descrizione":
                    descrizione,

                "tipo":
                    tipo,

                "tipo_esatto":
                    normalizza_tipo_esatto(
                        tipo
                    ),

                "famiglia_tipo":
                    famiglia_tipo(
                        tipo
                    )
            })


    return attributi


# ============================================================
# LETTURA DELLA GROUND TRUTH
# ============================================================

def leggi_mapping(nome_file):

    righe_mapping = []

    with open(
        nome_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        lettore = csv.DictReader(file)

        colonne_richieste = {
            "SRC_ENT",
            "SRC_ATT",
            "TGT_ENT",
            "TGT_ATT"
        }

        if not colonne_richieste.issubset(
            set(lettore.fieldnames)
        ):

            raise ValueError(
                "Formato mapping non riconosciuto. "
                f"Colonne trovate: {lettore.fieldnames}"
            )


        for riga in lettore:

            src_ent = pulisci_testo(
                riga["SRC_ENT"]
            )

            src_att = pulisci_testo(
                riga["SRC_ATT"]
            )

            tgt_ent = pulisci_testo(
                riga["TGT_ENT"]
            )

            tgt_att = pulisci_testo(
                riga["TGT_ATT"]
            )


            if (
                src_ent == ""
                or
                src_att == ""
            ):
                continue


            righe_mapping.append({
                "src_id":
                    crea_id(
                        src_ent,
                        src_att
                    ),

                "src_ent":
                    src_ent,

                "src_att":
                    src_att,

                "tgt_ent":
                    tgt_ent,

                "tgt_att":
                    tgt_att
            })


    return righe_mapping


# ============================================================
# COSTRUZIONE GROUND TRUTH POSITIVA
# ============================================================

def costruisci_ground_truth(
    righe_mapping,
    ids_mimic,
    ids_omop
):

    ground_truth = set()

    sorgenti_annotate = set()

    mapping_non_risolti = []


    valori_senza_match = {
        "",
        "NA",
        "N/A",
        "NONE",
        "NULL",
        "0"
    }


    for riga in righe_mapping:

        src_id = riga["src_id"]

        sorgenti_annotate.add(
            src_id
        )


        tgt_ent = (
            riga["tgt_ent"]
            .strip()
            .upper()
        )

        tgt_att = (
            riga["tgt_att"]
            .strip()
            .upper()
        )


        # NA,NA oppure 0,0 indicano
        # assenza di mapping positivo.

        if (
            tgt_ent in valori_senza_match
            or
            tgt_att in valori_senza_match
        ):
            continue


        tgt_id = crea_id(
            riga["tgt_ent"],
            riga["tgt_att"]
        )


        # Controlliamo che le colonne indicate
        # dalla ground truth esistano davvero
        # negli schemi caricati.

        if (
            src_id not in ids_mimic
            or
            tgt_id not in ids_omop
        ):

            mapping_non_risolti.append({
                "src_id":
                    src_id,

                "tgt_id":
                    tgt_id
            })

            continue


        ground_truth.add(
            (
                src_id,
                tgt_id
            )
        )


    return (
        ground_truth,
        sorgenti_annotate,
        mapping_non_risolti
    )


# ============================================================
# CREAZIONE TESTI PER EMBEDDINGS
# ============================================================

def crea_testo(
    attributo,
    configurazione
):

    nome = normalizza_nome(
        attributo["nome"]
    )

    descrizione = pulisci_testo(
        attributo["descrizione"]
    )


    if configurazione == "solo_nome":

        return nome


    if configurazione == "sola_descrizione":

        return descrizione


    if configurazione == "nome_descrizione":

        if descrizione == "":
            return nome

        return (
            nome
            + ". "
            + descrizione
        )


    raise ValueError(
        "Configurazione embeddings non valida"
    )


# ============================================================
# LEVENSHTEIN
# ============================================================

def distanza_levenshtein(
    stringa_a,
    stringa_b
):

    """
    Implementazione iterativa della stessa distanza
    di Levenshtein utilizzata nelle baseline.

    Viene usata una sola riga della matrice
    per rendere il calcolo più efficiente
    sul dataset pubblico più grande.
    """

    if stringa_a == stringa_b:
        return 0

    if len(stringa_a) == 0:
        return len(stringa_b)

    if len(stringa_b) == 0:
        return len(stringa_a)


    # Per consumare meno memoria usiamo
    # come seconda stringa quella più corta.

    if len(stringa_a) < len(stringa_b):

        stringa_a, stringa_b = (
            stringa_b,
            stringa_a
        )


    riga_precedente = list(
        range(
            len(stringa_b) + 1
        )
    )


    for i, carattere_a in enumerate(
        stringa_a,
        start=1
    ):

        riga_corrente = [i]


        for j, carattere_b in enumerate(
            stringa_b,
            start=1
        ):

            costo_inserimento = (
                riga_corrente[j - 1]
                + 1
            )

            costo_cancellazione = (
                riga_precedente[j]
                + 1
            )

            costo_sostituzione = (
                riga_precedente[j - 1]
                +
                (
                    0
                    if carattere_a
                    == carattere_b
                    else 1
                )
            )


            riga_corrente.append(
                min(
                    costo_inserimento,
                    costo_cancellazione,
                    costo_sostituzione
                )
            )


        riga_precedente = (
            riga_corrente
        )


    return riga_precedente[-1]


def similarita_levenshtein(
    stringa_a,
    stringa_b
):

    if (
        stringa_a == ""
        and
        stringa_b == ""
    ):
        return 1.0


    lunghezza_massima = max(
        len(stringa_a),
        len(stringa_b)
    )


    if lunghezza_massima == 0:
        return 0.0


    distanza = distanza_levenshtein(
        stringa_a,
        stringa_b
    )


    return (
        1
        -
        distanza
        /
        lunghezza_massima
    )


# ============================================================
# METRICHE
# ============================================================

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

        precision = 0.0


    if tp + fn > 0:

        recall = (
            tp
            /
            (tp + fn)
        )

    else:

        recall = 0.0


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

        f1 = 0.0


    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1
    }


# ============================================================
# BASELINE LEVENSHTEIN + FILTRO TIPO
# ============================================================

def esegui_levenshtein(
    schema_mimic,
    schema_omop
):

    predizioni = set()

    scores = {}


    for attributo_a in schema_mimic:

        nome_a = normalizza_nome(
            attributo_a["nome"]
        )


        for attributo_b in schema_omop:

            # Filtro rigido sul tipo,
            # già fissato negli esperimenti precedenti.

            if (
                attributo_a["tipo_esatto"]
                !=
                attributo_b["tipo_esatto"]
            ):
                continue


            nome_b = normalizza_nome(
                attributo_b["nome"]
            )


            score = similarita_levenshtein(
                nome_a,
                nome_b
            )


            coppia = (
                attributo_a["id"],
                attributo_b["id"]
            )


            scores[coppia] = score


            if score >= SOGLIA_LEVENSHTEIN:

                predizioni.add(
                    coppia
                )


    return predizioni, scores


# ============================================================
# MATRICE EMBEDDINGS
# ============================================================

def calcola_matrice_embeddings(
    modello,
    schema_mimic,
    schema_omop,
    configurazione
):

    testi_mimic = [
        crea_testo(
            attributo,
            configurazione
        )
        for attributo in schema_mimic
    ]

    testi_omop = [
        crea_testo(
            attributo,
            configurazione
        )
        for attributo in schema_omop
    ]


    embeddings_mimic = modello.encode(
        testi_mimic,
        convert_to_tensor=True,
        batch_size=64,
        show_progress_bar=True
    )


    embeddings_omop = modello.encode(
        testi_omop,
        convert_to_tensor=True,
        batch_size=64,
        show_progress_bar=True
    )


    return util.cos_sim(
        embeddings_mimic,
        embeddings_omop
    )


# ============================================================
# EMBEDDINGS STANDARD
# ============================================================

def predizioni_embeddings(
    matrice,
    schema_mimic,
    schema_omop,
    soglia
):

    predizioni = set()


    for i, attributo_a in enumerate(
        schema_mimic
    ):

        for j, attributo_b in enumerate(
            schema_omop
        ):

            score = (
                matrice[i][j]
                .item()
            )


            if score >= soglia:

                predizioni.add(
                    (
                        attributo_a["id"],
                        attributo_b["id"]
                    )
                )


    return predizioni


# ============================================================
# EMBEDDINGS + FILTRO TIPO ESATTO
# ============================================================

def predizioni_embeddings_tipo_esatto(
    matrice,
    schema_mimic,
    schema_omop,
    soglia
):

    predizioni = set()


    for i, attributo_a in enumerate(
        schema_mimic
    ):

        for j, attributo_b in enumerate(
            schema_omop
        ):

            if (
                attributo_a["tipo_esatto"]
                !=
                attributo_b["tipo_esatto"]
            ):
                continue


            score = (
                matrice[i][j]
                .item()
            )


            if score >= soglia:

                predizioni.add(
                    (
                        attributo_a["id"],
                        attributo_b["id"]
                    )
                )


    return predizioni


# ============================================================
# NUOVA ESTENSIONE:
# EMBEDDINGS + FAMIGLIE DI TIPI
# ============================================================

def predizioni_embeddings_famiglie_tipo(
    matrice,
    schema_mimic,
    schema_omop,
    soglia
):

    predizioni = set()


    for i, attributo_a in enumerate(
        schema_mimic
    ):

        for j, attributo_b in enumerate(
            schema_omop
        ):

            if (
                attributo_a["famiglia_tipo"]
                !=
                attributo_b["famiglia_tipo"]
            ):
                continue


            score = (
                matrice[i][j]
                .item()
            )


            if score >= soglia:

                predizioni.add(
                    (
                        attributo_a["id"],
                        attributo_b["id"]
                    )
                )


    return predizioni


# ============================================================
# EMBEDDINGS + MIGLIOR MATCH RECIPROCO
# ============================================================

def predizioni_match_reciproco(
    matrice,
    schema_mimic,
    schema_omop,
    soglia
):

    predizioni = set()


    # Il dataset reale contiene molti nomi ripetuti.
    # In caso di parità consideriamo tutti i candidati
    # che raggiungono lo score massimo.
    #
    # Questo evita che l'ordine delle righe del CSV
    # scelga arbitrariamente uno dei candidati.

    tolleranza = 1e-7


    massimi_per_mimic = []

    for i in range(
        len(schema_mimic)
    ):

        massimo = (
            matrice[i]
            .max()
            .item()
        )

        massimi_per_mimic.append(
            massimo
        )


    massimi_per_omop = []

    for j in range(
        len(schema_omop)
    ):

        massimo = (
            matrice[:, j]
            .max()
            .item()
        )

        massimi_per_omop.append(
            massimo
        )


    for i, attributo_a in enumerate(
        schema_mimic
    ):

        for j, attributo_b in enumerate(
            schema_omop
        ):

            score = (
                matrice[i][j]
                .item()
            )


            if score < soglia:
                continue


            migliore_per_a = (
                abs(
                    score
                    -
                    massimi_per_mimic[i]
                )
                <=
                tolleranza
            )


            migliore_per_b = (
                abs(
                    score
                    -
                    massimi_per_omop[j]
                )
                <=
                tolleranza
            )


            if (
                migliore_per_a
                and
                migliore_per_b
            ):

                predizioni.add(
                    (
                        attributo_a["id"],
                        attributo_b["id"]
                    )
                )


    return predizioni


# ============================================================
# AGGIUNTA RISULTATO ALLA TABELLA
# ============================================================

def aggiungi_risultato(
    risultati,
    metodo,
    configurazione,
    soglia,
    predizioni,
    ground_truth,
    note=""
):

    metriche = calcola_metriche(
        predizioni,
        ground_truth
    )


    risultati.append({
        "metodo":
            metodo,

        "configurazione":
            configurazione,

        "soglia":
            soglia,

        "predizioni":
            len(predizioni),

        "tp":
            metriche["tp"],

        "fp":
            metriche["fp"],

        "fn":
            metriche["fn"],

        "precision":
            round(
                metriche["precision"],
                4
            ),

        "recall":
            round(
                metriche["recall"],
                4
            ),

        "f1_score":
            round(
                metriche["f1"],
                4
            ),

        "note":
            note
    })


# ============================================================
# CREAZIONE CASI SIGNIFICATIVI
# ============================================================

def aggiungi_casi_embeddings(
    casi,
    nome_metodo,
    configurazione,
    matrice,
    schema_mimic,
    schema_omop,
    predizioni,
    ground_truth,
    massimo_fp=50
):

    indice_mimic = {
        attributo["id"]: i
        for i, attributo
        in enumerate(schema_mimic)
    }

    indice_omop = {
        attributo["id"]: j
        for j, attributo
        in enumerate(schema_omop)
    }


    union = (
        predizioni
        |
        ground_truth
    )


    righe_tp = []
    righe_fn = []
    righe_fp = []


    for src_id, tgt_id in union:

        if (
            src_id not in indice_mimic
            or
            tgt_id not in indice_omop
        ):
            continue


        i = indice_mimic[src_id]
        j = indice_omop[tgt_id]


        score = (
            matrice[i][j]
            .item()
        )


        predetta = (
            (src_id, tgt_id)
            in
            predizioni
        )

        corretta = (
            (src_id, tgt_id)
            in
            ground_truth
        )


        if predetta and corretta:
            esito = "TP"

        elif predetta:
            esito = "FP"

        else:
            esito = "FN"


        riga = {
            "metodo":
                nome_metodo,

            "configurazione":
                configurazione,

            "sorgente":
                src_id,

            "target":
                tgt_id,

            "score":
                round(
                    score,
                    4
                ),

            "tipo_sorgente":
                schema_mimic[i]["tipo"],

            "tipo_target":
                schema_omop[j]["tipo"],

            "famiglia_sorgente":
                schema_mimic[i][
                    "famiglia_tipo"
                ],

            "famiglia_target":
                schema_omop[j][
                    "famiglia_tipo"
                ],

            "esito":
                esito
        }


        if esito == "TP":
            righe_tp.append(riga)

        elif esito == "FN":
            righe_fn.append(riga)

        else:
            righe_fp.append(riga)


    # Per non creare un CSV enorme,
    # salviamo tutti TP e FN,
    # ma soltanto i 50 FP con score maggiore.

    righe_fp.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    casi.extend(
        righe_tp
    )

    casi.extend(
        righe_fn
    )

    casi.extend(
        righe_fp[:massimo_fp]
    )


# ============================================================
# SALVATAGGIO CSV
# ============================================================

def salva_risultati(
    risultati
):

    with open(
        "risultati_validazione_mimic_omop.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        colonne = [
            "metodo",
            "configurazione",
            "soglia",
            "predizioni",
            "tp",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1_score",
            "note"
        ]


        scrittore = csv.DictWriter(
            file,
            fieldnames=colonne
        )

        scrittore.writeheader()

        for riga in risultati:
            scrittore.writerow(riga)


def salva_casi(
    casi
):

    with open(
        "casi_validazione_mimic_omop.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        colonne = [
            "metodo",
            "configurazione",
            "sorgente",
            "target",
            "score",
            "tipo_sorgente",
            "tipo_target",
            "famiglia_sorgente",
            "famiglia_target",
            "esito"
        ]


        scrittore = csv.DictWriter(
            file,
            fieldnames=colonne
        )

        scrittore.writeheader()

        for riga in casi:
            scrittore.writerow(riga)


def salva_mapping_non_risolti(
    mapping_non_risolti
):

    with open(
        "mapping_non_risolti.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        colonne = [
            "src_id",
            "tgt_id"
        ]


        scrittore = csv.DictWriter(
            file,
            fieldnames=colonne
        )

        scrittore.writeheader()

        for riga in mapping_non_risolti:
            scrittore.writerow(riga)


# ============================================================
# PROGRAMMA PRINCIPALE
# ============================================================

print()
print(
    "VALIDAZIONE ESTERNA MIMIC-III -> OMOP"
)

print(
    "====================================="
)

print()


# ============================================================
# LETTURA DATI
# ============================================================

schema_mimic_completo = leggi_schema(
    FILE_MIMIC
)

schema_omop = leggi_schema(
    FILE_OMOP
)

righe_mapping = leggi_mapping(
    FILE_MAPPING
)


ids_mimic = {
    attributo["id"]
    for attributo
    in schema_mimic_completo
}

ids_omop = {
    attributo["id"]
    for attributo
    in schema_omop
}


(
    ground_truth,
    sorgenti_annotate,
    mapping_non_risolti
) = costruisci_ground_truth(
    righe_mapping,
    ids_mimic,
    ids_omop
)


# Utilizziamo soltanto le colonne MIMIC
# che sono effettivamente annotate nel file
# di mapping, comprese quelle marcate NA.
#
# In questo modo non trattiamo come falsi
# positivi colonne per cui non abbiamo
# un'annotazione nella ground truth.

schema_mimic = [
    attributo
    for attributo
    in schema_mimic_completo
    if attributo["id"]
    in sorgenti_annotate
]


print(
    "Attributi MIMIC completi:",
    len(schema_mimic_completo)
)

print(
    "Attributi MIMIC annotati:",
    len(schema_mimic)
)

print(
    "Attributi OMOP:",
    len(schema_omop)
)

print(
    "Corrispondenze positive GT:",
    len(ground_truth)
)

print(
    "Mapping non risolti:",
    len(mapping_non_risolti)
)


salva_mapping_non_risolti(
    mapping_non_risolti
)


if len(mapping_non_risolti) > 0:

    print()
    print(
        "ATTENZIONE:"
    )

    print(
        "Sono presenti mapping positivi "
        "che non corrispondono agli schemi."
    )

    print(
        "Controllare mapping_non_risolti.csv "
        "prima di interpretare i risultati."
    )


# ============================================================
# RISULTATI
# ============================================================

risultati = []
casi = []


# ============================================================
# 1. LEVENSHTEIN + FILTRO TIPO
# ============================================================

print()
print(
    "1. Levenshtein + filtro tipo..."
)


pred_levenshtein, _ = (
    esegui_levenshtein(
        schema_mimic,
        schema_omop
    )
)


aggiungi_risultato(
    risultati,
    metodo="Levenshtein",
    configurazione="nome_filtro_tipo",
    soglia=SOGLIA_LEVENSHTEIN,
    predizioni=pred_levenshtein,
    ground_truth=ground_truth,
    note="Filtro tipo con uguaglianza esatta"
)


metriche_lev = calcola_metriche(
    pred_levenshtein,
    ground_truth
)


print(
    "TP:",
    metriche_lev["tp"],
    "| FP:",
    metriche_lev["fp"],
    "| FN:",
    metriche_lev["fn"],
    "| F1:",
    round(
        metriche_lev["f1"],
        4
    )
)


# ============================================================
# CARICAMENTO MODELLO
# ============================================================

print()
print(
    "Caricamento modello embeddings..."
)


modello = SentenceTransformer(
    NOME_MODELLO
)

modello.eval()


print(
    "Modello caricato:",
    NOME_MODELLO
)


# ============================================================
# CONFIGURAZIONI EMBEDDINGS
# ============================================================

configurazioni = [
    "solo_nome",
    "sola_descrizione",
    "nome_descrizione"
]


for configurazione in configurazioni:

    soglia = SOGLIE_EMBEDDINGS[
        configurazione
    ]


    print()
    print(
        "====================================="
    )

    print(
        "CONFIGURAZIONE:",
        configurazione
    )

    print(
        "Soglia fissata:",
        soglia
    )

    print(
        "====================================="
    )


    matrice = calcola_matrice_embeddings(
        modello,
        schema_mimic,
        schema_omop,
        configurazione
    )


    # --------------------------------------------------------
    # 2-4. EMBEDDINGS STANDARD
    # --------------------------------------------------------

    pred_standard = predizioni_embeddings(
        matrice,
        schema_mimic,
        schema_omop,
        soglia
    )


    aggiungi_risultato(
        risultati,
        metodo="Embeddings",
        configurazione=configurazione,
        soglia=soglia,
        predizioni=pred_standard,
        ground_truth=ground_truth,
        note="Baseline embeddings senza filtro"
    )


    aggiungi_casi_embeddings(
        casi,
        "Embeddings",
        configurazione,
        matrice,
        schema_mimic,
        schema_omop,
        pred_standard,
        ground_truth
    )


    metriche = calcola_metriche(
        pred_standard,
        ground_truth
    )


    print()
    print(
        "EMBEDDINGS STANDARD"
    )

    print(
        "TP:",
        metriche["tp"],
        "| FP:",
        metriche["fp"],
        "| FN:",
        metriche["fn"]
    )

    print(
        "Precision:",
        round(
            metriche["precision"],
            4
        ),

        "| Recall:",
        round(
            metriche["recall"],
            4
        ),

        "| F1:",
        round(
            metriche["f1"],
            4
        )
    )


    # --------------------------------------------------------
    # 5. EMBEDDINGS + FILTRO TIPO ESATTO
    # --------------------------------------------------------

    pred_tipo = (
        predizioni_embeddings_tipo_esatto(
            matrice,
            schema_mimic,
            schema_omop,
            soglia
        )
    )


    aggiungi_risultato(
        risultati,
        metodo="Embeddings+filtro_tipo",
        configurazione=configurazione,
        soglia=soglia,
        predizioni=pred_tipo,
        ground_truth=ground_truth,
        note="Uguaglianza esatta del tipo"
    )


    aggiungi_casi_embeddings(
        casi,
        "Embeddings+filtro_tipo",
        configurazione,
        matrice,
        schema_mimic,
        schema_omop,
        pred_tipo,
        ground_truth
    )


    metriche = calcola_metriche(
        pred_tipo,
        ground_truth
    )


    print()
    print(
        "EMBEDDINGS + FILTRO TIPO"
    )

    print(
        "TP:",
        metriche["tp"],
        "| FP:",
        metriche["fp"],
        "| FN:",
        metriche["fn"],
        "| F1:",
        round(
            metriche["f1"],
            4
        )
    )


    # --------------------------------------------------------
    # 6. EMBEDDINGS + MATCH RECIPROCO
    # --------------------------------------------------------

    pred_reciproco = (
        predizioni_match_reciproco(
            matrice,
            schema_mimic,
            schema_omop,
            soglia
        )
    )


    aggiungi_risultato(
        risultati,
        metodo="Embeddings+match_reciproco",
        configurazione=configurazione,
        soglia=soglia,
        predizioni=pred_reciproco,
        ground_truth=ground_truth,
        note="Miglior candidato reciproco"
    )


    aggiungi_casi_embeddings(
        casi,
        "Embeddings+match_reciproco",
        configurazione,
        matrice,
        schema_mimic,
        schema_omop,
        pred_reciproco,
        ground_truth
    )


    metriche = calcola_metriche(
        pred_reciproco,
        ground_truth
    )


    print()
    print(
        "EMBEDDINGS + MATCH RECIPROCO"
    )

    print(
        "TP:",
        metriche["tp"],
        "| FP:",
        metriche["fp"],
        "| FN:",
        metriche["fn"],
        "| F1:",
        round(
            metriche["f1"],
            4
        )
    )


    # --------------------------------------------------------
    # 7. NUOVA ESTENSIONE:
    # FAMIGLIE DI TIPI
    # --------------------------------------------------------

    pred_famiglie = (
        predizioni_embeddings_famiglie_tipo(
            matrice,
            schema_mimic,
            schema_omop,
            soglia
        )
    )


    aggiungi_risultato(
        risultati,
        metodo="Embeddings+famiglie_tipo",
        configurazione=configurazione,
        soglia=soglia,
        predizioni=pred_famiglie,
        ground_truth=ground_truth,
        note="Compatibilita tra famiglie di tipi"
    )


    aggiungi_casi_embeddings(
        casi,
        "Embeddings+famiglie_tipo",
        configurazione,
        matrice,
        schema_mimic,
        schema_omop,
        pred_famiglie,
        ground_truth
    )


    metriche = calcola_metriche(
        pred_famiglie,
        ground_truth
    )


    print()
    print(
        "EMBEDDINGS + FAMIGLIE DI TIPI"
    )

    print(
        "TP:",
        metriche["tp"],
        "| FP:",
        metriche["fp"],
        "| FN:",
        metriche["fn"],
        "| F1:",
        round(
            metriche["f1"],
            4
        )
    )


# ============================================================
# SALVATAGGIO
# ============================================================

salva_risultati(
    risultati
)

salva_casi(
    casi
)


print()
print(
    "====================================="
)

print(
    "VALIDAZIONE COMPLETATA"
)

print(
    "====================================="
)

print()

print(
    "Risultati salvati in:"
)

print(
    "risultati_validazione_mimic_omop.csv"
)

print()

print(
    "Casi per analisi salvati in:"
)

print(
    "casi_validazione_mimic_omop.csv"
)

print()

print(
    "Controllo mapping salvato in:"
)

print(
    "mapping_non_risolti.csv"
)