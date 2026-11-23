"""Command line entry point.

    python -m energy_monitor.run inspect wind
    python -m energy_monitor.run all --from 2025-01-01 --to 2025-02-01
    python -m energy_monitor.run export
"""
import argparse
import csv
from datetime import date, timedelta

import polars as pl

from . import config, extract, load, modeling, transform


def ingest_range(source: str, start: date, end: date, conn=None) -> int:
    """Extract -> transform -> load for one source and one date range."""
    own_connection = conn is None
    conn = conn or load.connect()
    rows = 0
    try:
        paths = extract.download(source, start, end)
        frames = [transform.standardise(transform.read_raw(p), source) for p in paths]
        df = pl.concat(frames) if frames else transform.empty_frame()
        rows = load.upsert(df, conn)
        load.log_run(conn, source, start, end, rows, "success")
        print(f"[{source}] {rows} rows loaded")
        return rows
    except Exception as error:
        conn.rollback()
        load.log_run(conn, source, start, end, rows, "failed", str(error))
        raise
    finally:
        if own_connection:
            conn.close()


def build_models() -> None:
    conn = load.connect()
    try:
        modeling.build_models(conn)
    finally:
        conn.close()


def check_quality() -> None:
    conn = load.connect()
    try:
        modeling.run_quality_checks(conn)
    finally:
        conn.close()


def export_marts() -> None:
    """Write the summary tables to CSV (for Tableau Public)."""
    out_dir = config.DATA_DIR / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = load.connect()
    try:
        with conn.cursor() as cursor:
            for table in ("mart_daily_accuracy", "mart_hourly_profile"):
                cursor.execute(f"SELECT * FROM marts.{table}")
                headers = [d[0] for d in cursor.description]
                path = out_dir / f"{table}.csv"
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(cursor.fetchall())
                print(f"Exported {path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="energy_monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect", help="show columns and values of a source")
    p.add_argument("source", choices=config.SOURCES)

    for name, help_text in [("ingest", "download, clean and load"),
                            ("all", "ingest + build tables + quality checks")]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--from", dest="start", type=date.fromisoformat)
        p.add_argument("--to", dest="end", type=date.fromisoformat, help="exclusive")
        p.add_argument("--sources", nargs="+", default=list(config.SOURCES),
                       choices=config.SOURCES)

    sub.add_parser("model", help="rebuild summary tables and run checks")
    sub.add_parser("export", help="export summary tables to CSV")

    args = parser.parse_args()

    if args.command == "inspect":
        extract.inspect(args.source)
    elif args.command in ("ingest", "all"):
        end = args.end or date.today()
        start = args.start or end - timedelta(days=3)
        for source in args.sources:
            ingest_range(source, start, end)
        if args.command == "all":
            build_models()
            check_quality()
    elif args.command == "model":
        build_models()
        check_quality()
    elif args.command == "export":
        export_marts()


if __name__ == "__main__":
    main()
