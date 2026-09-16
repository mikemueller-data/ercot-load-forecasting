#ETL script for ERCOT load tables
from pathlib import Path
import duckdb
import holidays
import pandas as pd

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
#5. Add dst_flag boolean for DST fallback markers in raw ERCOT files (2017 and later)
#6. Add day_of_week and is_weekend
#7. Drop duplicate rows (May 2026 was fully duplicated)
#8. Add fallback_flag

# ERCOT local hour-ending conventions around spring DST transitions
# differ across historical source-file eras:
# pre-2017: local timestamps jump 01:00 -> 03:00
# 2017+:    local timestamps jump 02:00 -> 04:00
#
# UTC is constructed as a continuous hourly sequence, avoiding
# ambiguity from historical local-time/DST formatting conventions.

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
        ) AS local_timestamp,

        TRY_CAST(COAST AS DOUBLE) AS COAST,
        TRY_CAST(EAST AS DOUBLE) AS EAST,
        TRY_CAST(FAR_WEST AS DOUBLE) AS FAR_WEST,
        TRY_CAST(NORTH AS DOUBLE) AS NORTH,
        TRY_CAST(NORTH_C AS DOUBLE) AS NORTH_C,
        TRY_CAST(SOUTHERN AS DOUBLE) AS SOUTHERN,
        TRY_CAST(SOUTH_C AS DOUBLE) AS SOUTH_C,
        TRY_CAST(WEST AS DOUBLE) AS WEST,
        TRY_CAST(ERCOT AS DOUBLE) AS ERCOT,
        Hour_End LIKE '% DST' AS dst_flag,
        EXTRACT(DOW FROM local_timestamp) AS day_of_week,
        CASE
            WHEN EXTRACT(DOW FROM local_timestamp) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend
    FROM ercot_load_raw
"""
###Create clean data table
con.sql(create_clean_table_query)

#Add US Holidays

df=con.sql("""SELECT * FROM ercot_load_clean""").df()
us_holidays = holidays.US(years=range(2002, 2027))
print("US HOLIDAYS: ",us_holidays)
df['is_holiday']=df['local_timestamp'].dt.date.isin(us_holidays.keys())

#May 2026 and June 1 2026 have duplicate rows. Drop them.

df=df.drop_duplicates()

#Locl time falls back each fall, leading to legitimate repeat 2AM values on the fallback day. Let's flag it.

df['fallback_flag'] = df['local_timestamp'].duplicated()

#Add UTC timestamp starting from Jan 1, 2004 1am ERCOT local time. 
#This only works because each row is exactly 1 hour and none are skipped or missing in the local dataset. 

df['utc_timestamp'] = pd.date_range(
    start='2004-01-01 08:00',
    periods=len(df),
    freq='h',
    tz='UTC'
)

print(df['utc_timestamp'].dt.tz)
print(df['utc_timestamp'].head())

#Add day_of_year feature
df['day_of_year'] = df['local_timestamp'].dt.dayofyear

#Reorder columns for organization
df = df[
    [
        'local_timestamp',
        'utc_timestamp',
        'day_of_year',
        'day_of_week',
        'is_weekend',
        'is_holiday',
        'fallback_flag',
        'dst_flag',
        'COAST',
        'EAST',
        'FAR_WEST',
        'NORTH',
        'NORTH_C',
        'SOUTHERN',
        'SOUTH_C',
        'WEST',
        'ERCOT'
    ]
]

#Write to table
con.register("clean_df", df)








con.sql("""
    CREATE OR REPLACE TABLE ercot_load_clean AS
    SELECT *
    FROM clean_df
""")

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

print(database_path)

print(df.columns)

con.close()