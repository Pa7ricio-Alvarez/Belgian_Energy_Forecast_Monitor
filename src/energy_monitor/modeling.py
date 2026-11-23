"""Step 4 - MODEL and CHECK: run the SQL files that build the summary tables and test them."""
from . import config


class QualityCheckError(Exception):
    pass


def _statements(path):
    """Split a .sql file into single statements (ignores comment-only pieces)."""
    for piece in path.read_text(encoding="utf-8").split(";"):
        code = "\n".join(line for line in piece.splitlines() if not line.strip().startswith("--"))
        if code.strip():
            yield piece.strip()


def run_sql_file(conn, filename: str) -> None:
    with conn.cursor() as cursor:
        for statement in _statements(config.SQL_DIR / filename):
            cursor.execute(statement)
    conn.commit()


def build_models(conn) -> None:
    """Create the staging views and the summary (mart) tables."""
    run_sql_file(conn, "10_staging.sql")
    run_sql_file(conn, "20_marts.sql")
    print("Summary tables rebuilt.")


def run_quality_checks(conn) -> None:
    """Each check returns (name, number_of_bad_rows). Any bad row stops the pipeline."""
    failures = []
    with conn.cursor() as cursor:
        for statement in _statements(config.SQL_DIR / "90_quality_checks.sql"):
            cursor.execute(statement)
            name, bad_rows = cursor.fetchone()
            status = "OK  " if bad_rows == 0 else "FAIL"
            print(f"  [{status}] {name}: {bad_rows}")
            if bad_rows:
                failures.append(f"{name} ({bad_rows})")
    if failures:
        raise QualityCheckError("Quality checks failed: " + ", ".join(failures))
