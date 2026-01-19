# scripts/init_db.py
"""
Database initialization script for More House.

Creates the more_house schema and all required tables.
Run this once to set up the database.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SCHEMA_NAME = os.getenv("DB_SCHEMA", "more_house")

# SQL to create schema and tables
CREATE_SCHEMA_SQL = f"""
-- Create schema
CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};

-- Set search path
SET search_path TO {SCHEMA_NAME}, public;
"""

CREATE_TABLES_SQL = f"""
-- Rooms table
CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.rooms (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(20) UNIQUE NOT NULL,
    floor VARCHAR(10),
    category VARCHAR(50),
    sqm DECIMAL(6,2),
    weekly_rate DECIMAL(10,2),
    mattress_size VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contracts table
CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.contracts (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(20) NOT NULL REFERENCES {SCHEMA_NAME}.rooms(room_id),
    resident_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    weekly_rate DECIMAL(10,2),
    total_value DECIMAL(12,2),
    weeks_booked DECIMAL(6,2),
    payment_plan VARCHAR(50),
    status VARCHAR(30) DEFAULT 'active',
    nationality VARCHAR(100),
    university VARCHAR(200),
    level_of_study VARCHAR(100),
    source VARCHAR(100),
    lead_source VARCHAR(100),
    monday_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_dates CHECK (end_date >= start_date)
);

-- Payment schedule table (expected payments)
CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.payment_schedule (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES {SCHEMA_NAME}.contracts(id),
    due_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_type VARCHAR(30) DEFAULT 'rent',
    status VARCHAR(20) DEFAULT 'pending',
    paid_date DATE,
    paid_amount DECIMAL(10,2),
    monday_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OPEX budget table
CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.opex_budget (
    id SERIAL PRIMARY KEY,
    month_date DATE NOT NULL,
    category VARCHAR(100),
    amount DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_contracts_room_id ON {SCHEMA_NAME}.contracts(room_id);
CREATE INDEX IF NOT EXISTS idx_contracts_dates ON {SCHEMA_NAME}.contracts(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON {SCHEMA_NAME}.contracts(status);
CREATE INDEX IF NOT EXISTS idx_payment_schedule_due_date ON {SCHEMA_NAME}.payment_schedule(due_date);
CREATE INDEX IF NOT EXISTS idx_payment_schedule_status ON {SCHEMA_NAME}.payment_schedule(status);
CREATE INDEX IF NOT EXISTS idx_payment_schedule_contract ON {SCHEMA_NAME}.payment_schedule(contract_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION {SCHEMA_NAME}.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_rooms_updated_at ON {SCHEMA_NAME}.rooms;
CREATE TRIGGER update_rooms_updated_at
    BEFORE UPDATE ON {SCHEMA_NAME}.rooms
    FOR EACH ROW EXECUTE FUNCTION {SCHEMA_NAME}.update_updated_at_column();

DROP TRIGGER IF EXISTS update_contracts_updated_at ON {SCHEMA_NAME}.contracts;
CREATE TRIGGER update_contracts_updated_at
    BEFORE UPDATE ON {SCHEMA_NAME}.contracts
    FOR EACH ROW EXECUTE FUNCTION {SCHEMA_NAME}.update_updated_at_column();

DROP TRIGGER IF EXISTS update_payment_schedule_updated_at ON {SCHEMA_NAME}.payment_schedule;
CREATE TRIGGER update_payment_schedule_updated_at
    BEFORE UPDATE ON {SCHEMA_NAME}.payment_schedule
    FOR EACH ROW EXECUTE FUNCTION {SCHEMA_NAME}.update_updated_at_column();
"""


def init_database():
    """Initialize the database schema and tables."""
    connection_string = os.getenv("TIMESCALE_SERVICE_URL")
    if not connection_string:
        logger.error("TIMESCALE_SERVICE_URL not set in environment")
        sys.exit(1)

    try:
        logger.info("Connecting to database...")
        conn = psycopg2.connect(dsn=connection_string)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info(f"Creating schema: {SCHEMA_NAME}")
        cursor.execute(CREATE_SCHEMA_SQL)

        logger.info("Creating tables...")
        cursor.execute(CREATE_TABLES_SQL)

        logger.info("Database initialization complete!")

        # Verify tables were created
        cursor.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{SCHEMA_NAME}'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[t[0] for t in tables]}")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)


def drop_schema():
    """Drop the entire schema (use with caution!)."""
    connection_string = os.getenv("TIMESCALE_SERVICE_URL")
    if not connection_string:
        logger.error("TIMESCALE_SERVICE_URL not set")
        sys.exit(1)

    confirm = input(f"This will DROP the entire '{SCHEMA_NAME}' schema. Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        logger.info("Aborted.")
        return

    try:
        conn = psycopg2.connect(dsn=connection_string)
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute(f"DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE")
        logger.info(f"Schema '{SCHEMA_NAME}' dropped.")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="More House Database Management")
    parser.add_argument("--drop", action="store_true", help="Drop the schema (dangerous!)")
    args = parser.parse_args()

    if args.drop:
        drop_schema()
    else:
        init_database()
