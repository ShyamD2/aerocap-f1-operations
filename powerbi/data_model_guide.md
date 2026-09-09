# Power BI Data Modeling & Integration Guide

This guide documents how to import the `F1-OpsCorrelate` SQLite database into **Microsoft Power BI Desktop** to build the 3-page interactive operations dashboard.

---

## 1. Connecting Power BI to the SQLite Database

### Method A: Direct SQLite ODBC Driver (Recommended for Live Refresh)
1. Install the free **SQLite ODBC Driver** (from `ch-werner.de/sqliteodbc/` or via Chocolatey: `choco install sqlite-odbc`).
2. In Power BI Desktop, click **Get Data** $\rightarrow$ **More...** $\rightarrow$ **ODBC**.
3. Select the DSN or enter the connection string:
   ```
   driver={SQLite3 ODBC Driver};Database=E:\downloads\f1 jobs\data\f1_operations.db;
   ```
4. Select all 7 tables:
   * `dim_facilities`
   * `dim_parts`
   * `fact_test_runs`
   * `fact_expenses`
   * `dim_personnel_td045`
   * `fact_correlation_runs`
   * `candidate_upgrades`

### Method B: Python Script Connector (No ODBC Driver Required)
1. In Power BI Desktop, select **Get Data** $\rightarrow$ **Python script**.
2. Paste the following script:
   ```python
   import sqlite3
   import pandas as pd

   conn = sqlite3.connect(r"E:\downloads\f1 jobs\data\f1_operations.db")
   dim_facilities = pd.read_sql_query("SELECT * FROM dim_facilities", conn)
   dim_parts = pd.read_sql_query("SELECT * FROM dim_parts", conn)
   fact_test_runs = pd.read_sql_query("SELECT * FROM fact_test_runs", conn)
   fact_expenses = pd.read_sql_query("SELECT * FROM fact_expenses", conn)
   dim_personnel_td045 = pd.read_sql_query("SELECT * FROM dim_personnel_td045", conn)
   fact_correlation_runs = pd.read_sql_query("SELECT * FROM fact_correlation_runs", conn)
   candidate_upgrades = pd.read_sql_query("SELECT * FROM candidate_upgrades", conn)
   conn.close()
   ```

---

## 2. Model View Relationships (Star Schema)

In Power BI's **Model View**, establish the following 1-to-many single-direction relationships:

```
dim_facilities [facility_id] 1  --->  * fact_test_runs [facility_id]
dim_parts [part_id]           1  --->  * fact_test_runs [critical_part_id]
fact_test_runs [test_id]      1  --->  * fact_expenses [test_id]
```

---

## 3. Importing DAX Measures
Open the `dax_measures.dax` file located at `powerbi/dax_measures.dax`.
Create a dedicated table named `_Measures` in Power BI, and paste each formula to enable:
* `[NetRelevantCostsUSD]`
* `[StatutoryCostCapUSD]`
* `[CostCapHeadroomUSD]`
* `[ComplianceStatus]`
* `[CapExHeadroomUSD]`
* `[FacilityReadinessRate]`
