-- database/schema/01_dimensions.sql
-- Isolated definitions for static dimension tables under TimescaleDB/PostgreSQL.

-- Pricing Nodes/Zones Dimension Table
CREATE TABLE IF NOT EXISTS dim_pricing_locations (
    location_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('ZONE', 'NODE')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed basic locations (e.g. Zonal Pricing)
INSERT INTO dim_pricing_locations (name, type, description)
VALUES 
    ('ONTARIO_ZONAL_PRICE', 'ZONE', 'Ontario Province-wide Zonal Price average')
ON CONFLICT (name) DO NOTHING;

-- Consumer Pricing Classification
CREATE TABLE IF NOT EXISTS dim_customer_class (
    class_code VARCHAR(1) PRIMARY KEY CHECK (class_code IN ('A', 'B')),
    name VARCHAR(50) NOT NULL,
    description TEXT
);

INSERT INTO dim_customer_class (class_code, name, description)
VALUES
    ('A', 'Class A', 'Coincident Peak Demand Factor (>3MW or 1-3MW opt-in) paying monthly pool-share GA.'),
    ('B', 'Class B', 'Standard volumetric payer paying flat-rate GA ($/MWh).')
ON CONFLICT (class_code) DO NOTHING;
