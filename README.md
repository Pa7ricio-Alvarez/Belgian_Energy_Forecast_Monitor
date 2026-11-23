# Belgian Energy Forecast Monitor

**Goal:** an automated pipeline that shows how accurate Belgium's wind and solar power
forecasts are, and when they are most wrong, so that analysts can see it at a glance
without touching a line of code.

## Why it matters

Electricity supply and demand must match every second. When a wind or solar forecast is
off, energy companies have to buy or sell power at short notice, which costs money.
Knowing *when* and *by how much* forecasts miss helps them plan better.

## What you get

- A database that is updated daily and compares forecast vs. actual output
- Two ready-to-use summary tables: **daily accuracy** and **accuracy by hour of day**
- A dashboard: `[link / screenshot]`

## The data

Public data from [Elia](https://opendata.elia.be), Belgium's electricity grid operator:
wind and solar production, measured and forecast, every 15 minutes.
(Data © Elia, used under Elia's open-data terms.)

## Challenges and how I handled them

| Challenge | Approach |
|---|---|
| Millions of 15-minute rows | Download and process month by month with fast tooling (Polars) |
| Daylight-saving days have 23 or 25 hours | Store every time in UTC and convert to Brussels time once, in one place |
| Solar output is zero at night and some values are missing | Keep real zeros and real gaps separate; never fill gaps with zeros |
| Re-running a pipeline can create duplicate data | Loading is repeatable: the same input always gives the same result |
| Recent measurements are estimates that get revised | Every daily run re-loads the last 3 days |
| Bad data silently reaching reports | Automatic checks stop the pipeline when something looks wrong |

## How it works

```mermaid
flowchart LR
  A[Elia open data] --> B[Download] --> C[Clean] --> D[(MySQL)] --> E[Summary tables] --> F[Dashboard]
```

1. **Download** the latest data from Elia
2. **Clean** it: consistent times and units, no duplicates
3. **Store** it in a MySQL database
4. **Summarise** it into easy-to-read tables
5. **Check** the results automatically

Airflow runs these five steps every day.

## Tools

| Tool | Used for |
|---|---|
| Python, Polars | Downloading and cleaning data |
| MySQL | Storing data |
| SQL | Summary tables and quality checks |
| Airflow | Daily scheduling |
| Docker | Same setup on any computer |
| GitHub Actions, pytest | Automatic testing |

## Results

> Fill in after your first full run.

- Wind forecasts were off by an average of **[X] MW ([Y]%)**; solar by **[X] MW ([Y]%)**
- Errors are largest around **[hour / season]**
- The pipeline processes **[N] rows in [N] minutes** and runs daily without manual work

## Run it yourself

You need Docker and Python 3.11+.

```bash
git clone https://github.com/<your-username>/belgian-energy-forecast-monitor.git
cd belgian-energy-forecast-monitor
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
docker compose up -d                                  # starts MySQL
python -m energy_monitor.run all --from 2025-01-01 --to 2025-02-01
```

To run it on a daily schedule with Airflow, see [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md).

## Project layout

```
sql/         database setup, summary tables, quality checks
src/         download, clean, load (Python)
airflow/     the daily schedule
tests/       automatic tests
dashboard/   dashboard notes and screenshot
```

## What I'd add next

Weather data to explain the errors, cloud storage, dbt for the SQL layer, and alerts when
accuracy drops.

## About

Built by Patricio Alvarez ·[ www.linkedin.com/in/patricio-l-alvarez ]  · [patrick.2697@hotmail.com]
