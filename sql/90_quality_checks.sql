-- Each check returns (name, number of bad rows). Zero = pass. Anything else stops the pipeline.

SELECT 'no_negative_production' AS check_name, COUNT(*) AS bad_rows
FROM raw.observations
WHERE measured_mw < 0;

-- If production is far above the installed capacity, series are probably counted twice
-- (look at FILTERS in config.py).
SELECT 'production_not_above_capacity' AS check_name, COUNT(*) AS bad_rows
FROM raw.observations
WHERE monitored_capacity_mw > 0
  AND measured_mw > monitored_capacity_mw * 1.1;

SELECT 'valid_hour_of_day' AS check_name, COUNT(*) AS bad_rows
FROM raw.observations
WHERE local_hour NOT BETWEEN 0 AND 23;

SELECT 'daily_table_not_empty' AS check_name, CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS bad_rows
FROM marts.mart_daily_accuracy;

SELECT 'hourly_table_not_empty' AS check_name, CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS bad_rows
FROM marts.mart_hourly_profile;
