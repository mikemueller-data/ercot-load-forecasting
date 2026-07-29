#07-29-2026
Retrieved Excel files from https://www.ercot.com/gridinfo/load/load_hist
Some files were named differently and had different extensions (e.g. *.xls)
Standardized the names to Native_Load_{year}.xlsx and saved xls files as xlsx.

Created script ercot_load_forecasting/scripts/build_load_database.py to create 
concatenated database file of Jan 2004 - June 2026 electric load for all 8 
regions plus aggregated total for ERCOT. Values are target values for predictive 
modeling training and testing.
