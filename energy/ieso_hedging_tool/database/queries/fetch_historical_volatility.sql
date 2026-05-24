-- database/queries/fetch_historical_volatility.sql
-- Calculates rolling standard deviation of HOEP/LMP over past 30 days to measure volatility.

WITH hourly_prices AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_ts,
        location_name,
        AVG(ontario_price) AS avg_price
    FROM location_prices
    WHERE timestamp >= :start_time AND timestamp < :end_time
    GROUP BY 1, 2
)
SELECT 
    hour_ts,
    location_name,
    avg_price,
    -- Calculate moving standard deviation over a 24-hour lookback window
    STDDEV(avg_price) OVER (
        PARTITION BY location_name 
        ORDER BY hour_ts 
        ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
    ) AS volatility_24h,
    -- Calculate moving standard deviation over a 168-hour lookback window (7 days)
    STDDEV(avg_price) OVER (
        PARTITION BY location_name 
        ORDER BY hour_ts 
        ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
    ) AS volatility_168h
FROM hourly_prices
ORDER BY location_name, hour_ts;
