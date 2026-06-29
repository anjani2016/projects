-- database/views/01_hourly_rollups.sql
-- Create an hourly rollup view that aggregates 5-minute ticks into time-weighted hourly averages.

CREATE OR REPLACE VIEW hourly_price_rollups AS
SELECT 
    date_trunc('hour', timestamp) AS hour_timestamp,
    location_name,
    ROUND(AVG(ontario_price), 4) AS avg_hourly_price,
    ROUND(MAX(ontario_price), 4) AS peak_hourly_price,
    ROUND(MIN(ontario_price), 4) AS min_hourly_price,
    ROUND(AVG(energy_loss), 4) AS avg_loss_component,
    ROUND(AVG(energy_congestion), 4) AS avg_congestion_component,
    COUNT(timestamp) AS tick_count -- Useful to ensure data completeness (e.g. should be 12 ticks/hr for 5-min intervals)
FROM location_prices
GROUP BY 1, 2;
