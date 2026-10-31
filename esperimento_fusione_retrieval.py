import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURAZIONE
# ============================================================

MODELLO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Costante standard usata nella Reciprocal Rank Fusion
RRF_K = 60

FILE_MIMIC = "data_validation/MIMIC_III_Schema.csv"
FILE_OMOP = "data_validation/OMOP_Schema.csv"
FILE_MAPPING = "data_validation/MIMIC_to_OMOP_Mapping.csv"


# ============================================================
# FUNZIONI BASE
# ============================================================

def pulisci(valore):
    if pd.isna(valore):
        return ""

    return str(valore).strip()


def normalizza_nome(nome):
    return pulisci(nome).replace("_", " ").lower()


def crea_id(tabella, colonna):
    return (
        f"{pulisci(tabella).upper()}."
        f"{pulisci(colonna).upper()}"
    )


# ============================================================
# LETTURA SCHEMI
# ============================================================

def leggi_schema(percorso):

    df = pd.read_csv(percorso)

    schema = []

    for _, riga in df.iterrows():

        tabella = pulisci(riga["TableName"])
        colonna = pulisci(riga["ColumnName"])

        # Scartiamo righe senza tabella o colonna
        if tabella == "" or colonna == "":
            continue

        schema.append({
            "id": crea_id(tabella, colonna),
            "tabella": tabella,
            "nome": colonna,
            "descrizione": pulisci(
                riga["ColumnDesc"]
            )
        })

    return schema


# ============================================================
# GROUND TRUTH
# ============================================================

def costruisci_ground_truth(
    mapping,
    mimic_ids,
    omop_ids
):

    ground_truth = []

    sorgenti_annotate = set()

    non_risolti = []

    valori_vuoti = {
        "",
        "NA",
        "N/A",
        "NONE",
        "NULL",
        "0",
        "NAN"
    }

    for _, riga in mapping.iterrows():

        src_ent = pulisci(riga["SRC_ENT"])
        src_att = pulisci(riga["SRC_ATT"])

        tgt_ent = pulisci(riga["TGT_ENT"])
        tgt_att = pulisci(riga["TGT_ATT"])

        if src_ent == "" or src_att == "":
            continue

        src_id = crea_id(
            src_ent,
            src_att
        )

        # Memorizziamo tutte le sorgenti annotate
        if src_id in mimic_ids:
            sorgenti_annotate.add(src_id)

        # Nessun mapping positivo
        if (
            tgt_ent.upper() in valori_vuoti
            or tgt_att.upper() in valori_vuoti
        ):
            continue

        tgt_id = crea_id(
            tgt_ent,
            tgt_att
        )

        # Mapping utilizzabile
        if (
            src_id in mimic_ids
            and tgt_id in omop_ids
        ):

            coppia = (
                src_id,
                tgt_id
            )

            if coppia not in ground_truth:
                ground_truth.append(
                    coppia
                )

        else:

            non_risolti.append(
                (
                    src_id,
                    tgt_id
                )
            )

    return (
        ground_truth,
        sorgenti_annotate,
        non_risolti
    )


# ============================================================
# RAPPRESENTAZIONI TESTUALI
# ============================================================

def crea_testo(
    attributo,
    configurazione
):

    tabella = normalizza_nome(
        attributo["tabella"]
    )

    nome = normalizza_nome(
        attributo["nome"]
    )

    descrizione = pulisci(
        attributo["descrizione"]
    )

    # --------------------------------------------------------
    # 1. NOME + DESCRIZIONE
    # --------------------------------------------------------

    if configurazione == "nome_descrizione":

        if descrizione:
            return (
                f"{nome}. "
                f"{descrizione}"
            )

        return nome

    # --------------------------------------------------------
    # 2. CONTROLLO SENZA TABELLA
    # --------------------------------------------------------
    #
    # Stesso formato del contesto,
    # ma senza TableName.
    #
    # Serve per capire se il miglioramento
    # dipende veramente dal nome della tabella.
    # --------------------------------------------------------

    if configurazione == "senza_contesto":

        if descrizione:

            return (
                f"Column: {nome}. "
                f"Description: {descrizione}"
            )

        return (
            f"Column: {nome}"
        )

    # --------------------------------------------------------
    # 3. CONTESTO DELLA TABELLA
    # --------------------------------------------------------

    if configurazione == "contesto_tabella":

        if descrizione:

            return (
                f"Table: {tabella}. "
                f"Column: {nome}. "
                f"Description: {descrizione}"
            )

        return (
            f"Table: {tabella}. "
            f"Column: {nome}"
        )

    raise ValueError(
        "Configurazione non riconosciuta"
    )


# ============================================================
# RANKING E GESTIONE DELLE PARITA'
# ============================================================

def crea_ranking(
    scores,
    target_ids
):

    indici = list(
        range(len(target_ids))
    )

    # --------------------------------------------------------
    # Gestione delle parita'
    #
    # 1. similarita' maggiore
    # 2. se uguale entro 7 decimali:
    #    identificatore target alfabetico
    #
    # Questo garantisce posizioni uniche:
    # 1, 2, 3, ..., 425
    #
    # Quindi Top-10 contiene realmente
    # massimo 10 candidati.
    # --------------------------------------------------------

    indici.sort(
        key=lambda j: (
            -round(
                float(scores[j]),
                7
            ),
            target_ids[j]
        )
    )

    return indici


# ============================================================
# CALCOLO RECALL@K
# ============================================================

def calcola_recall(
    ranking,
    ground_truth,
    k
):

    trovati = 0

    for src_id, tgt_id in ground_truth:

        primi_k = (
            ranking[src_id][:k]
        )

        if tgt_id in primi_k:
            trovati += 1

    recall = (
        trovati
        / len(ground_truth)
    )

    return (
        trovati,
        recall
    )


# ============================================================
# LETTURA DEI DATI
# ============================================================

mimic = leggi_schema(
    FILE_MIMIC
)

omop = leggi_schema(
    FILE_OMOP
)

mapping = pd.read_csv(
    FILE_MAPPING
)


mimic_ids = {
    a["id"]
    for a in mimic
}

omop_ids = {
    a["id"]
    for a in omop
}


(
    ground_truth,
    sorgenti_annotate,
    non_risolti
) = costruisci_ground_truth(
    mapping,
    mimic_ids,
    omop_ids
)


# Manteniamo solo gli attributi
# MIMIC presenti nelle annotazioni

mimic = [
    a
    for a in mimic
    if a["id"]
    in sorgenti_annotate
]


# Ordinamento deterministico

mimic.sort(
    key=lambda x: x["id"]
)

omop.sort(
    key=lambda x: x["id"]
)


source_ids = [
    a["id"]
    for a in mimic
]

target_ids = [
    a["id"]
    for a in omop
]


target_index = {
    target_id: i
    for i, target_id
    in enumerate(target_ids)
}


print(
    "MIMIC valutati:",
    len(mimic)
)

print(
    "OMOP validi:",
    len(omop)
)

print(
    "Ground truth:",
    len(ground_truth)
)

print(
    "Mapping non risolti:",
    len(non_risolti)
)


# ============================================================
# MODELLO EMBEDDINGS
# ============================================================

model = SentenceTransformer(
    MODELLO
)


configurazioni = [

    "nome_descrizione",

    "contesto_tabella",

    "senza_contesto"
]


similarita = {}


# ============================================================
# CALCOLO EMBEDDINGS
# ============================================================

for configurazione in configurazioni:

    print()

    print(
        "Calcolo:",
        configurazione
    )


    testi_source = [

        crea_testo(
            a,
            configurazione
        )

        for a in mimic
    ]


    testi_target = [

        crea_testo(
            a,
            configurazione
        )

        for a in omop
    ]


    emb_source = model.encode(

        testi_source,

        normalize_embeddings=True,

        show_progress_bar=True
    )


    emb_target = model.encode(

        testi_target,

        normalize_embeddings=True,

        show_progress_bar=True
    )


    # Con embedding normalizzati,
    # prodotto scalare = cosine similarity

    similarita[
        configurazione
    ] = np.matmul(

        emb_source,

        emb_target.T
    )


# ============================================================
# RANKING DELLE TRE RAPPRESENTAZIONI
# ============================================================

ranking = {}

posizioni = {}


for configurazione in configurazioni:

    ranking[
        configurazione
    ] = {}

    posizioni[
        configurazione
    ] = {}


    for i, src_id in enumerate(
        source_ids
    ):

        ordine = crea_ranking(

            similarita[
                configurazione
            ][i],

            target_ids
        )


        ranking[
            configurazione
        ][src_id] = [

            target_ids[j]

            for j in ordine
        ]


        # Posizioni uniche:
        # 1, 2, 3, ..., 425

        posizioni[
            configurazione
        ][src_id] = {

            j: posizione

            for posizione, j
            in enumerate(
                ordine,
                start=1
            )
        }


# ============================================================
# FUSIONE 1:
# RECIPROCAL RANK FUSION
# ============================================================

ranking[
    "fusione_rrf"
] = {}

posizioni[
    "fusione_rrf"
] = {}


for i, src_id in enumerate(
    source_ids
):

    candidati = []


    pos_nome = posizioni[
        "nome_descrizione"
    ][src_id]


    pos_contesto = posizioni[
        "contesto_tabella"
    ][src_id]


    for j, tgt_id in enumerate(
        target_ids
    ):

        rango_nome = (
            pos_nome[j]
        )

        rango_contesto = (
            pos_contesto[j]
        )


        # ----------------------------------------------------
        # RECIPROCAL RANK FUSION
        # ----------------------------------------------------

        score_rrf = (

            1
            / (
                RRF_K
                + rango_nome
            )

            +

            1
            / (
                RRF_K
                + rango_contesto
            )
        )


        # Media delle similarita'
        # usata SOLO per rompere eventuali parita'

        media_similarita = (

            float(
                similarita[
                    "nome_descrizione"
                ][i][j]
            )

            +

            float(
                similarita[
                    "contesto_tabella"
                ][i][j]
            )

        ) / 2


        candidati.append({

            "indice": j,

            "target": tgt_id,

            "rrf":
                score_rrf,

            "media_similarita":
                media_similarita
        })


    # --------------------------------------------------------
    # Ordinamento RRF
    #
    # 1. score RRF
    # 2. media similarita'
    # 3. target alfabetico
    # --------------------------------------------------------

    candidati.sort(

        key=lambda x: (

            -round(
                x["rrf"],
                12
            ),

            -round(
                x[
                    "media_similarita"
                ],
                7
            ),

            x["target"]
        )
    )


    ranking[
        "fusione_rrf"
    ][src_id] = [

        x["target"]

        for x in candidati
    ]


    posizioni[
        "fusione_rrf"
    ][src_id] = {

        x["indice"]:
            posizione

        for posizione, x
        in enumerate(
            candidati,
            start=1
        )
    }


# ============================================================
# FUSIONE 2:
# BEST-RANK FUSION
# ============================================================
#
# Idea:
#
# dare maggiore importanza alla rappresentazione
# che colloca il candidato piu' in alto.
#
# Se un candidato e':
#
# nome+descrizione = 150
# contesto         = 1
#
# il best_rank sara' 1.
#
# L'altro rango viene usato solo dopo,
# come secondo criterio.
# ============================================================

ranking[
    "fusione_best_rank"
] = {}

posizioni[
    "fusione_best_rank"
] = {}


for i, src_id in enumerate(
    source_ids
):

    candidati = []


    pos_nome = posizioni[
        "nome_descrizione"
    ][src_id]


    pos_contesto = posizioni[
        "contesto_tabella"
    ][src_id]


    for j, tgt_id in enumerate(
        target_ids
    ):

        rango_nome = (
            pos_nome[j]
        )

        rango_contesto = (
            pos_contesto[j]
        )


        # Rango migliore tra i due metodi

        best_rank = min(

            rango_nome,

            rango_contesto
        )


        # Rango dell'altro metodo

        altro_rank = max(

            rango_nome,

            rango_contesto
        )


        # Similarita' media usata
        # solo come terzo criterio

        media_similarita = (

            float(
                similarita[
                    "nome_descrizione"
                ][i][j]
            )

            +

            float(
                similarita[
                    "contesto_tabella"
                ][i][j]
            )

        ) / 2


        candidati.append({

            "indice":
                j,

            "target":
                tgt_id,

            "best_rank":
                best_rank,

            "altro_rank":
                altro_rank,

            "media_similarita":
                media_similarita
        })


    # --------------------------------------------------------
    # Ordinamento Best-Rank
    #
    # 1. miglior rango
    # 2. rango dell'altro metodo
    # 3. media delle similarita'
    # 4. target alfabetico
    # --------------------------------------------------------

    candidati.sort(

        key=lambda x: (

            x[
                "best_rank"
            ],

            x[
                "altro_rank"
            ],

            -round(
                x[
                    "media_similarita"
                ],
                7
            ),

            x[
                "target"
            ]
        )
    )


    ranking[
        "fusione_best_rank"
    ][src_id] = [

        x["target"]

        for x in candidati
    ]


    posizioni[
        "fusione_best_rank"
    ][src_id] = {

        x["indice"]:
            posizione

        for posizione, x
        in enumerate(
            candidati,
            start=1
        )
    }


# ============================================================
# CONFIGURAZIONI FINALI DA CONFRONTARE
# ============================================================

ordine_configurazioni = [

    "nome_descrizione",

    "contesto_tabella",

    "senza_contesto",

    "fusione_rrf",

    "fusione_best_rank"
]


# ============================================================
# RECALL@1, RECALL@5, RECALL@10
# ============================================================

risultati = []


for configurazione in ordine_configurazioni:

    hit1, recall1 = calcola_recall(

        ranking[
            configurazione
        ],

        ground_truth,

        1
    )


    hit5, recall5 = calcola_recall(

        ranking[
            configurazione
        ],

        ground_truth,

        5
    )


    hit10, recall10 = calcola_recall(

        ranking[
            configurazione
        ],

        ground_truth,

        10
    )


    risultati.append({

        "configurazione":
            configurazione,

        "hit@1":
            hit1,

        "recall@1":
            round(
                recall1,
                4
            ),

        "hit@5":
            hit5,

        "recall@5":
            round(
                recall5,
                4
            ),

        "hit@10":
            hit10,

        "recall@10":
            round(
                recall10,
                4
            )
    })


# ============================================================
# RANGHI DELLE CORRISPONDENZE CORRETTE
# ============================================================

righe_ranghi = []


for src_id, tgt_id in ground_truth:

    j = target_index[
        tgt_id
    ]


    rango_nome = (
        posizioni[
            "nome_descrizione"
        ][src_id][j]
    )


    rango_contesto = (
        posizioni[
            "contesto_tabella"
        ][src_id][j]
    )


    rango_senza = (
        posizioni[
            "senza_contesto"
        ][src_id][j]
    )


    rango_rrf = (
        posizioni[
            "fusione_rrf"
        ][src_id][j]
    )


    rango_best = (
        posizioni[
            "fusione_best_rank"
        ][src_id][j]
    )


    righe_ranghi.append({

        "source":
            src_id,

        "target_corretto":
            tgt_id,

        "rango_nome_descrizione":
            rango_nome,

        "rango_contesto_tabella":
            rango_contesto,

        "rango_senza_contesto":
            rango_senza,

        "rango_fusione_rrf":
            rango_rrf,

        "rango_fusione_best_rank":
            rango_best,

        "top10_nome_descrizione":
            rango_nome <= 10,

        "top10_contesto_tabella":
            rango_contesto <= 10,

        "top10_senza_contesto":
            rango_senza <= 10,

        "top10_fusione_rrf":
            rango_rrf <= 10,

        "top10_fusione_best_rank":
            rango_best <= 10
    })


# ============================================================
# CASI GUADAGNATI E PERSI
# ============================================================

righe_casi = []


for riga in righe_ranghi:

    in_nome = (
        riga[
            "top10_nome_descrizione"
        ]
    )

    in_contesto = (
        riga[
            "top10_contesto_tabella"
        ]
    )

    in_rrf = (
        riga[
            "top10_fusione_rrf"
        ]
    )

    in_best = (
        riga[
            "top10_fusione_best_rank"
        ]
    )


    categorie = []


    # --------------------------------------------------------
    # RRF VS NOME+DESCRIZIONE
    # --------------------------------------------------------

    if in_rrf and not in_nome:

        categorie.append(
            "RRF_guadagnato_vs_nome_descrizione"
        )


    if not in_rrf and in_nome:

        categorie.append(
            "RRF_perso_vs_nome_descrizione"
        )


    # --------------------------------------------------------
    # RRF VS CONTESTO
    # --------------------------------------------------------

    if in_rrf and not in_contesto:

        categorie.append(
            "RRF_guadagnato_vs_contesto"
        )


    if not in_rrf and in_contesto:

        categorie.append(
            "RRF_perso_vs_contesto"
        )


    # --------------------------------------------------------
    # BEST-RANK VS NOME+DESCRIZIONE
    # --------------------------------------------------------

    if in_best and not in_nome:

        categorie.append(
            "BEST_guadagnato_vs_nome_descrizione"
        )


    if not in_best and in_nome:

        categorie.append(
            "BEST_perso_vs_nome_descrizione"
        )


    # --------------------------------------------------------
    # BEST-RANK VS CONTESTO
    # --------------------------------------------------------

    if in_best and not in_contesto:

        categorie.append(
            "BEST_guadagnato_vs_contesto"
        )


    if not in_best and in_contesto:

        categorie.append(
            "BEST_perso_vs_contesto"
        )


    # --------------------------------------------------------
    # DIFFERENZA DIRETTA RRF VS BEST-RANK
    # --------------------------------------------------------

    if in_best and not in_rrf:

        categorie.append(
            "BEST_guadagnato_vs_RRF"
        )


    if in_rrf and not in_best:

        categorie.append(
            "BEST_perso_vs_RRF"
        )


    if categorie:

        nuova_riga = dict(
            riga
        )

        nuova_riga[
            "categoria"
        ] = " | ".join(
            categorie
        )

        righe_casi.append(
            nuova_riga
        )


# ============================================================
# TOP-10 EFFETTIVE
# ============================================================

righe_top10 = []


for configurazione in ordine_configurazioni:

    for src_id in source_ids:

        primi_10 = (
            ranking[
                configurazione
            ][src_id][:10]
        )


        for posizione, tgt_id in enumerate(

            primi_10,

            start=1
        ):

            righe_top10.append({

                "configurazione":
                    configurazione,

                "source":
                    src_id,

                "posizione":
                    posizione,

                "target":
                    tgt_id
            })


# ============================================================
# SALVATAGGIO CSV
# ============================================================

pd.DataFrame(
    risultati
).to_csv(

    "risultati_fusione_retrieval.csv",

    index=False
)


pd.DataFrame(
    righe_ranghi
).to_csv(

    "ranghi_ground_truth_fusione.csv",

    index=False
)


pd.DataFrame(
    righe_casi
).to_csv(

    "casi_guadagnati_persi_fusione.csv",

    index=False
)


pd.DataFrame(
    righe_top10
).to_csv(

    "top10_fusione_retrieval.csv",

    index=False
)


# ============================================================
# OUTPUT FINALE
# ============================================================

print()

print(
    "RISULTATI FINALI"
)

print()


df_risultati = pd.DataFrame(
    risultati
)


print(
    df_risultati.to_string(
        index=False
    )
)


print()

print(
    "File creati:"
)

print(
    "- risultati_fusione_retrieval.csv"
)

print(
    "- ranghi_ground_truth_fusione.csv"
)

print(
    "- casi_guadagnati_persi_fusione.csv"
)

print(
    "- top10_fusione_retrieval.csv"
)