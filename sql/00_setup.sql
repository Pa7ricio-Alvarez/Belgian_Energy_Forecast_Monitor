-- Runs automatically the first time the MySQL container starts.
-- Creates three "layers" (MySQL calls them databases):
--   raw      = cleaned data exactly as loaded
--   staging  = views that prepare the data
--   marts    = final summary tables used for reporting

CREATE DATABASE IF NOT EXISTS raw;
CREATE DATABASE IF NOT EXISTS staging;
CREATE DATABASE IF NOT EXISTS marts;

GRANT ALL PRIVILEGES ON raw.* TO 'energy'@'%';
GRANT ALL PRIVILEGES ON staging.* TO 'energy'@'%';
GRANT ALL PRIVILEGES ON marts.* TO 'energy'@'%';

-- One row per 15 minutes, per source (wind/solar) and per production series.
-- The primary key is what makes loading repeatable: loading the same row again
-- updates it instead of creating a duplicate.
CREATE TABLE IF NOT EXISTS raw.observations (
    ts_utc                 DATETIME     NOT NULL,   -- time in UTC
    source                 VARCHAR(10)  NOT NULL,   -- 'wind' or 'solar'
    series_key             VARCHAR(100) NOT NULL,   -- identifies the production series
    region                 VARCHAR(50),
    local_date             DATE         NOT NULL,   -- date in Brussels time
    local_hour             TINYINT      NOT NULL,   -- hour (0-23) in Brussels time
    measured_mw            DOUBLE,                  -- actual production (MW)
    forecast_dayahead_mw   DOUBLE,                  -- forecast made the day before (MW)
    forecast_latest_mw     DOUBLE,                  -- most recent forecast (MW)
    monitored_capacity_mw  DOUBLE,                  -- installed capacity watched by Elia (MW)
    loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (ts_utc, source, series_key),
    KEY idx_local_date (local_date)
);

-- Audit trail: one row for every pipeline run.
CREATE TABLE IF NOT EXISTS raw.pipeline_runs (
    run_id       INT AUTO_INCREMENT PRIMARY KEY,
    run_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source       VARCHAR(10),
    date_from    DATE,
    date_to      DATE,
    rows_loaded  INT,
    status       VARCHAR(10),
    message      VARCHAR(500)
);
