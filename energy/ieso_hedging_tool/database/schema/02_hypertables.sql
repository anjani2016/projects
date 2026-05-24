-- database/schema/02_hypertables.sql
-- Ingest high-frequency time series tables for pricing and demand, tailored for TimescaleDB extensions.

-- 5-Minute and Hourly pricing hypertables
CREATE TABLE IF NOT EXISTS location_prices (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    ontario_price NUMERIC(10, 4) NOT NULL,
    energy_loss NUMERIC(10, 4) DEFAULT 0.0,
    energy_congestion NUMERIC(10, 4) DEFAULT 0.0,
    PRIMARY KEY (timestamp, location_name)
);

-- Turn into TimescaleDB hypertable if extension is available
-- SELECT create_hypertable('location_prices', 'timestamp', if_not_exists => TRUE);

-- High frequency demand hypertable
CREATE TABLE IF NOT EXISTS system_demand (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL PRIMARY KEY,
    demand_mw NUMERIC(12, 4) NOT NULL
);

-- SELECT create_hypertable('system_demand', 'timestamp', if_not_exists => TRUE);
