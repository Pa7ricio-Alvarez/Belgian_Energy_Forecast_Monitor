"""Central settings. If Elia renames a column, this is the only file you edit."""
import os
from pathlib import Path

# --- Where the data comes from (Elia Open Data, Opendatasoft API v2.1) -------------------
BASE_URL = "https://opendata.elia.be/api/explore/v2.1/catalog/datasets"
SOURCES = {
    "wind": "ods031",   # Wind power production estimation and forecast (historical)
    "solar": "ods032",  # Photovoltaic power production estimation and forecast (historical)
}
DATETIME_FIELD = "datetime"  # name of the timestamp column, used to filter by date

# --- Column names -------------------------------------------------------------------------
# Left: our standard name. Right: names we look for in the Elia file (first match wins).
# Run `python -m energy_monitor.run inspect wind` to see the real names and adjust here.
COLUMN_CANDIDATES = {
    "ts_utc": ["datetime"],
    "measured_mw": ["measured"],
    "forecast_dayahead_mw": ["dayaheadforecast"],
    "forecast_latest_mw": ["mostrecentforecast"],
    "monitored_capacity_mw": ["monitoredcapacity"],
}
REQUIRED = ["ts_utc", "measured_mw", "forecast_dayahead_mw"]

# Columns that identify ONE production series (for example offshore vs onshore wind).
# Those that exist in the file are joined into a single `series_key`.
SERIES_COLUMNS = ["region", "offshoreonshore", "gridconnectiontype"]

# Keep only these values, so that we never count the same electricity twice.
# Run `inspect` to see the possible values, then adjust.
FILTERS = {
    "wind": {"region": ["Belgium"]},
    "solar": {"region": ["Belgium"]},
}

LOCAL_TZ = "Europe/Brussels"

# --- Paths and database -------------------------------------------------------------------
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
SQL_DIR = Path(__file__).resolve().parents[2] / "sql"

DB = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "energy"),
    "password": os.getenv("MYSQL_PASSWORD", "energy_pw"),
    "database": "raw",
}
