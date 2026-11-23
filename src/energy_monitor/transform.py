"""Step 2 - TRANSFORM: clean the raw Elia file with Polars.

Result: a tidy table that matches raw.observations in MySQL.
"""
from pathlib import Path

import polars as pl

from . import config

OUTPUT_COLUMNS = [
    "ts_utc", "source", "series_key", "region", "local_date", "local_hour",
    "measured_mw", "forecast_dayahead_mw", "forecast_latest_mw", "monitored_capacity_mw",
]
NUMERIC = ["measured_mw", "forecast_dayahead_mw", "forecast_latest_mw", "monitored_capacity_mw"]

SCHEMA = {
    "ts_utc": pl.Datetime, "source": pl.Utf8, "series_key": pl.Utf8, "region": pl.Utf8,
    "local_date": pl.Date, "local_hour": pl.Int8,
    "measured_mw": pl.Float64, "forecast_dayahead_mw": pl.Float64,
    "forecast_latest_mw": pl.Float64, "monitored_capacity_mw": pl.Float64,
}


def empty_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=SCHEMA)


def read_raw(path: Path) -> pl.DataFrame:
    """Read a downloaded CSV. Everything is read as text first, converted below."""
    try:
        return pl.read_csv(path, separator=";", infer_schema_length=0)
    except pl.exceptions.NoDataError:
        return pl.DataFrame()


def standardise(df: pl.DataFrame, source: str) -> pl.DataFrame:
    """Rename columns, fix times and numbers, filter series, remove duplicates."""
    if df.height == 0:
        return empty_frame()

    # 1. Find the columns we need
    mapping = {}
    for standard, candidates in config.COLUMN_CANDIDATES.items():
        for candidate in candidates:
            if candidate in df.columns:
                mapping[standard] = candidate
                break
    missing = [name for name in config.REQUIRED if name not in mapping]
    if missing:
        raise ValueError(
            f"[{source}] could not find columns for {missing}. "
            f"Columns in the file: {df.columns}. Update COLUMN_CANDIDATES in config.py."
        )

    # 2. Keep only the series we want (avoids counting the same power twice)
    rows_before = df.height
    for column, allowed in config.FILTERS.get(source, {}).items():
        if column in df.columns:
            wanted = [value.lower() for value in allowed]
            df = df.filter(pl.col(column).str.to_lowercase().is_in(wanted))
    if df.height == 0:
        raise ValueError(
            f"[{source}] filters removed all {rows_before} rows. Check FILTERS in config.py "
            f"(run `inspect {source}` to see the values that exist)."
        )

    # 3. Series key: combines the columns that identify one production series
    present = [c for c in config.SERIES_COLUMNS if c in df.columns]
    series_key = (
        pl.concat_str([pl.col(c).fill_null("n/a") for c in present], separator="|")
        if present else pl.lit("all")
    )
    region = pl.col("region") if "region" in df.columns else pl.lit("n/a")

    # 4. Times: store UTC (no daylight-saving problems), and also the Brussels date and hour
    ts_utc = pl.col(mapping["ts_utc"]).str.to_datetime(time_zone="UTC")
    local = ts_utc.dt.convert_time_zone(config.LOCAL_TZ)

    # 5. Numbers (optional columns become empty values)
    numbers = []
    for name in NUMERIC:
        if name in mapping:
            numbers.append(pl.col(mapping[name]).cast(pl.Float64, strict=False).alias(name))
        else:
            numbers.append(pl.lit(None, dtype=pl.Float64).alias(name))

    out = df.select(
        ts_utc.dt.replace_time_zone(None).alias("ts_utc"),
        pl.lit(source).alias("source"),
        series_key.alias("series_key"),
        region.alias("region"),
        local.dt.date().alias("local_date"),
        local.dt.hour().cast(pl.Int8).alias("local_hour"),
        *numbers,
    )
    out = out.with_columns(pl.col(NUMERIC).fill_nan(None))

    # 6. Remove duplicates (keep the latest line for the same time + series)
    out = out.unique(subset=["ts_utc", "source", "series_key"], keep="last", maintain_order=True)
    return out.select(OUTPUT_COLUMNS)
