"""Step 3 - LOAD: write the clean data into MySQL (repeatable, no duplicates)."""
import polars as pl
import pymysql

from . import config
from .transform import OUTPUT_COLUMNS

_placeholders = ", ".join(["%s"] * len(OUTPUT_COLUMNS))
_updates = ", ".join(
    f"{c}=VALUES({c})" for c in OUTPUT_COLUMNS if c not in ("ts_utc", "source", "series_key")
)
UPSERT_SQL = (
    f"INSERT INTO raw.observations ({', '.join(OUTPUT_COLUMNS)}) VALUES ({_placeholders}) "
    f"ON DUPLICATE KEY UPDATE {_updates}"
)


def connect() -> pymysql.connections.Connection:
    return pymysql.connect(**config.DB, autocommit=False)


def upsert(df: pl.DataFrame, conn, batch_size: int = 5000) -> int:
    """Insert new rows and update existing ones. Running twice gives the same result."""
    rows = df.select(OUTPUT_COLUMNS).rows()
    with conn.cursor() as cursor:
        for i in range(0, len(rows), batch_size):
            cursor.executemany(UPSERT_SQL, rows[i : i + batch_size])
    conn.commit()
    return len(rows)


def log_run(conn, source: str, start, end, rows: int, status: str, message: str = "") -> None:
    """Write one line per run into raw.pipeline_runs (a simple audit trail)."""
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO raw.pipeline_runs (source, date_from, date_to, rows_loaded, status, message) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (source, start, end, rows, status, message[:500]),
        )
    conn.commit()
