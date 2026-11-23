# Dashboard

1. Export the summary tables to CSV:
   `python -m energy_monitor.run export`
   (files appear in `data/exports/`)
2. Open Tableau Public, connect to the two CSV files, and build three views:
   - Daily forecast error over time (`mart_daily_accuracy`)
   - Error by hour of day (`mart_hourly_profile`)
   - Wind vs. solar comparison
3. Publish, then add the link and a screenshot here and in the main README.

![dashboard screenshot](dashboard.png)
