from datetime import date

from energy_monitor import extract


def test_month_chunks_split_on_month_boundaries():
    chunks = list(extract.month_chunks(date(2025, 1, 15), date(2025, 3, 2)))
    assert chunks == [
        (date(2025, 1, 15), date(2025, 2, 1)),
        (date(2025, 2, 1), date(2025, 3, 1)),
        (date(2025, 3, 1), date(2025, 3, 2)),
    ]


def test_month_chunks_single_day():
    assert list(extract.month_chunks(date(2025, 5, 1), date(2025, 5, 2))) == [
        (date(2025, 5, 1), date(2025, 5, 2))
    ]


def test_month_chunks_year_end():
    chunks = list(extract.month_chunks(date(2024, 12, 20), date(2025, 1, 5)))
    assert chunks == [
        (date(2024, 12, 20), date(2025, 1, 1)),
        (date(2025, 1, 1), date(2025, 1, 5)),
    ]


def test_build_params_end_date_is_exclusive():
    params = extract.build_params(date(2025, 1, 1), date(2025, 1, 8))
    assert "date'2025-01-01'" in params["where"]
    assert "< date'2025-01-08'" in params["where"]
    assert params["timezone"] == "UTC"
