README for ERCOT load forecasting and decision support project
Init: 28 July 2026

The electric utility industry needs to anticipate future load so that they can both ensure reliability (i.e. power remains available)
for their customers and minimize the risk of overcommitting costly resources that are not needed (e.g. running peaker plants at full 
power on days when base supply is sufficient). This is a classic case of assymmetric risk in which the costs of underestimating 
load requirements (reliability issues and blackouts, causing potentially catastrophic economic and reputational losses) and 
overestimating load requirements (generating more power than demand, incurring unnecessary costs) are drastically different.

The purpose of this project is to use historical load and weather data to predict future load requirement for the Electric Reliability
Council of Texas (ERCOT), including uncertainty and assessment of whether uncertainty bands overlap with critical operational
decision thresholds. In those cases, we will estimate the probability that load exceeds operational thresholds and provide a system 
to decide whether to generate or purchase electricity for the following day.

## Data

- ERCOT hourly load (2004–2026)

## Repository Structure

data/
scripts/
notebooks/
src/

## Workflow

1. Download ERCOT files
2. Build DuckDB database
3. Create clean database with ETL and EDA notebook iteration

## Technologies

Python
SQL
DuckDB
Pandas
NumPy
Git

## Project Status

09-16-26
The load ETL pipeline ingests historical ERCOT native-load files and standardizes historical timestamp formats into a canonical hourly dataset. The pipeline removes exact duplicate observations (May 2026), preserves source missing values, and provides both ERCOT local timestamps and a continuous UTC time axis for later weather-data alignment. Calendar metadata includes day-of-year, day-of-week, weekend, holiday, and DST/fallback indicators.

09-17-26
Added 24-hour and 168-hour load lag features for ERCOT system load and each load region.