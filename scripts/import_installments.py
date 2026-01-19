# scripts/import_installments.py
"""
Import payment schedule data from Installments.xlsx into the database.

This imports the actual payment due dates and amounts from Monday CRM export.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import psycopg2
from dotenv import load_dotenv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SCHEMA_NAME = os.getenv("DB_SCHEMA", "more_house")


def parse_date(value):
    """Parse date from various formats."""
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except:
            return None
    return None


def import_installments(file_path: str, clear_existing: bool = False):
    """
    Import installments data from Excel.

    The Excel has columns:
    - Name (resident)
    - Unit Booked New (room_id)
    - Gross Income (total contract value)
    - Payment Plan
    - Actual Length of Stay - Start/End
    - Booking Fee Due Date + Amount
    - Installment 1-5 Due Date + Amount
    """
    connection_string = os.getenv("TIMESCALE_SERVICE_URL")
    if not connection_string:
        logger.error("TIMESCALE_SERVICE_URL not set")
        sys.exit(1)

    # Read Excel
    logger.info(f"Reading: {file_path}")
    df = pd.read_excel(file_path, sheet_name=0, header=4)

    logger.info(f"Found {len(df)} records")
    logger.info(f"Columns: {df.columns.tolist()}")

    try:
        conn = psycopg2.connect(dsn=connection_string)
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")

        if clear_existing:
            logger.info("Clearing existing payment schedules...")
            cursor.execute("DELETE FROM payment_schedule")
            cursor.execute("DELETE FROM contracts")
            conn.commit()

        contracts_created = 0
        payments_created = 0
        skipped = 0

        for idx, row in df.iterrows():
            resident_name = str(row.get('Name', '')).strip()
            room_id = str(row.get('Unit Booked New', '')).strip()
            total_value = row.get('Gross Income')
            payment_plan = str(row.get('Payment Plan', '')).strip()
            start_date = parse_date(row.get('Actual Length of Stay - Start'))
            end_date = parse_date(row.get('Actual Length of Stay - End'))

            if not resident_name or not room_id or pd.isna(total_value):
                skipped += 1
                continue

            # Check if room exists, create if not
            cursor.execute(
                "SELECT room_id FROM rooms WHERE room_id = %s",
                (room_id,)
            )
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO rooms (room_id, floor, category)
                    VALUES (%s, %s, %s)
                """, (room_id, 'TBD', 'TBD'))
                logger.info(f"Created room: {room_id}")

            # Create contract
            cursor.execute("""
                INSERT INTO contracts (
                    room_id, resident_name, start_date, end_date,
                    total_value, payment_plan, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'active')
                RETURNING id
            """, (
                room_id,
                resident_name,
                start_date,
                end_date,
                float(total_value) if pd.notna(total_value) else 0,
                payment_plan if payment_plan else 'Unknown'
            ))
            contract_id = cursor.fetchone()[0]
            contracts_created += 1

            # Insert payment schedule entries
            # Booking Fee (installment_number = 0)
            booking_fee_due = parse_date(row.get('📅Booking Fee Due Date'))
            booking_fee_amt = row.get('Booking Fee Payment Amount')
            if pd.notna(booking_fee_amt) and float(booking_fee_amt) > 0:
                cursor.execute("""
                    INSERT INTO payment_schedule (
                        contract_id, installment_number, due_date, amount, status
                    )
                    VALUES (%s, %s, %s, %s, 'pending')
                """, (contract_id, 0, booking_fee_due, float(booking_fee_amt)))
                payments_created += 1

            # Installments 1-5
            for i in range(1, 6):
                due_date_col = f'📅Installment {i} Due Date'
                amount_col = f'Installment {i} Amount'

                due_date = parse_date(row.get(due_date_col))
                amount = row.get(amount_col)

                if pd.notna(amount) and float(amount) > 0:
                    cursor.execute("""
                        INSERT INTO payment_schedule (
                            contract_id, installment_number, due_date, amount, status
                        )
                        VALUES (%s, %s, %s, %s, 'pending')
                    """, (contract_id, i, due_date, float(amount)))
                    payments_created += 1

        conn.commit()

        logger.info(f"\n=== Import Complete ===")
        logger.info(f"Contracts created: {contracts_created}")
        logger.info(f"Payment entries created: {payments_created}")
        logger.info(f"Rows skipped: {skipped}")

        # Summary stats
        cursor.execute("SELECT COUNT(*) FROM contracts")
        total_contracts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM payment_schedule")
        total_payments = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(amount) FROM payment_schedule WHERE status = 'pending'")
        total_pending = cursor.fetchone()[0]

        logger.info(f"\n=== Database Summary ===")
        logger.info(f"Total contracts: {total_contracts}")
        logger.info(f"Total payment entries: {total_payments}")
        logger.info(f"Total pending amount: £{total_pending:,.2f}" if total_pending else "Total pending: £0")

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import installments from Excel")
    parser.add_argument(
        "file",
        nargs="?",
        default="/Users/alexgilts/Library/Mobile Documents/com~apple~CloudDocs/AG Work/SAV Group/Installments.xlsx",
        help="Path to Installments Excel file"
    )
    parser.add_argument("--clear", action="store_true", help="Clear existing data before import")
    args = parser.parse_args()

    import_installments(args.file, clear_existing=args.clear)
