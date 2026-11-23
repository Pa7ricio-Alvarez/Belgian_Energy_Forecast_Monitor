import polars as pl
import pytest

from energy_monitor import transform


def make_raw(rows):
    """Build a raw-looking table: everything is text, like a freshly read CSV."""
    columns = ["datetime", "region", "offshoreonshore", "measured",
               "dayaheadforecast", "mostrecentforecast", "monitoredcapacity"]
    return pl.DataFrame(rows, schema={c: pl.Utf8 for c in columns}, orient="row")


def row(ts, region="Belgium", kind="Onshore", measured="100", dayahead="110"):
    return (ts, region, kind, measured, dayahead, "105", "500")


def test_output_has_expected_columns_and_types():
    out = transform.standardise(make_raw([row("2025-01-15T10:00:00+00:00")]), "wind")
    assert out.columns == transform.OUTPUT_COLUMNS
    assert out["measured_mw"].dtype == pl.Float64
    assert out["source"][0] == "wind"
    assert out["series_key"][0] == "Belgium|Onshore"


def test_local_hour_follows_brussels_time_in_winter_and_summer():
    winter = transform.standardise(make_raw([row("2025-01-15T10:00:00+00:00")]), "wind")
    summer = transform.standardise(make_raw([row("2025-07-01T10:00:00+00:00")]), "wind")
    assert winter["local_hour"][0] == 11   # UTC+1
    assert summer["local_hour"][0] == 12   # UTC+2


def test_daylight_saving_switch_day():
    # 30 March 2025: clocks jump from 02:00 to 03:00 in Brussels.
    rows = [row("2025-03-30T00:30:00+00:00"), row("2025-03-30T01:30:00+00:00")]
    out = transform.standardise(make_raw(rows), "wind")
    assert out["local_hour"].to_list() == [1, 3]


def test_duplicates_keep_latest_value():
    rows = [row("2025-01-15T10:00:00+00:00", measured="100"),
            row("2025-01-15T10:00:00+00:00", measured="120")]
    out = transform.standardise(make_raw(rows), "wind")
    assert out.height == 1
    assert out["measured_mw"][0] == 120.0


def test_series_outside_filter_are_dropped():
    rows = [row("2025-01-15T10:00:00+00:00", region="Belgium"),
            row("2025-01-15T10:00:00+00:00", region="Flanders")]
    out = transform.standardise(make_raw(rows), "wind")
    assert out["region"].to_list() == ["Belgium"]


def test_empty_values_become_nulls_not_zeros():
    rows = [row("2025-01-15T10:00:00+00:00", measured="NaN"),
            row("2025-01-15T10:15:00+00:00", measured="")]
    out = transform.standardise(make_raw(rows), "wind")
    assert out["measured_mw"].null_count() == 2


def test_missing_required_column_gives_helpful_error():
    bad = pl.DataFrame({"datetime": ["2025-01-15T10:00:00+00:00"], "other": ["1"]})
    with pytest.raises(ValueError, match="COLUMN_CANDIDATES"):
        transform.standardise(bad, "wind")


def test_filter_removing_everything_gives_helpful_error():
    with pytest.raises(ValueError, match="FILTERS"):
        transform.standardise(make_raw([row("2025-01-15T10:00:00+00:00", region="Mars")]), "wind")


def test_empty_input_returns_empty_table():
    assert transform.standardise(pl.DataFrame(), "wind").height == 0
