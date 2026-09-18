# Build various non-calendar features.

import pandas as pd
import duckdb

#Load table into dataframe

con = duckdb.connect("/Users/mikemueller/GitHub/ercot_load_forecasting/data/database/ercot.duckdb")

df = con.sql('''SELECT * FROM ercot_load_clean''').df()

regions= ['COAST', 'EAST', 'FAR_WEST', 'NORTH', 'NORTH_C', 'SOUTHERN', 'SOUTH_C', 'WEST']

df['ERCOT_lag_24']=df['ERCOT'].shift(24)
df['ERCOT_lag_168']=df['ERCOT'].shift(168)

for r in regions:
    for lag in [24, 168]:
        featstr=r+'_lag_'+str(lag)
        df[featstr]=df[r].shift(lag)

    
con.register("new_features_df", df)


con.sql("""
    CREATE OR REPLACE TABLE ercot_load_features AS
    SELECT *
    FROM new_features_df
""")