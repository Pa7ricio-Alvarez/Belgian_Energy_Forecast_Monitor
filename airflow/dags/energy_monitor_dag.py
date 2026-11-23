"""Daily pipeline: download -> clean -> load -> build summary tables -> check quality.

Every run re-loads the last 3 days, because Elia revises its recent measurements.
Loading is repeatable, so re-loading is safe.
"""
from datetime import datetime, timedelta

try:  # Airflow 3
    from airflow.sdk import dag, task
except ImportError:  # Airflow 2
    from airflow.decorators import dag, task

REFRESH_DAYS = 3


@dag(
    dag_id="energy_monitor",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["energy"],
)
def energy_monitor():
    @task
    def ingest(source: str, data_interval_end=None) -> str:
        # Imported inside the task so Airflow can read this file even before the code is mounted.
        from energy_monitor.run import ingest_range

        end = data_interval_end.date()
        ingest_range(source, end - timedelta(days=REFRESH_DAYS), end)
        return source

    @task
    def build_models():
        from energy_monitor.run import build_models as build

        build()

    @task
    def check_quality():
        from energy_monitor.run import check_quality as check

        check()

    ingested = ingest.expand(source=["wind", "solar"])
    ingested >> build_models() >> check_quality()


energy_monitor()
