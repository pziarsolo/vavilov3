INSTITUTE_ACCESSION_COUNTRY_STATS = """
SELECT  "country_id",
        "country_code",
        "country_name",
       COUNT(*) AS "counts" FROM (
            SELECT DISTINCT
                "vavilov_accession"."accession_id",
                "vavilov_country"."country_id" AS "country_id",
                "vavilov_country"."code" AS "country_code",
                "vavilov_country"."name" AS "country_name"
                    FROM "vavilov_country"
                        INNER JOIN "vavilov_passport" ON ("vavilov_country"."country_id" = "vavilov_passport"."country_id")
                        INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
                    WHERE "vavilov_accession"."institute_id" = {institute_id}
            ) as TMP
GROUP BY "country_id", "country_code", "country_name"
"""

INSTITUTE_ACCESSIONSET_COUNTRY_STATS = """
SELECT  "country_id",
        "country_code",
        "country_name",
       COUNT(*) AS "counts" FROM (
            SELECT DISTINCT
                "vavilov_accessionset"."accessionset_id",
                "vavilov_country"."country_id" AS "country_id",
                "vavilov_country"."code" AS "country_code",
                "vavilov_country"."name" AS "country_name"
                    FROM "vavilov_country"
                        INNER JOIN "vavilov_passport" ON ("vavilov_country"."country_id" = "vavilov_passport"."country_id")
                        INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
                        INNER JOIN "vavilov_accessionset_accessions" ON ("vavilov_accession"."accession_id" = "vavilov_accessionset_accessions"."accession_id")
                        INNER JOIN "vavilov_accessionset" ON ("vavilov_accessionset"."accessionset_id" = "vavilov_accessionset_accessions"."accessionset_id")
                    WHERE "vavilov_accessionset"."institute_id" = {institute_id}
            ) as TMP
GROUP BY "country_id", "country_code", "country_name"
"""

INSTITUTE_ACCESSION_TAXA_STATS = '''
SELECT "taxon_id",
    "taxon_name",
    "rank_name",
    COUNT(*) AS "counts" FROM (
        SELECT DISTINCT "vavilov_accession"."accession_id",
            "vavilov_taxon"."taxon_id" as "taxon_id",
            "vavilov_taxon"."name" as "taxon_name",
            "vavilov_rank"."name" as "rank_name"
        FROM "vavilov_taxon"
            INNER JOIN "vavilov_passport_taxa" ON ("vavilov_taxon"."taxon_id" = "vavilov_passport_taxa"."taxon_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."passport_id" = "vavilov_passport_taxa"."passport_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
            INNER JOIN "vavilov_rank" ON ("vavilov_taxon"."rank_id" = "vavilov_rank"."rank_id")
        WHERE "vavilov_accession"."institute_id" = {institute_id}) as TMP
GROUP BY "taxon_name", "rank_name", "taxon_id";
'''

INSTITUTE_ACCESSIONSET_TAXA_STATS = '''
SELECT "taxon_id",
    "taxon_name",
    "rank_name",
    COUNT(*) AS "counts" FROM (
        SELECT DISTINCT "vavilov_accessionset"."accessionset_id",
                "vavilov_taxon"."taxon_id" as "taxon_id",
                "vavilov_taxon"."name" as "taxon_name",
                "vavilov_rank"."name" as "rank_name"
        FROM "vavilov_taxon"
            INNER JOIN "vavilov_passport_taxa" ON ("vavilov_taxon"."taxon_id" = "vavilov_passport_taxa"."taxon_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."passport_id" = "vavilov_passport_taxa"."passport_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
            INNER JOIN "vavilov_accessionset_accessions" ON ("vavilov_accession"."accession_id" = "vavilov_accessionset_accessions"."accession_id")
            INNER JOIN "vavilov_accessionset" ON ("vavilov_accessionset"."accessionset_id" = "vavilov_accessionset_accessions"."accessionset_id")
            INNER JOIN "vavilov_rank" ON ("vavilov_taxon"."rank_id" = "vavilov_rank"."rank_id")
        WHERE "vavilov_accessionset"."institute_id" = {institute_id}) as TMP
GROUP BY "taxon_name", "rank_name", "taxon_id";
'''

COUNTRY_ACCESSION_INSTITUTE_STATS = """
SELECT
    "institute_id",
    "institute_code",
    "institute_name",
    COUNT(*) AS "counts" FROM (
        SELECT DISTINCT
            "vavilov_accession"."accession_id",
            "vavilov_institute"."institute_id" AS "institute_id",
            "vavilov_institute"."code" AS "institute_code",
            "vavilov_institute"."name" AS "institute_name"
        FROM "vavilov_institute"
            INNER JOIN "vavilov_accession" ON ("vavilov_accession"."institute_id" = "vavilov_institute"."institute_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
        WHERE "vavilov_passport"."country_id" = {country_id}
    ) as TMP
GROUP BY "institute_id", "institute_code", "institute_name"
"""

COUNTRY_ACCESSIONSET_INSTITUTE_STATS = """
SELECT
    "institute_id",
    "institute_code",
    "institute_name",
    COUNT(*) AS "counts" FROM (
        SELECT DISTINCT
            "vavilov_accessionset"."accessionset_id",
            "vavilov_institute"."institute_id" AS "institute_id",
            "vavilov_institute"."code" AS "institute_code",
            "vavilov_institute"."name" AS "institute_name"
        FROM "vavilov_institute"
            INNER JOIN "vavilov_accessionset" ON ("vavilov_accessionset"."institute_id" = "vavilov_institute"."institute_id")
            INNER JOIN "vavilov_accessionset_accessions" ON ("vavilov_accessionset_accessions"."accessionset_id" = "vavilov_accessionset"."accessionset_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_accession"."accession_id" = "vavilov_accessionset_accessions"."accession_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
        WHERE "vavilov_passport"."country_id" = {country_id}
    ) as TMP
GROUP BY "institute_id", "institute_code", "institute_name"
"""

COUNTRY_ACCESSION_TAXA_STATS = '''
SELECT "taxon_id",
    "taxon_name",
    "rank_name",
    COUNT(*) AS "counts" FROM (
        SELECT DISTINCT "vavilov_accession"."accession_id",
            "vavilov_taxon"."taxon_id" as "taxon_id",
            "vavilov_taxon"."name" as "taxon_name",
            "vavilov_rank"."name" as "rank_name"
        FROM "vavilov_taxon"
            INNER JOIN "vavilov_passport_taxa" ON ("vavilov_taxon"."taxon_id" = "vavilov_passport_taxa"."taxon_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."passport_id" = "vavilov_passport_taxa"."passport_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
            INNER JOIN "vavilov_rank" ON ("vavilov_taxon"."rank_id" = "vavilov_rank"."rank_id")
        WHERE "vavilov_passport"."country_id" = {country_id}
    ) as TMP
GROUP BY "taxon_name", "rank_name", "taxon_id";
'''
COUNTRY_ACCESSIONSET_TAXA_STATS = '''
SELECT "taxon_id",
    "taxon_name",
    "rank_name",
    COUNT(*) AS "counts" FROM (
        SELECT DISTINCT "vavilov_accessionset"."accessionset_id",
            "vavilov_taxon"."taxon_id" as "taxon_id",
            "vavilov_taxon"."name" as "taxon_name",
            "vavilov_rank"."name" as "rank_name"
        FROM "vavilov_taxon"
            INNER JOIN "vavilov_passport_taxa" ON ("vavilov_taxon"."taxon_id" = "vavilov_passport_taxa"."taxon_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."passport_id" = "vavilov_passport_taxa"."passport_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
            INNER JOIN "vavilov_accessionset_accessions" ON ("vavilov_accession"."accession_id" = "vavilov_accessionset_accessions"."accession_id")
            INNER JOIN "vavilov_accessionset" ON ("vavilov_accessionset_accessions"."accessionset_id" = "vavilov_accessionset"."accessionset_id")
            INNER JOIN "vavilov_rank" ON ("vavilov_taxon"."rank_id" = "vavilov_rank"."rank_id")
        WHERE "vavilov_passport"."country_id" = {country_id}
    ) as TMP
GROUP BY "taxon_name", "rank_name", "taxon_id";
'''
TAXA_ACCESSION_STATS = '''
SELECT "taxon_id",
    "taxon_name",
    "rank_name",
    COUNT(*) AS "num_accessions" FROM (
        SELECT DISTINCT "vavilov_accession"."accession_id",
            "vavilov_taxon"."taxon_id" as "taxon_id",
            "vavilov_taxon"."name" as "taxon_name",
            "vavilov_rank"."name" as "rank_name"
        FROM "vavilov_taxon"
            INNER JOIN "vavilov_passport_taxa" ON ("vavilov_taxon"."taxon_id" = "vavilov_passport_taxa"."taxon_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."passport_id" = "vavilov_passport_taxa"."passport_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
            INNER JOIN "vavilov_rank" ON ("vavilov_taxon"."rank_id" = "vavilov_rank"."rank_id")
    ) AS TMP
GROUP BY "taxon_name", "rank_name", "taxon_id";
'''
TAXA_ACCESSIONSET_STATS = '''
SELECT "taxon_id",
    "taxon_name",
    "rank_name",
    COUNT(*) AS "num_accessionsets" FROM (
        SELECT DISTINCT "vavilov_accessionset"."accessionset_id",
            "vavilov_taxon"."taxon_id" as "taxon_id",
            "vavilov_taxon"."name" as "taxon_name",
            "vavilov_rank"."name" as "rank_name"
        FROM "vavilov_taxon"
            INNER JOIN "vavilov_passport_taxa" ON ("vavilov_taxon"."taxon_id" = "vavilov_passport_taxa"."taxon_id")
            INNER JOIN "vavilov_passport" ON ("vavilov_passport"."passport_id" = "vavilov_passport_taxa"."passport_id")
            INNER JOIN "vavilov_accession" ON ("vavilov_passport"."accession_id" = "vavilov_accession"."accession_id")
            INNER JOIN "vavilov_accessionset_accessions" ON ("vavilov_accession"."accession_id" = "vavilov_accessionset_accessions"."accession_id")
            INNER JOIN "vavilov_accessionset" ON ("vavilov_accessionset_accessions"."accessionset_id" = "vavilov_accessionset"."accessionset_id")
            INNER JOIN "vavilov_rank" ON ("vavilov_taxon"."rank_id" = "vavilov_rank"."rank_id")
    ) AS TMP2
GROUP BY "taxon_name", "rank_name", "taxon_id";
'''


def get_institute_stats_raw_sql(institute_id, stats_type, entity_type, user):
    if stats_type == 'country':
        if entity_type == 'accession':
            return INSTITUTE_ACCESSION_COUNTRY_STATS.format(institute_id=institute_id)
        elif entity_type == 'accessionset':
            return INSTITUTE_ACCESSIONSET_COUNTRY_STATS.format(institute_id=institute_id)
    elif stats_type == 'taxa':
        if entity_type == 'accession':
            return INSTITUTE_ACCESSION_TAXA_STATS.format(institute_id=institute_id)
        elif entity_type == 'accessionset':
            return INSTITUTE_ACCESSIONSET_TAXA_STATS.format(institute_id=institute_id)


def get_country_stats_raw_sql(country_id, stats_type, entity_type, user):
    if stats_type == 'institute':
        if entity_type == 'accession':
            return COUNTRY_ACCESSION_INSTITUTE_STATS.format(country_id=country_id)
        elif entity_type == 'accessionset':
            return COUNTRY_ACCESSIONSET_INSTITUTE_STATS.format(country_id=country_id)
    elif stats_type == 'taxa':
        if entity_type == 'accession':
            return COUNTRY_ACCESSION_TAXA_STATS.format(country_id=country_id)
        elif entity_type == 'accessionset':
            return COUNTRY_ACCESSIONSET_TAXA_STATS.format(country_id=country_id)


def get_taxa_stas_raw_sql(entity_type, user=None):
    if entity_type == 'accession':
        return TAXA_ACCESSION_STATS
    elif entity_type == 'accessionset':
        return TAXA_ACCESSIONSET_STATS
