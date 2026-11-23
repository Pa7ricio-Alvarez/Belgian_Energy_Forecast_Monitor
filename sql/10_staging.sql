-- Total production per 15 minutes: adds up the series (e.g. offshore + onshore wind).
-- Only rows that have BOTH an actual value and a day-ahead forecast can be compared.
CREATE OR REPLACE VIEW staging.v_total_production AS
SELECT
    ts_utc,
    local_date,
    local_hour,
    source,
    SUM(measured_mw)           AS measured_mw,
    SUM(forecast_dayahead_mw)  AS forecast_mw
FROM raw.observations
WHERE measured_mw IS NOT NULL
  AND forecast_dayahead_mw IS NOT NULL
GROUP BY ts_utc, local_date, local_hour, source;

-- Forecast error: positive = forecast was too high, negative = too low.
CREATE OR REPLACE VIEW staging.v_forecast_errors AS
SELECT
    ts_utc,
    local_date,
    local_hour,
    source,
    measured_mw,
    forecast_mw,
    forecast_mw - measured_mw       AS error_mw,
    ABS(forecast_mw - measured_mw)  AS abs_error_mw
FROM staging.v_total_production;
