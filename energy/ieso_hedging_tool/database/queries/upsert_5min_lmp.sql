-- database/queries/upsert_5min_lmp.sql
-- Idempotent upsert script for 5-minute Locational Marginal Pricing signals.

INSERT INTO location_prices (timestamp, location_name, ontario_price, energy_loss, energy_congestion)
VALUES (:timestamp, :location_name, :ontario_price, :energy_loss, :energy_congestion)
ON CONFLICT (timestamp, location_name) 
DO UPDATE SET 
    ontario_price = EXCLUDED.ontario_price,
    energy_loss = EXCLUDED.energy_loss,
    energy_congestion = EXCLUDED.energy_congestion;
