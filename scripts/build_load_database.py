from pathlib import Path
import duckdb

data_dir = Path(
    "/Users/mikemueller/GitHub/"
    "ercot_load_forecasting/data/raw/ercot"
)

database_path = Path(
    "/Users/mikemueller/MyPythonStuff/"
    "Python_Practice/Data/ercot.duckdb"
)

files = sorted(data_dir.glob("Native_Load_*.xlsx"))

print(f"Found {len(files)} files.")

for file in files:
    print(file.name)

if not files:
    raise FileNotFoundError("No ERCOT Excel files were found.")



con = duckdb.connect(str(database_path))

con.sql("INSTALL excel")
con.sql("LOAD excel")

select_statements = []

for file in files:
    file_path = str(file)

    select_statements.append(
        f"""
        SELECT *
        FROM read_xlsx('{file_path}')
        """
    )

union_query = "\nUNION ALL\n".join(select_statements)

create_table_query = f"""
    CREATE OR REPLACE TABLE ercot_load AS
    {union_query}
"""
print(create_table_query)
con.sql(create_table_query)

print(
    con.sql("""
        SELECT COUNT(*) AS row_count
        FROM ercot_load
    """)
)

print(
    con.sql("""
        SELECT *
        FROM ercot_load
        LIMIT 5
    """)
)

con.close()