# scripts/import_excel.py
"""
Import data from Excel file into the database.
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
from integrations.excel_importer import ExcelImporter
from backend.services.cashflow_service import CashFlowService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SCHEMA_NAME = os.getenv("DB_SCHEMA", "more_house")


def import_data(file_path: str, clear_existing: bool = False):
    """
    Import data from Excel file into database.

    Args:
        file_path: Path to the Excel file
        clear_existing: If True, clear existing data before import
    """
    connection_string = os.getenv("TIMESCALE_SERVICE_URL")
    if not connection_string:
        logger.error("TIMESCALE_SERVICE_URL not set")
        sys.exit(1)

    # Load Excel data
    logger.info(f"Loading Excel file: {file_path}")
    importer = ExcelImporter(file_path)
    rooms, contracts = importer.import_booked_units()

    logger.info(f"Found {len(rooms)} rooms and {len(contracts)} contracts")

    try:
        conn = psycopg2.connect(dsn=connection_string)
        cursor = conn.cursor()

        # Set schema
        cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")

        if clear_existing:
            logger.info("Clearing existing data...")
            cursor.execute(f"DELETE FROM {SCHEMA_NAME}.payment_schedule")
            cursor.execute(f"DELETE FROM {SCHEMA_NAME}.contracts")
            cursor.execute(f"DELETE FROM {SCHEMA_NAME}.rooms")
            conn.commit()

        # Insert rooms
        logger.info("Inserting rooms...")
        for room in rooms:
            cursor.execute("""
                INSERT INTO rooms (room_id, floor, category, sqm, weekly_rate)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (room_id) DO UPDATE SET
                    floor = EXCLUDED.floor,
                    category = EXCLUDED.category,
                    sqm = EXCLUDED.sqm,
                    weekly_rate = EXCLUDED.weekly_rate
            """, (
                room['room_id'],
                room['floor'],
                room['category'],
                room['sqm'],
                room['weekly_rate']
            ))
        conn.commit()
        logger.info(f"Inserted/updated {len(rooms)} rooms")

        # Insert contracts and generate payment schedules
        logger.info("Inserting contracts...")
        contracts_inserted = 0
        payments_inserted = 0

        for contract in contracts:
            cursor.execute("""
                INSERT INTO contracts (
                    room_id, resident_name, start_date, end_date,
                    weekly_rate, total_value, weeks_booked,
                    payment_plan, status, nationality, university, source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                contract['room_id'],
                contract['resident_name'],
                contract['start_date'],
                contract['end_date'],
                contract['weekly_rate'],
                contract['total_value'],
                contract['weeks_booked'],
                contract['payment_plan'],
                contract['status'],
                contract.get('nationality'),
                contract.get('university'),
                contract.get('source')
            ))

            contract_id = cursor.fetchone()[0]
            contracts_inserted += 1

            # Generate payment schedule
            payments = CashFlowService.generate_payment_schedule(
                contract_id=contract_id,
                total_value=contract['total_value'],
                start_date=contract['start_date'],
                end_date=contract['end_date'],
                payment_plan=contract['payment_plan']
            )

            for payment in payments:
                cursor.execute("""
                    INSERT INTO payment_schedule (
                        contract_id, due_date, amount, payment_type, status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    payment['contract_id'],
                    payment['due_date'],
                    payment['amount'],
                    payment['payment_type'],
                    payment['status']
                ))
                payments_inserted += 1

        conn.commit()
        logger.info(f"Inserted {contracts_inserted} contracts")
        logger.info(f"Generated {payments_inserted} payment schedule entries")

        # Summary
        cursor.execute("SELECT COUNT(*) FROM rooms")
        room_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM contracts")
        contract_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM payment_schedule")
        payment_count = cursor.fetchone()[0]

        logger.info(f"\nDatabase summary:")
        logger.info(f"  Rooms: {room_count}")
        logger.info(f"  Contracts: {contract_count}")
        logger.info(f"  Payment schedule entries: {payment_count}")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import Excel data into database")
    parser.add_argument("file", help="Path to Excel file")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before import")
    args = parser.parse_args()

    import_data(args.file, clear_existing=args.clear)
