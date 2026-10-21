import csv
from collections import defaultdict


FILE_MIMIC = "data_validation/MIMIC_III_Schema.csv"
FILE_OMOP = "data_validation/OMOP_Schema.csv"
FILE_MAPPING = "data_validation/MIMIC_to_OMOP_Mapping.csv"


# ============================================================
# FUNZIONI DI BASE
# ============================================================

def pulisci(testo):

    if testo is None:
        return ""

    return str(testo).strip()


def crea_id(tabella, colonna):

    return (
        pulisci(tabella).upper()
        + "."
        + pulisci(colonna).upper()
    )


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

            # Stessa regola della pipeline:
            # se manca tabella o nome colonna,
            # la riga non rappresenta un attributo valido.

            if (
                tabella == ""
                or
                nome == ""
            ):
                continue

            attributi.append({
                "id": crea_id(
                    tabella,
                    nome
                ),
                "descrizione":
                    descrizione
            })

    return attributi


# ============================================================
# LETTURA DELLE COLONNE MIMIC ANNOTATE
# ============================================================

def leggi_sorgenti_annotate(nome_file):

    sorgenti = set()

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

            if (
                src_ent != ""
                and
                src_att != ""
            ):

                sorgenti.add(
                    crea_id(
                        src_ent,
                        src_att
                    )
                )

    return sorgenti


# ============================================================
# ANALISI DELLE DESCRIZIONI
# ============================================================

def analizza_descrizioni(
    schema,
    nome_dataset
):

    mancanti = []

    gruppi_descrizioni = defaultdict(
        list
    )

    for attributo in schema:

        descrizione = attributo[
            "descrizione"
        ]

        if descrizione == "":

            mancanti.append(
                attributo["id"]
            )

        else:

            chiave = (
                descrizione
                .strip()
                .lower()
            )

            gruppi_descrizioni[
                chiave
            ].append(
                attributo["id"]
            )

    duplicati = {
        descrizione: attributi
        for descrizione, attributi
        in gruppi_descrizioni.items()
        if len(attributi) > 1
    }

    print()

    print(
        "===================================="
    )

    print(
        nome_dataset
    )

    print(
        "===================================="
    )

    print(
        "Totale colonne:",
        len(schema)
    )

    print(
        "Descrizioni mancanti:",
        len(mancanti)
    )

    print(
        "Descrizioni presenti:",
        len(schema)
        -
        len(mancanti)
    )

    print(
        "Gruppi di descrizioni duplicate:",
        len(duplicati)
    )

    colonne_duplicate = sum(
        len(attributi)
        for attributi
        in duplicati.values()
    )

    print(
        "Colonne coinvolte in duplicati:",
        colonne_duplicate
    )

    return (
        mancanti,
        duplicati
    )


# ============================================================
# LETTURA DATASET
# ============================================================

mimic_completo = leggi_schema(
    FILE_MIMIC
)

omop = leggi_schema(
    FILE_OMOP
)

sorgenti_annotate = (
    leggi_sorgenti_annotate(
        FILE_MAPPING
    )
)


# Consideriamo solo gli attributi MIMIC
# effettivamente presenti nel mapping.

mimic_valutato = [
    attributo
    for attributo
    in mimic_completo
    if attributo["id"]
    in sorgenti_annotate
]


# ============================================================
# ANALISI
# ============================================================

(
    mancanti_mimic,
    duplicati_mimic
) = analizza_descrizioni(
    mimic_valutato,
    "MIMIC"
)


(
    mancanti_omop,
    duplicati_omop
) = analizza_descrizioni(
    omop,
    "OMOP"
)


# ============================================================
# DESCRIZIONI MANCANTI
# ============================================================

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


# ============================================================
# DESCRIZIONI DUPLICATE
# ============================================================

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
# RIEPILOGO
# ============================================================

with open(
    "censimento_descrizioni.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    scrittore = csv.writer(
        file
    )

    scrittore.writerow([
        "dataset",
        "totale_colonne",
        "descrizioni_mancanti",
        "descrizioni_presenti",
        "gruppi_descrizioni_duplicate",
        "colonne_coinvolte_in_duplicati"
    ])

    colonne_duplicate_mimic = sum(
        len(attributi)
        for attributi
        in duplicati_mimic.values()
    )

    colonne_duplicate_omop = sum(
        len(attributi)
        for attributi
        in duplicati_omop.values()
    )

    scrittore.writerow([
        "MIMIC",
        len(mimic_valutato),
        len(mancanti_mimic),
        len(mimic_valutato)
        -
        len(mancanti_mimic),
        len(duplicati_mimic),
        colonne_duplicate_mimic
    ])

    scrittore.writerow([
        "OMOP",
        len(omop),
        len(mancanti_omop),
        len(omop)
        -
        len(mancanti_omop),
        len(duplicati_omop),
        colonne_duplicate_omop
    ])


print()

print(
    "File creati:"
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