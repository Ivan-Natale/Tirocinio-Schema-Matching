import csv
from collections import defaultdict

from sentence_transformers import SentenceTransformer, util


# ============================================================
# FILE
# ============================================================

FILE_MIMIC = (
    "data_validation/"
    "MIMIC_III_Schema.csv"
)

FILE_OMOP = (
    "data_validation/"
    "OMOP_Schema.csv"
)

FILE_MAPPING = (
    "data_validation/"
    "MIMIC_to_OMOP_Mapping.csv"
)


# ============================================================
# MODELLO E PARAMETRI FISSATI PRIMA DELLA VALIDAZIONE
# ============================================================

NOME_MODELLO = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


SOGLIA_LEVENSHTEIN = 0.33


SOGLIE_EMBEDDINGS = {

    "solo_nome": 0.80,

    "sola_descrizione": 0.65,

    "nome_descrizione": 0.75
}


# Tolleranza usata nella gestione
# delle parità del match reciproco.

TOLLERANZA_PARITA = 1e-7


# ============================================================
# FUNZIONI DI BASE
# ============================================================

def pulisci(testo):

    if testo is None:
        return ""

    return str(testo).strip()


def normalizza_nome(nome):

    return (
        pulisci(nome)
        .replace("_", " ")
        .lower()
    )


def normalizza_tipo_esatto(tipo):

    return (
        pulisci(tipo)
        .upper()
        .replace(" ", "")
    )


def crea_id(
    tabella,
    colonna
):

    return (
        pulisci(tabella).upper()
        + "."
        + pulisci(colonna).upper()
    )


# ============================================================
# FAMIGLIE DI TIPI
# ============================================================

def famiglia_tipo(tipo):

    tipo = (
        pulisci(tipo)
        .lower()
        .strip()
    )

    if "(" in tipo:

        tipo_base = (
            tipo
            .split("(")[0]
            .strip()
        )

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


    return (
        "ALTRO:"
        +
        tipo_base.upper()
    )


# ============================================================
# LETTURA SCHEMA
# ============================================================

def leggi_schema(nome_file):

    attributi = []


    with open(
        nome_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:


        lettore = csv.DictReader(
            file
        )


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


            tabella = pulisci(
                riga["TableName"]
            )


            nome = pulisci(
                riga["ColumnName"]
            )


            descrizione = pulisci(
                riga["ColumnDesc"]
            )


            tipo = pulisci(
                riga["ColumnType"]
            )


            # Stessa regola usata nel censimento:
            # righe prive di tabella o nome colonna
            # non vengono considerate attributi.

            if (
                tabella == ""
                or
                nome == ""
            ):

                continue


            attributi.append({

                "id":
                    crea_id(
                        tabella,
                        nome
                    ),

                "tabella":
                    tabella,

                "nome":
                    nome,

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
# LETTURA MAPPING
# ============================================================

def leggi_mapping(nome_file):

    righe_mapping = []


    with open(
        nome_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:


        lettore = csv.DictReader(
            file
        )


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


            src_ent = pulisci(
                riga["SRC_ENT"]
            )


            src_att = pulisci(
                riga["SRC_ATT"]
            )


            tgt_ent = pulisci(
                riga["TGT_ENT"]
            )


            tgt_att = pulisci(
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
# GROUND TRUTH
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


        src_id = riga[
            "src_id"
        ]


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


        # Se il benchmark dichiara
        # che non esiste un target,
        # non aggiungiamo una GT positiva.

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
# CENSIMENTO DESCRIZIONI
# ============================================================

def analizza_descrizioni(
    schema,
    nome_dataset
):

    mancanti = []

    gruppi = defaultdict(
        list
    )


    for attributo in schema:


        descrizione = pulisci(
            attributo["descrizione"]
        )


        if descrizione == "":

            mancanti.append(
                attributo["id"]
            )

        else:

            # Normalizzazione minima
            # per il censimento dei duplicati.

            chiave = (
                descrizione
                .strip()
                .lower()
            )


            gruppi[
                chiave
            ].append(
                attributo["id"]
            )


    duplicati = {

        descrizione:
            attributi

        for descrizione, attributi
        in gruppi.items()

        if len(attributi) > 1
    }


    colonne_duplicate = sum(

        len(attributi)

        for attributi
        in duplicati.values()
    )


    riepilogo = {

        "dataset":
            nome_dataset,

        "totale_colonne":
            len(schema),

        "descrizioni_mancanti":
            len(mancanti),

        "descrizioni_presenti":
            len(schema)
            -
            len(mancanti),

        "gruppi_descrizioni_duplicate":
            len(duplicati),

        "colonne_coinvolte_in_duplicati":
            colonne_duplicate
    }


    return (
        riepilogo,
        mancanti,
        duplicati
    )


def salva_censimento_descrizioni(
    riepiloghi,
    mancanti_mimic,
    mancanti_omop,
    duplicati_mimic,
    duplicati_omop
):


    # --------------------------------------------------------
    # RIEPILOGO
    # --------------------------------------------------------

    with open(
        "censimento_descrizioni.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:


        colonne = [

            "dataset",
            "totale_colonne",
            "descrizioni_mancanti",
            "descrizioni_presenti",
            "gruppi_descrizioni_duplicate",
            "colonne_coinvolte_in_duplicati"
        ]


        scrittore = csv.DictWriter(
            file,
            fieldnames=colonne
        )


        scrittore.writeheader()


        for riga in riepiloghi:

            scrittore.writerow(
                riga
            )


    # --------------------------------------------------------
    # MANCANTI
    # --------------------------------------------------------

    with open(
        "descrizioni_mancanti.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:


        scrittore = csv.writer(
            file
        )


        scrittore.writerow([
            "dataset",
            "attributo"
        ])


        for attributo in mancanti_mimic:

            scrittore.writerow([
                "MIMIC",
                attributo
            ])


        for attributo in mancanti_omop:

            scrittore.writerow([
                "OMOP",
                attributo
            ])


    # --------------------------------------------------------
    # DUPLICATI
    # --------------------------------------------------------

    with open(
        "descrizioni_duplicate.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:


        scrittore = csv.writer(
            file
        )


        scrittore.writerow([

            "dataset",
            "descrizione",
            "numero_occorrenze",
            "attributi"
        ])


        for descrizione, attributi in (
            duplicati_mimic.items()
        ):

            scrittore.writerow([

                "MIMIC",

                descrizione,

                len(attributi),

                " | ".join(
                    attributi
                )
            ])


        for descrizione, attributi in (
            duplicati_omop.items()
        ):

            scrittore.writerow([

                "OMOP",

                descrizione,

                len(attributi),

                " | ".join(
                    attributi
                )
            ])


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


    descrizione = pulisci(
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
            +
            ". "
            +
            descrizione
        )


    raise ValueError(
        "Configurazione embeddings non valida"
    )


# ============================================================
# CONTROLLO DESCRIZIONI MANCANTI
# ============================================================

def coppia_valida_per_configurazione(
    attributo_a,
    attributo_b,
    configurazione
):

    """
    Nella configurazione sola_descrizione
    una coppia viene valutata soltanto se
    entrambe le descrizioni sono presenti.

    IMPORTANTE:
    la ground truth non viene modificata.

    Se una corrispondenza corretta ha una
    descrizione mancante, il metodo non può
    predirla e quindi rimane un falso negativo.
    Questo mantiene corretto il calcolo del recall.
    """


    if configurazione != "sola_descrizione":

        return True


    descrizione_a = pulisci(
        attributo_a["descrizione"]
    )


    descrizione_b = pulisci(
        attributo_b["descrizione"]
    )


    if descrizione_a == "":

        return False


    if descrizione_b == "":

        return False


    return True


# ============================================================
# LEVENSHTEIN
# ============================================================

def distanza_levenshtein(
    stringa_a,
    stringa_b
):


    if stringa_a == stringa_b:

        return 0


    if len(stringa_a) == 0:

        return len(
            stringa_b
        )


    if len(stringa_b) == 0:

        return len(
            stringa_a
        )


    if len(stringa_a) < len(stringa_b):

        stringa_a, stringa_b = (
            stringa_b,
            stringa_a
        )


    riga_precedente = list(
        range(
            len(stringa_b)
            +
            1
        )
    )


    for i, carattere_a in enumerate(
        stringa_a,
        start=1
    ):


        riga_corrente = [
            i
        ]


        for j, carattere_b in enumerate(
            stringa_b,
            start=1
        ):


            costo_inserimento = (
                riga_corrente[j - 1]
                +
                1
            )


            costo_cancellazione = (
                riga_precedente[j]
                +
                1
            )


            costo_sostituzione = (

                riga_precedente[j - 1]

                +

                (
                    0

                    if carattere_a
                    ==
                    carattere_b

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


    return (
        riga_precedente[-1]
    )


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

        "tp":
            tp,

        "fp":
            fp,

        "fn":
            fn,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1
    }


# ============================================================
# LEVENSHTEIN + FILTRO TIPO ESATTO
# ============================================================

def esegui_levenshtein(
    schema_mimic,
    schema_omop
):


    predizioni = set()


    for attributo_a in schema_mimic:


        nome_a = normalizza_nome(
            attributo_a["nome"]
        )


        for attributo_b in schema_omop:


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


            if score >= SOGLIA_LEVENSHTEIN:


                predizioni.add(
                    (
                        attributo_a["id"],
                        attributo_b["id"]
                    )
                )


    return predizioni


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

        for attributo
        in schema_mimic
    ]


    testi_omop = [

        crea_testo(
            attributo,
            configurazione
        )

        for attributo
        in schema_omop
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


    matrice = util.cos_sim(
        embeddings_mimic,
        embeddings_omop
    )


    return matrice


# ============================================================
# EMBEDDINGS STANDARD
# ============================================================

def predizioni_embeddings(
    matrice,
    schema_mimic,
    schema_omop,
    soglia,
    configurazione
):


    predizioni = set()


    for i, attributo_a in enumerate(
        schema_mimic
    ):


        for j, attributo_b in enumerate(
            schema_omop
        ):


            # CORREZIONE:
            # in sola_descrizione non vengono
            # valutate coppie con almeno una
            # descrizione mancante.

            if not coppia_valida_per_configurazione(
                attributo_a,
                attributo_b,
                configurazione
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
# EMBEDDINGS + FILTRO TIPO ESATTO
# ============================================================

def predizioni_embeddings_tipo_esatto(
    matrice,
    schema_mimic,
    schema_omop,
    soglia,
    configurazione
):


    predizioni = set()


    for i, attributo_a in enumerate(
        schema_mimic
    ):


        for j, attributo_b in enumerate(
            schema_omop
        ):


            if not coppia_valida_per_configurazione(
                attributo_a,
                attributo_b,
                configurazione
            ):

                continue


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
# EMBEDDINGS + FAMIGLIE DI TIPI
# ============================================================

def predizioni_embeddings_famiglie_tipo(
    matrice,
    schema_mimic,
    schema_omop,
    soglia,
    configurazione
):


    predizioni = set()


    for i, attributo_a in enumerate(
        schema_mimic
    ):


        for j, attributo_b in enumerate(
            schema_omop
        ):


            if not coppia_valida_per_configurazione(
                attributo_a,
                attributo_b,
                configurazione
            ):

                continue


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
# MATCH RECIPROCO
# ============================================================

def predizioni_match_reciproco(
    matrice,
    schema_mimic,
    schema_omop,
    soglia,
    configurazione
):

    """
    Un match viene accettato se:

    1. supera la soglia;
    2. il target è tra i migliori candidati
       della sorgente;
    3. la sorgente è tra i migliori candidati
       del target.

    GESTIONE DELLE PARITA':

    se più candidati hanno lo stesso score massimo
    entro una tolleranza di 1e-7, vengono mantenuti
    tutti.

    In questo modo l'ordine delle righe del CSV
    non decide arbitrariamente quale candidato
    mantenere.

    LIMITE:

    il match reciproco continua a favorire una
    struttura simile a uno-a-uno.

    Se due attributi sorgente corretti devono
    convergere sullo stesso attributo target,
    ma uno dei due ha score inferiore, il target
    considererà migliore soltanto l'altro.

    Il metodo può quindi perdere corrispondenze
    corrette nei mapping molti-a-uno.
    """


    predizioni = set()

    righe_parita = []


    migliori_target_per_source = {}

    migliori_source_per_target = {}


    # ========================================================
    # MIGLIORI TARGET PER OGNI SOURCE
    # ========================================================

    for i, attributo_a in enumerate(
        schema_mimic
    ):


        candidati = []


        for j, attributo_b in enumerate(
            schema_omop
        ):


            # In sola_descrizione vengono
            # completamente ignorate le coppie
            # con descrizioni mancanti.

            if not coppia_valida_per_configurazione(
                attributo_a,
                attributo_b,
                configurazione
            ):

                continue


            score = (
                matrice[i][j]
                .item()
            )


            candidati.append(
                (
                    j,
                    score
                )
            )


        if len(candidati) == 0:


            migliori_target_per_source[
                i
            ] = []


            continue


        massimo = max(

            score

            for _, score
            in candidati
        )


        migliori = [

            j

            for j, score
            in candidati

            if abs(
                score
                -
                massimo
            )
            <=
            TOLLERANZA_PARITA
        ]


        migliori_target_per_source[
            i
        ] = migliori


        if (
            len(migliori) > 1
            and
            massimo >= soglia
        ):


            righe_parita.append({

                "configurazione":
                    configurazione,

                "lato":
                    "SOURCE_MIMIC",

                "attributo":
                    attributo_a["id"],

                "score_massimo":
                    round(
                        massimo,
                        6
                    ),

                "numero_candidati_pari":
                    len(migliori),

                "candidati":
                    " | ".join(

                        schema_omop[j]["id"]

                        for j
                        in migliori
                    )
            })


    # ========================================================
    # MIGLIORI SOURCE PER OGNI TARGET
    # ========================================================

    for j, attributo_b in enumerate(
        schema_omop
    ):


        candidati = []


        for i, attributo_a in enumerate(
            schema_mimic
        ):


            if not coppia_valida_per_configurazione(
                attributo_a,
                attributo_b,
                configurazione
            ):

                continue


            score = (
                matrice[i][j]
                .item()
            )


            candidati.append(
                (
                    i,
                    score
                )
            )


        if len(candidati) == 0:


            migliori_source_per_target[
                j
            ] = []


            continue


        massimo = max(

            score

            for _, score
            in candidati
        )


        migliori = [

            i

            for i, score
            in candidati

            if abs(
                score
                -
                massimo
            )
            <=
            TOLLERANZA_PARITA
        ]


        migliori_source_per_target[
            j
        ] = migliori


        if (
            len(migliori) > 1
            and
            massimo >= soglia
        ):


            righe_parita.append({

                "configurazione":
                    configurazione,

                "lato":
                    "TARGET_OMOP",

                "attributo":
                    attributo_b["id"],

                "score_massimo":
                    round(
                        massimo,
                        6
                    ),

                "numero_candidati_pari":
                    len(migliori),

                "candidati":
                    " | ".join(

                        schema_mimic[i]["id"]

                        for i
                        in migliori
                    )
            })


    # ========================================================
    # CONTROLLO RECIPROCITA'
    # ========================================================

    for i, attributo_a in enumerate(
        schema_mimic
    ):


        for j in migliori_target_per_source[
            i
        ]:


            score = (
                matrice[i][j]
                .item()
            )


            if score < soglia:

                continue


            if (
                i
                in
                migliori_source_per_target[
                    j
                ]
            ):


                predizioni.add(
                    (
                        attributo_a["id"],
                        schema_omop[j]["id"]
                    )
                )


    return (
        predizioni,
        righe_parita
    )


# ============================================================
# AGGIUNTA RISULTATI
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
# DETTAGLI CASI
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

        attributo["id"]:
            i

        for i, attributo
        in enumerate(
            schema_mimic
        )
    }


    indice_omop = {

        attributo["id"]:
            j

        for j, attributo
        in enumerate(
            schema_omop
        )
    }


    unione = (
        predizioni
        |
        ground_truth
    )


    righe_tp = []

    righe_fn = []

    righe_fp = []


    for src_id, tgt_id in unione:


        if (
            src_id not in indice_mimic
            or
            tgt_id not in indice_omop
        ):

            continue


        i = indice_mimic[
            src_id
        ]


        j = indice_omop[
            tgt_id
        ]


        attributo_a = (
            schema_mimic[i]
        )


        attributo_b = (
            schema_omop[j]
        )


        valida = (
            coppia_valida_per_configurazione(
                attributo_a,
                attributo_b,
                configurazione
            )
        )


        predetta = (
            (
                src_id,
                tgt_id
            )
            in predizioni
        )


        corretta = (
            (
                src_id,
                tgt_id
            )
            in ground_truth
        )


        if (
            predetta
            and
            corretta
        ):

            esito = "TP"


        elif predetta:

            esito = "FP"


        else:

            esito = "FN"


        # Per sola_descrizione non mostriamo
        # un punteggio ottenuto da una coppia
        # non valida.

        if (
            configurazione
            ==
            "sola_descrizione"
            and
            not valida
        ):


            score = ""

            motivo_non_valida = (
                "descrizione_mancante"
            )


        else:


            score = round(
                matrice[i][j].item(),
                4
            )


            motivo_non_valida = ""


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
                score,

            "descrizione_sorgente_mancante":
                (
                    "SI"
                    if
                    pulisci(
                        attributo_a[
                            "descrizione"
                        ]
                    )
                    ==
                    ""
                    else
                    "NO"
                ),

            "descrizione_target_mancante":
                (
                    "SI"
                    if
                    pulisci(
                        attributo_b[
                            "descrizione"
                        ]
                    )
                    ==
                    ""
                    else
                    "NO"
                ),

            "coppia_valida_configurazione":
                (
                    "SI"
                    if valida
                    else
                    "NO"
                ),

            "motivo_non_valida":
                motivo_non_valida,

            "tipo_sorgente":
                attributo_a["tipo"],

            "tipo_target":
                attributo_b["tipo"],

            "famiglia_sorgente":
                attributo_a[
                    "famiglia_tipo"
                ],

            "famiglia_target":
                attributo_b[
                    "famiglia_tipo"
                ],

            "esito":
                esito
        }


        if esito == "TP":

            righe_tp.append(
                riga
            )


        elif esito == "FN":

            righe_fn.append(
                riga
            )


        else:

            righe_fp.append(
                riga
            )


    # Ordiniamo i falsi positivi
    # dal punteggio più alto.

    def chiave_fp(riga):

        if riga["score"] == "":

            return -1.0

        return float(
            riga["score"]
        )


    righe_fp.sort(
        key=chiave_fp,
        reverse=True
    )


    casi.extend(
        righe_tp
    )


    casi.extend(
        righe_fn
    )


    casi.extend(
        righe_fp[
            :massimo_fp
        ]
    )


# ============================================================
# GROUND TRUTH DETTAGLIATA
# ============================================================

def salva_ground_truth_dettagli(
    ground_truth,
    schema_mimic,
    schema_omop
):


    diz_mimic = {

        attributo["id"]:
            attributo

        for attributo
        in schema_mimic
    }


    diz_omop = {

        attributo["id"]:
            attributo

        for attributo
        in schema_omop
    }


    with open(
        "ground_truth_dettagli.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:


        colonne = [

            "sorgente",

            "nome_sorgente",

            "descrizione_sorgente",

            "tipo_sorgente",

            "target",

            "nome_target",

            "descrizione_target",

            "tipo_target"
        ]


        scrittore = csv.DictWriter(
            file,
            fieldnames=colonne
        )


        scrittore.writeheader()


        for src_id, tgt_id in sorted(
            ground_truth
        ):


            sorgente = (
                diz_mimic[
                    src_id
                ]
            )


            target = (
                diz_omop[
                    tgt_id
                ]
            )


            scrittore.writerow({

                "sorgente":
                    src_id,

                "nome_sorgente":
                    sorgente["nome"],

                "descrizione_sorgente":
                    sorgente["descrizione"],

                "tipo_sorgente":
                    sorgente["tipo"],

                "target":
                    tgt_id,

                "nome_target":
                    target["nome"],

                "descrizione_target":
                    target["descrizione"],

                "tipo_target":
                    target["tipo"]
            })


# ============================================================
# SALVATAGGIO RISULTATI
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

            scrittore.writerow(
                riga
            )


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

            "descrizione_sorgente_mancante",

            "descrizione_target_mancante",

            "coppia_valida_configurazione",

            "motivo_non_valida",

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

            scrittore.writerow(
                riga
            )


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

            scrittore.writerow(
                riga
            )


def salva_parita(
    righe_parita
):


    with open(
        "parita_match_reciproco.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:


        colonne = [

            "configurazione",
            "lato",
            "attributo",
            "score_massimo",
            "numero_candidati_pari",
            "candidati"
        ]


        scrittore = csv.DictWriter(
            file,
            fieldnames=colonne
        )


        scrittore.writeheader()


        for riga in righe_parita:

            scrittore.writerow(
                riga
            )


# ============================================================
# PROGRAMMA PRINCIPALE
# ============================================================

print()

print(
    "VALIDAZIONE ESTERNA CORRETTA "
    "MIMIC-III -> OMOP"
)

print(
    "============================================"
)

print()


# ============================================================
# LETTURA
# ============================================================

schema_mimic_completo = (
    leggi_schema(
        FILE_MIMIC
    )
)


schema_omop = (
    leggi_schema(
        FILE_OMOP
    )
)


righe_mapping = (
    leggi_mapping(
        FILE_MAPPING
    )
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


# Consideriamo solo le colonne MIMIC
# effettivamente annotate nel benchmark.

schema_mimic = [

    attributo

    for attributo
    in schema_mimic_completo

    if attributo["id"]
    in sorgenti_annotate
]


# ============================================================
# CENSIMENTO
# ============================================================

(
    riepilogo_mimic,
    mancanti_mimic,
    duplicati_mimic

) = analizza_descrizioni(

    schema_mimic,
    "MIMIC"
)


(
    riepilogo_omop,
    mancanti_omop,
    duplicati_omop

) = analizza_descrizioni(

    schema_omop,
    "OMOP"
)


salva_censimento_descrizioni(

    [
        riepilogo_mimic,
        riepilogo_omop
    ],

    mancanti_mimic,

    mancanti_omop,

    duplicati_mimic,

    duplicati_omop
)


print(
    "Attributi MIMIC completi:",
    len(schema_mimic_completo)
)


print(
    "Attributi MIMIC valutati:",
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


print()


print(
    "Descrizioni mancanti MIMIC:",
    len(mancanti_mimic)
)


print(
    "Descrizioni mancanti OMOP:",
    len(mancanti_omop)
)


print(
    "Gruppi descrizioni duplicate MIMIC:",
    len(duplicati_mimic)
)


print(
    "Gruppi descrizioni duplicate OMOP:",
    len(duplicati_omop)
)


# ============================================================
# FILE DI CONTROLLO
# ============================================================

salva_mapping_non_risolti(
    mapping_non_risolti
)


salva_ground_truth_dettagli(
    ground_truth,
    schema_mimic,
    schema_omop
)


if len(mapping_non_risolti) > 0:

    print()

    print(
        "ATTENZIONE: presenti mapping non risolti."
    )

    print(
        "Controllare mapping_non_risolti.csv."
    )


# ============================================================
# RISULTATI
# ============================================================

risultati = []

casi = []

tutte_parita = []


# ============================================================
# 1. LEVENSHTEIN
# ============================================================

print()

print(
    "1. Levenshtein + filtro tipo..."
)


pred_levenshtein = (
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

    note=(
        "Filtro tipo con uguaglianza esatta"
    )
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
# MODELLO EMBEDDINGS
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
# CONFIGURAZIONI
# ============================================================

configurazioni = [

    "solo_nome",

    "sola_descrizione",

    "nome_descrizione"
]


for configurazione in configurazioni:


    soglia = (
        SOGLIE_EMBEDDINGS[
            configurazione
        ]
    )


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


    matrice = (
        calcola_matrice_embeddings(

            modello,

            schema_mimic,

            schema_omop,

            configurazione
        )
    )


    # ========================================================
    # STANDARD
    # ========================================================

    pred_standard = (
        predizioni_embeddings(

            matrice,

            schema_mimic,

            schema_omop,

            soglia,

            configurazione
        )
    )


    aggiungi_risultato(

        risultati,

        metodo="Embeddings",

        configurazione=
            configurazione,

        soglia=
            soglia,

        predizioni=
            pred_standard,

        ground_truth=
            ground_truth,

        note=(
            "In sola_descrizione le coppie "
            "con almeno una descrizione "
            "mancante non producono match; "
            "la ground truth resta invariata."
        )
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


    # ========================================================
    # FILTRO TIPO ESATTO
    # ========================================================

    pred_tipo = (
        predizioni_embeddings_tipo_esatto(

            matrice,

            schema_mimic,

            schema_omop,

            soglia,

            configurazione
        )
    )


    aggiungi_risultato(

        risultati,

        metodo="Embeddings+filtro_tipo",

        configurazione=
            configurazione,

        soglia=
            soglia,

        predizioni=
            pred_tipo,

        ground_truth=
            ground_truth,

        note=(
            "Uguaglianza esatta del tipo"
        )
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


    # ========================================================
    # MATCH RECIPROCO
    # ========================================================

    (
        pred_reciproco,
        righe_parita

    ) = predizioni_match_reciproco(

        matrice,

        schema_mimic,

        schema_omop,

        soglia,

        configurazione
    )


    tutte_parita.extend(
        righe_parita
    )


    aggiungi_risultato(

        risultati,

        metodo=(
            "Embeddings+match_reciproco"
        ),

        configurazione=
            configurazione,

        soglia=
            soglia,

        predizioni=
            pred_reciproco,

        ground_truth=
            ground_truth,

        note=(
            "Tutti i candidati a pari score "
            "massimo sono mantenuti entro "
            "una tolleranza di 1e-7."
        )
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


    # ========================================================
    # FAMIGLIE DI TIPI
    # ========================================================

    pred_famiglie = (
        predizioni_embeddings_famiglie_tipo(

            matrice,

            schema_mimic,

            schema_omop,

            soglia,

            configurazione
        )
    )


    aggiungi_risultato(

        risultati,

        metodo=(
            "Embeddings+famiglie_tipo"
        ),

        configurazione=
            configurazione,

        soglia=
            soglia,

        predizioni=
            pred_famiglie,

        ground_truth=
            ground_truth,

        note=(
            "Compatibilita tra famiglie di tipi"
        )
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
# SALVATAGGIO FINALE
# ============================================================

salva_risultati(
    risultati
)


salva_casi(
    casi
)


salva_parita(
    tutte_parita
)


print()

print(
    "============================================"
)

print(
    "VALIDAZIONE CORRETTA COMPLETATA"
)

print(
    "============================================"
)

print()


print(
    "File prodotti:"
)

print(
    "- censimento_descrizioni.csv"
)

print(
    "- descrizioni_mancanti.csv"
)

print(
    "- descrizioni_duplicate.csv"
)

print(
    "- risultati_validazione_mimic_omop.csv"
)

print(
    "- casi_validazione_mimic_omop.csv"
)

print(
    "- parita_match_reciproco.csv"
)

print(
    "- ground_truth_dettagli.csv"
)

print(
    "- mapping_non_risolti.csv"
)