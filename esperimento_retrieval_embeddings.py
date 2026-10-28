import csv

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
# MODELLO
# ============================================================

NOME_MODELLO = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# Tolleranza utilizzata per le parità
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


def crea_id(tabella, colonna):

    return (
        pulisci(tabella).upper()
        + "."
        + pulisci(colonna).upper()
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

        lettore = csv.DictReader(file)


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


            # Ignoriamo righe che non rappresentano
            # attributi validi.

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
                    tipo
            })


    return attributi


# ============================================================
# LETTURA MAPPING
# ============================================================

def leggi_mapping(nome_file):

    righe = []


    with open(
        nome_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        lettore = csv.DictReader(file)


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


            righe.append({

                "src_id":
                    crea_id(
                        src_ent,
                        src_att
                    ),

                "tgt_ent":
                    tgt_ent,

                "tgt_att":
                    tgt_att
            })


    return righe


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

            mapping_non_risolti.append(
                (
                    src_id,
                    tgt_id
                )
            )

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
# CREAZIONE TESTI
# ============================================================

def crea_testo(
    attributo,
    configurazione
):

    nome = normalizza_nome(
        attributo["nome"]
    )

    tabella = normalizza_nome(
        attributo["tabella"]
    )

    descrizione = pulisci(
        attributo["descrizione"]
    )


    # --------------------------------------------------------
    # SOLO NOME
    # --------------------------------------------------------

    if configurazione == "solo_nome":

        return nome


    # --------------------------------------------------------
    # SOLA DESCRIZIONE
    # --------------------------------------------------------

    if configurazione == "sola_descrizione":

        return descrizione


    # --------------------------------------------------------
    # NOME + DESCRIZIONE
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # CONTESTO TABELLA
    # --------------------------------------------------------

    if configurazione == "contesto_tabella":

        if descrizione == "":

            return (
                "Table: "
                +
                tabella
                +
                ". Column: "
                +
                nome
            )

        return (
            "Table: "
            +
            tabella
            +
            ". Column: "
            +
            nome
            +
            ". Description: "
            +
            descrizione
        )


    raise ValueError(
        "Configurazione non valida"
    )


# ============================================================
# VALIDITA' DEL CANDIDATO
# ============================================================

def candidato_valido(
    attributo_source,
    attributo_target,
    configurazione
):

    """
    Solo per 'sola_descrizione':

    - la descrizione source deve esistere;
    - la descrizione target deve esistere.

    Per le altre configurazioni tutti gli
    attributi sono candidati validi.
    """

    if configurazione != "sola_descrizione":

        return True


    descrizione_source = pulisci(
        attributo_source["descrizione"]
    )

    descrizione_target = pulisci(
        attributo_target["descrizione"]
    )


    return (
        descrizione_source != ""
        and
        descrizione_target != ""
    )


# ============================================================
# CALCOLO EMBEDDINGS
# ============================================================

def calcola_matrice(
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


    return util.cos_sim(
        embeddings_mimic,
        embeddings_omop
    )


# ============================================================
# COSTRUZIONE DEL RANKING
# ============================================================

def ranking_source(
    matrice,
    indice_source,
    attributo_source,
    schema_omop,
    configurazione
):

    candidati = []


    for j, attributo_target in enumerate(
        schema_omop
    ):

        if not candidato_valido(
            attributo_source,
            attributo_target,
            configurazione
        ):
            continue


        score = (
            matrice[indice_source][j]
            .item()
        )


        candidati.append({

            "indice_target":
                j,

            "target_id":
                attributo_target["id"],

            "score":
                score
        })


    # Ordine dal punteggio maggiore
    # al punteggio minore.

    candidati.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    # --------------------------------------------------------
    # RANGO CON GESTIONE DELLE PARITA'
    # --------------------------------------------------------

    for candidato in candidati:

        score_candidato = candidato[
            "score"
        ]


        # Il rango non dipende dalla posizione
        # fisica nel CSV.
        #
        # Conta quanti candidati hanno uno score
        # realmente superiore.

        quanti_superiori = sum(

            1

            for altro in candidati

            if (
                altro["score"]
                >
                score_candidato
                +
                TOLLERANZA_PARITA
            )
        )


        candidato["rango"] = (
            quanti_superiori
            +
            1
        )


    return candidati


# ============================================================
# PROGRAMMA PRINCIPALE
# ============================================================

print()

print(
    "ESPERIMENTO ESPLORATIVO "
    "RETRIEVAL EMBEDDINGS"
)

print(
    "============================================"
)

print()


# ============================================================
# LETTURA DATI
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


schema_mimic = [

    attributo

    for attributo
    in schema_mimic_completo

    if attributo["id"]
    in sorgenti_annotate
]


print(
    "Attributi MIMIC valutati:",
    len(schema_mimic)
)

print(
    "Attributi OMOP:",
    len(schema_omop)
)

print(
    "Ground truth positiva:",
    len(ground_truth)
)

print(
    "Mapping non risolti:",
    len(mapping_non_risolti)
)


# ============================================================
# INDICI
# ============================================================

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


# ============================================================
# CONTROLLO 54 CORRISPONDENZE CON DESCRIZIONE MANCANTE
# ============================================================

gt_descrizione_mancante = 0


for src_id, tgt_id in ground_truth:

    source = diz_mimic[
        src_id
    ]

    target = diz_omop[
        tgt_id
    ]


    if (
        pulisci(
            source["descrizione"]
        )
        ==
        ""
        or
        pulisci(
            target["descrizione"]
        )
        ==
        ""
    ):

        gt_descrizione_mancante += 1


print()

print(
    "GT con almeno una descrizione mancante:",
    gt_descrizione_mancante
)

print(
    "GT teoricamente valutabili con sola descrizione:",
    len(ground_truth)
    -
    gt_descrizione_mancante
)


# ============================================================
# CARICAMENTO MODELLO
# ============================================================

print()

print(
    "Caricamento modello..."
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

    "nome_descrizione",

    "contesto_tabella"
]


risultati = []

righe_ranghi = []

righe_top10 = []


# ============================================================
# ESPERIMENTO
# ============================================================

for configurazione in configurazioni:

    print()

    print(
        "============================================"
    )

    print(
        "CONFIGURAZIONE:",
        configurazione
    )

    print(
        "============================================"
    )


    matrice = calcola_matrice(

        modello,

        schema_mimic,

        schema_omop,

        configurazione
    )


    # Salviamo i ranking per ogni source
    ranking_per_source = {}


    for i, source in enumerate(
        schema_mimic
    ):

        ranking = ranking_source(

            matrice,

            i,

            source,

            schema_omop,

            configurazione
        )


        ranking_per_source[
            source["id"]
        ] = ranking


        # ----------------------------------------------------
        # TOP-10
        # ----------------------------------------------------
        #
        # Manteniamo tutti i candidati con rango <= 10.
        # In presenza di parità potrebbero quindi esserci
        # più di 10 righe.

        for candidato in ranking:

            if candidato["rango"] > 10:
                continue


            target = schema_omop[
                candidato["indice_target"]
            ]


            righe_top10.append({

                "configurazione":
                    configurazione,

                "sorgente":
                    source["id"],

                "target":
                    target["id"],

                "rango":
                    candidato["rango"],

                "similarita":
                    round(
                        candidato["score"],
                        6
                    ),

                "ground_truth":
                    (
                        1
                        if (
                            source["id"],
                            target["id"]
                        )
                        in ground_truth
                        else 0
                    )
            })


    # ========================================================
    # VALUTAZIONE GROUND TRUTH
    # ========================================================

    recuperate_1 = 0

    recuperate_5 = 0

    recuperate_10 = 0


    for src_id, tgt_id in sorted(
        ground_truth
    ):

        source = diz_mimic[
            src_id
        ]

        target = diz_omop[
            tgt_id
        ]


        source_desc_mancante = (

            pulisci(
                source["descrizione"]
            )
            ==
            ""
        )


        target_desc_mancante = (

            pulisci(
                target["descrizione"]
            )
            ==
            ""
        )


        ranking = ranking_per_source[
            src_id
        ]


        candidato_corretto = None


        for candidato in ranking:

            if (
                candidato["target_id"]
                ==
                tgt_id
            ):

                candidato_corretto = (
                    candidato
                )

                break


        # ----------------------------------------------------
        # TARGET NON VALUTABILE
        # ----------------------------------------------------

        if candidato_corretto is None:

            rango = ""

            similarita = ""

            recuperata_1 = 0

            recuperata_5 = 0

            recuperata_10 = 0


        # ----------------------------------------------------
        # TARGET PRESENTE NEL RANKING
        # ----------------------------------------------------

        else:

            rango = candidato_corretto[
                "rango"
            ]

            similarita = round(
                candidato_corretto["score"],
                6
            )


            recuperata_1 = (
                1
                if rango <= 1
                else 0
            )

            recuperata_5 = (
                1
                if rango <= 5
                else 0
            )

            recuperata_10 = (
                1
                if rango <= 10
                else 0
            )


        recuperate_1 += (
            recuperata_1
        )

        recuperate_5 += (
            recuperata_5
        )

        recuperate_10 += (
            recuperata_10
        )


        righe_ranghi.append({

            "configurazione":
                configurazione,

            "sorgente":
                src_id,

            "target_corretto":
                tgt_id,

            "rango":
                rango,

            "similarita":
                similarita,

            "recuperata_at_1":
                recuperata_1,

            "recuperata_at_5":
                recuperata_5,

            "recuperata_at_10":
                recuperata_10,

            "descrizione_sorgente_mancante":
                (
                    "SI"
                    if source_desc_mancante
                    else "NO"
                ),

            "descrizione_target_mancante":
                (
                    "SI"
                    if target_desc_mancante
                    else "NO"
                )
        })


    totale_gt = len(
        ground_truth
    )


    recall_1 = (
        recuperate_1
        /
        totale_gt
    )


    recall_5 = (
        recuperate_5
        /
        totale_gt
    )


    recall_10 = (
        recuperate_10
        /
        totale_gt
    )


    risultati.append({

        "configurazione":
            configurazione,

        "totale_ground_truth":
            totale_gt,

        "recuperate_at_1":
            recuperate_1,

        "recall_at_1":
            round(
                recall_1,
                4
            ),

        "recuperate_at_5":
            recuperate_5,

        "recall_at_5":
            round(
                recall_5,
                4
            ),

        "recuperate_at_10":
            recuperate_10,

        "recall_at_10":
            round(
                recall_10,
                4
            )
    })


    print()

    print(
        "Recall@1:",
        round(
            recall_1,
            4
        ),
        "(",
        recuperate_1,
        "/",
        totale_gt,
        ")"
    )


    print(
        "Recall@5:",
        round(
            recall_5,
            4
        ),
        "(",
        recuperate_5,
        "/",
        totale_gt,
        ")"
    )


    print(
        "Recall@10:",
        round(
            recall_10,
            4
        ),
        "(",
        recuperate_10,
        "/",
        totale_gt,
        ")"
    )


# ============================================================
# SALVATAGGIO RISULTATI
# ============================================================

with open(
    "risultati_retrieval_embeddings.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [

        "configurazione",

        "totale_ground_truth",

        "recuperate_at_1",

        "recall_at_1",

        "recuperate_at_5",

        "recall_at_5",

        "recuperate_at_10",

        "recall_at_10"
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


# ============================================================
# SALVATAGGIO RANGHI DELLE GT
# ============================================================

with open(
    "ranghi_ground_truth_retrieval.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [

        "configurazione",

        "sorgente",

        "target_corretto",

        "rango",

        "similarita",

        "recuperata_at_1",

        "recuperata_at_5",

        "recuperata_at_10",

        "descrizione_sorgente_mancante",

        "descrizione_target_mancante"
    ]


    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )


    scrittore.writeheader()


    for riga in righe_ranghi:

        scrittore.writerow(
            riga
        )


# ============================================================
# SALVATAGGIO TOP-10
# ============================================================

with open(
    "top10_retrieval_embeddings.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    colonne = [

        "configurazione",

        "sorgente",

        "target",

        "rango",

        "similarita",

        "ground_truth"
    ]


    scrittore = csv.DictWriter(
        file,
        fieldnames=colonne
    )


    scrittore.writeheader()


    for riga in righe_top10:

        scrittore.writerow(
            riga
        )


# ============================================================
# FINE
# ============================================================

print()

print(
    "============================================"
)

print(
    "ESPERIMENTO COMPLETATO"
)

print(
    "============================================"
)

print()

print(
    "File creati:"
)

print(
    "- risultati_retrieval_embeddings.csv"
)

print(
    "- ranghi_ground_truth_retrieval.csv"
)

print(
    "- top10_retrieval_embeddings.csv"
)