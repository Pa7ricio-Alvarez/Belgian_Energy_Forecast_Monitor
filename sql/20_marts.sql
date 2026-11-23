-- Summary table 1: how accurate was the forecast on each day?
-- pct_error = total absolute error as a % of total actual production.
-- (It avoids dividing by zero at night, when solar production is 0.)
DROP TABLE IF EXISTS marts.mart_daily_accuracy;
CREATE TABLE marts.mart_daily_accuracy AS
SELECT
    local_date,
    source,
    COUNT(*)                                              AS n_quarter_hours,
    ROUND(AVG(measured_mw), 1)                            AS avg_actual_mw,
    ROUND(AVG(abs_error_mw), 1)                           AS mean_abs_error_mw,
    ROUND(AVG(error_mw), 1)                               AS bias_mw,
    ROUND(100 * SUM(abs_error_mw) / NULLIF(SUM(measured_mw), 0), 1) AS pct_error
FROM staging.v_forecast_errors
GROUP BY local_date, source;

-- Summary table 2: at which hour of the day are forecasts worst?
DROP TABLE IF EXISTS marts.mart_hourly_profile;
CREATE TABLE marts.mart_hourly_profile AS
SELECT
    source,
    local_hour,
    COUNT(*)                                              AS n_quarter_hours,
    ROUND(AVG(measured_mw), 1)                            AS avg_actual_mw,
    ROUND(AVG(abs_error_mw), 1)                           AS mean_abs_error_mw,
    ROUND(AVG(error_mw), 1)                               AS bias_mw,
    ROUND(100 * SUM(abs_error_mw) / NULLIF(SUM(measured_mw), 0), 1) AS pct_error
FROM staging.v_forecast_errors
GROUP BY source, local_hour;
