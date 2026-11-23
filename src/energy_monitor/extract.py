"""Step 1 - EXTRACT: download raw data from the Elia Open Data API.

Result: one CSV file per month and source in data/raw/<source>/.
"""
import csv
import io
import time
from datetime import date, timedelta
from pathlib import Path

import requests

from . import config


def month_chunks(start: date, end: date):
    """Split [start, end) into pieces that do not cross a month boundary."""
    current = start
    while current < end:
        next_month = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
        chunk_end = min(next_month, end)
        yield current, chunk_end
        current = chunk_end


def build_params(start: date, end: date, limit: int | None = None) -> dict:
    """Query parameters for the Opendatasoft 'exports' endpoint (end date is exclusive)."""
    field = config.DATETIME_FIELD
    params = {
        "where": f"{field} >= date'{start}' AND {field} < date'{end}'",
        "order_by": field,
        "delimiter": ";",
        "timezone": "UTC",
    }
    if limit:
        params["limit"] = limit
    return params


def _get(url: str, params: dict, attempts: int = 3) -> requests.Response:
    """GET with simple retries (waits 2, 4, 8 seconds between attempts)."""
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=180)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")
            return response
        except (requests.RequestException, RuntimeError) as error:
            if attempt == attempts:
                raise
            wait = 2**attempt
            print(f"  attempt {attempt} failed ({error}); retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def _url(source: str) -> str:
    return f"{config.BASE_URL}/{config.SOURCES[source]}/exports/csv"


def download(source: str, start: date, end: date) -> list[Path]:
    """Download [start, end) for one source. Returns the list of saved files."""
    folder = config.DATA_DIR / "raw" / source
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for chunk_start, chunk_end in month_chunks(start, end):
        path = folder / f"{chunk_start}_{chunk_end}.csv"
        print(f"[{source}] downloading {chunk_start} -> {chunk_end}")
        response = _get(_url(source), build_params(chunk_start, chunk_end))
        path.write_bytes(response.content)
        paths.append(path)
    return paths


def inspect(source: str) -> None:
    """Print the column names and the distinct values of the 'series' columns.

    Use this first, to confirm that config.py matches the real data.
    """
    end = date.today()
    start = end - timedelta(days=7)
    response = _get(_url(source), build_params(start, end, limit=2000))
    rows = list(csv.DictReader(io.StringIO(response.text), delimiter=";"))
    if not rows:
        print("No rows returned for the last 7 days. Try again later or widen the dates.")
        return
    print(f"\n== {source} ({config.SOURCES[source]}) ==")
    print("Columns:", ", ".join(rows[0].keys()))
    for column in config.SERIES_COLUMNS:
        if column in rows[0]:
            values = sorted({row[column] for row in rows})
            print(f"Values of '{column}':", values)
    print("\nFirst row:")
    for key, value in rows[0].items():
        print(f"  {key}: {value}")
