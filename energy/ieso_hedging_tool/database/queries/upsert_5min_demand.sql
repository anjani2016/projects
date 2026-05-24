-- database/queries/upsert_5min_demand.sql
-- Idempotent upsert script for 5-minute system demand metrics.

INSERT INTO system_demand (timestamp, demand_mw)
VALUES (:timestamp, :demand_mw)
ON CONFLICT (timestamp) 
DO UPDATE SET demand_mw = EXCLUDED.demand_mw;
