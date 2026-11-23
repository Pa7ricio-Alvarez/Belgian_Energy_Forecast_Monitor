# Build guide (for you, the builder)

Each step says what you do, which technology it uses, and what you should see when it works.
Do the steps in order and don't move on until the "Check" works.

---

## Step 1 - Set up your computer

**Do:** install Python 3.11+, Git, Docker Desktop and PyCharm. Open this folder in PyCharm
(File > Open). In the PyCharm terminal:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Technology:** Python virtual environment, pip.
**Check:** `pytest` runs. (If `test_transform.py` fails, copy the error and ask for help.)

## Step 2 - Start MySQL

**Do:** make sure Docker Desktop is running, then `docker compose up -d`.
**Technology:** Docker, MySQL 8, SQL (`sql/00_setup.sql` runs automatically).
**What it does:** creates three databases (`raw`, `staging`, `marts`), the table
`raw.observations` and the run log `raw.pipeline_runs`.
**Check:**
```bash
docker exec -it energy-mysql mysql -uenergy -penergy_pw -e "SHOW TABLES IN raw;"
```
You should see `observations` and `pipeline_runs`. If port 3306 is busy, change the left number
in `docker-compose.yml` and set `MYSQL_PORT` to match.

## Step 3 - Look at the real data (important!)

**Do:** `python -m energy_monitor.run inspect wind` and then the same with `solar`.
**What it does:** downloads one week and prints the column names and the values of columns
such as `region`.
**Why:** I could not test against the live Elia API while building this, so **the column names
and filter values in `src/energy_monitor/config.py` are best guesses**. Compare:

- `COLUMN_CANDIDATES`: do the names match the printed columns? Fix any that don't.
- `FILTERS`: pick values so each moment is counted once. Example: if `region` has a
  "Belgium" total plus separate regions, keep only "Belgium". If another column (such as
  `gridconnectiontype`) splits the same power into overlapping groups, add a filter for it too.

**Check:** the names in config.py all appear in the printed list.

## Step 4 - Run the pipeline on a small period

**Do:** `python -m energy_monitor.run all --from 2025-01-01 --to 2025-01-08`
**What it does (Python + Polars + MySQL + SQL):**
1. `extract.py` downloads CSVs into `data/raw/` (retries if the API hiccups)
2. `transform.py` cleans them: UTC times, Brussels date/hour, numbers, no duplicates
3. `load.py` writes them to `raw.observations` using `INSERT ... ON DUPLICATE KEY UPDATE`
4. `sql/10_staging.sql` and `sql/20_marts.sql` build the summary tables
5. `sql/90_quality_checks.sql` tests the result; any failure stops the run

**Check:**
```bash
docker exec -it energy-mysql mysql -uenergy -penergy_pw -e "SELECT * FROM marts.mart_daily_accuracy LIMIT 10;"
```
Run the same command twice: the row count in `raw.observations` must not change.
That proves loading is repeatable (a key point for your README and interviews).

If the quality check `production_not_above_capacity` fails, the usual cause is double
counting: go back to Step 3 and tighten `FILTERS`.

## Step 5 - Load a longer period

**Do:** `python -m energy_monitor.run all --from 2024-01-01 --to 2025-01-01`
**Result:** a year of data. Write down the number of rows and how long it took: these go
in the README "Results" section.

## Step 6 - Run the tests and push to GitHub

**Do:** `pytest` and `ruff check .` must both pass. Then:
```bash
git init
git add .
git commit -m "Initial version of the energy monitor"
git branch -M main
git remote add origin https://github.com/<your-username>/belgian-energy-forecast-monitor.git
git push -u origin main
```
Create the empty repository on github.com first (without a README). On GitHub, open the
**Actions** tab: the CI workflow should turn green.

## Step 7 - Schedule it with Airflow (Astro CLI)

**Do:** install the [Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli), then:
```bash
cd airflow
astro dev init        # answer "yes" if it asks to use the non-empty folder; keep our files
astro dev start
```
`astro dev init` creates the missing Airflow files; our `dags/`, `requirements.txt` and
`docker-compose.override.yml` are already prepared. Open the Airflow page it prints
(http://localhost:8080), enable the `energy_monitor` DAG and trigger it.
**Result:** a screenshot of a green run for the README.

**Note:** I could not test the Airflow part in my environment. If a task fails with
`ModuleNotFoundError: energy_monitor`, apply the `volumes` and `environment` from
`airflow/docker-compose.override.yml` to the other Airflow services too.
Your MySQL must be running (`docker compose up -d` in the main folder).

## Step 8 - Dashboard (optional)

**Do:** `python -m energy_monitor.run export`, then follow `dashboard/README.md`.
**Result:** a public Tableau link + screenshot.

## Step 9 - Finish the README

Fill in the `[brackets]` in `README.md` with your real numbers. Only write numbers you
measured.

---

## GitHub "About" section

Click the gear icon next to **About** on your repository page and fill in:

- **Description:** `Automated pipeline monitoring the accuracy of Belgian wind & solar forecasts: Python/Polars, MySQL, SQL, Airflow, Docker. Built on Elia open data.`
- **Website:** your Tableau Public link
- **Topics:** `data-engineering` `etl` `python` `polars` `mysql` `sql` `apache-airflow` `docker` `energy` `open-data` `belgium` `data-pipeline`

## Troubleshooting

| Problem | Likely cause |
|---|---|
| `HTTP 400` from the download | The date filter or field name is wrong: check `DATETIME_FIELD` in config.py |
| `could not find columns` | Column names differ: fix `COLUMN_CANDIDATES` (Step 3) |
| `filters removed all rows` | `FILTERS` values don't exist: use the values printed by `inspect` |
| `Can't connect to MySQL` | Docker isn't running, or port/password differs from `.env` |
| Setup SQL changes not applied | It only runs on first start: `docker compose down -v` then `up -d` |
