#ETL script for ERCOT load tables
from pathlib import Path
import duckdb

data_dir = Path(
    "/Users/mikemueller/GitHub/"
    "ercot_load_forecasting/data/raw/ercot"
)

database_path = Path(
    "/Users/mikemueller/GitHub/"
    "ercot_load_forecasting/data/database/"
    "ercot.duckdb"
)

files = sorted(data_dir.glob("Native_Load_*.xlsx"))

print(f"Found {len(files)} files.")

for file in files:
    print(file.name)

if not files:
    raise FileNotFoundError("No ERCOT Excel files were found.")

####^^^Get Excel files^^^####
#####Make database tables#####

con = duckdb.connect(str(database_path))

con.sql("INSTALL excel")
con.sql("LOAD excel")

select_statements = []

for file in files:
    file_path = str(file)

    select_statements.append(
        f"""
        SELECT *
        FROM read_xlsx(
            '{file_path}',
            all_varchar = true)
        """
    )

union_query = "\nUNION ALL\n".join(select_statements)

create_raw_table_query = f"""
    CREATE OR REPLACE TABLE ercot_load_raw AS
    {union_query}
"""
print(create_raw_table_query)
###Create raw data table
con.sql(create_raw_table_query)

#Historical ERCOT files use multiple timestamp formats:
#1. Excel serial dates (older files)
#2. ISO timestamps
#3. MM/DD/YYYY HH:MM
#4. 24:00 notation for hour ending
#5. Add is_dst_repeat boolean for repeat 2AM hours when clocks fall back

create_clean_table_query="""
    CREATE OR REPLACE TABLE ercot_load_clean AS
    SELECT
        time_bucket(
            INTERVAL '1 hour',
            (
            CASE
                WHEN TRY_CAST(Hour_End AS DOUBLE) IS NOT NULL
                    THEN TIMESTAMP '1899-12-30'
                     + TRY_CAST(Hour_End AS DOUBLE) * INTERVAL '1 day'

                WHEN TRY_CAST(Hour_End AS TIMESTAMP) IS NOT NULL
                    THEN TRY_CAST(Hour_End AS TIMESTAMP)

                WHEN Hour_End LIKE '% 24:00'
                    THEN TRY_STRPTIME(
                        REPLACE(Hour_End, ' 24:00', ' 00:00'),
                        '%m/%d/%Y %H:%M'
                    ) + INTERVAL '1 day'

                WHEN Hour_End LIKE '% DST'
                    THEN TRY_STRPTIME(
                        REPLACE(Hour_End, ' DST', ''),
                        '%m/%d/%Y %H:%M'
                    )

                ELSE TRY_STRPTIME(Hour_End, '%m/%d/%Y %H:%M')
            END
            )  + INTERVAL '30 minutes'
        ) AS Hour_End,

        TRY_CAST(COAST AS DOUBLE) AS COAST,
        TRY_CAST(EAST AS DOUBLE) AS EAST,
        TRY_CAST(FAR_WEST AS DOUBLE) AS FAR_WEST,
        TRY_CAST(NORTH AS DOUBLE) AS NORTH,
        TRY_CAST(NORTH_C AS DOUBLE) AS NORTH_C,
        TRY_CAST(SOUTHERN AS DOUBLE) AS SOUTHERN,
        TRY_CAST(SOUTH_C AS DOUBLE) AS SOUTH_C,
        TRY_CAST(WEST AS DOUBLE) AS WEST,
        TRY_CAST(ERCOT AS DOUBLE) AS ERCOT,
        Hour_End LIKE '% DST' AS is_dst_repeat

    FROM ercot_load_raw
"""
###Create clean data table
con.sql(create_clean_table_query)

print(
    con.sql("""
        SELECT COUNT(*) AS row_count_raw
        FROM ercot_load_raw
    """)
)

print(
    con.sql("""
        SELECT COUNT(*) AS row_count_clean
        FROM ercot_load_clean
    """)
)

print(
    con.sql("""
        SELECT *
        FROM ercot_load_raw
        LIMIT 5
    """).df()
)

print(
    con.sql("""
        SELECT *
        FROM ercot_load_clean
        LIMIT 30
    """).df()
)

print(
    con.sql("""
        SELECT Hour_End
        FROM ercot_load_raw
        LIMIT 30;
    """)
)

print(
    con.sql("""
    DESCRIBE ercot_load_raw
    """)
)


con.close()