-- PostgreSQL schema setup for IoT data pipeline
-- This script creates the necessary tables for sensor data and daily aggregation.

-- Create table for raw sensor data
CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temperature DOUBLE PRECISION
);

-- Create table for daily aggregated sensor stats
CREATE TABLE IF NOT EXISTS daily_sensor_stats (
    date DATE NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    avg_temperature DOUBLE PRECISION,
    count_records INT,
    PRIMARY KEY (date, sensor_id)
);
