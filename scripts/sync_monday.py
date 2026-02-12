# scripts/sync_monday.py
"""
Live sync from Monday CRM Won Deals / Installments board.

Board ID: 8606133913
Fetches contracts and payment schedules directly from Monday.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCHEMA_NAME = os.getenv("DB_SCHEMA", "more_house")

# Monday column mappings for board 9376648770 (MH - Unit Schedule / Rooms)
ROOM_COLUMN_MAP = {
    'floor': 'dropdown_mkrs7zx2',
    'category': 'dropdown_mkrx42t8',
    'sqm': 'numeric_mkrxddk6',
    'weekly_rate': 'numeric_mkrxa9hm',
    'mattress_size': 'dropdown_mkrxx9jb',
    'term_status': 'color_mkrx57e1',
    'contract_status': 'color_mkvk6y7',
    'washing_machine': 'boolean_mksx150g',
    'safe': 'boolean_mkvdrd2k',
}

# Monday column mappings for board 8606133913 (Won Deals / Installments)
COLUMN_MAP = {
    # Contract info
    'unit': 'text_mktbxcap',           # Unit Booked New
    'length_of_stay': 'timerange_mkt9gsnr',  # Actual Length of Stay (timeline)
    'gross_income': 'formula_mks34v1y',      # Gross Income
    'rate_agreed': 'numeric_mks2n5fp',       # Rate Agreed (weekly rent)
    'payment_plan': 'color_mks9w1p0',        # Payment Plan (status)
    'nationality': 'country_mks9cg7q',       # Nationality
    'university': 'dropdown_mks9rbmv',       # University
    'stage': 'deal_stage',                   # Stage (status)

    # Due dates
    'booking_fee_due': 'date_mkszxxzx',
    'instalment_1_due': 'date_mkszyrpe',
    'instalment_2_due': 'date_mksza278',
    'instalment_3_due': 'date_mkszs0a4',
    'instalment_4_due': 'date_mkszsh2q',
    'instalment_5_due': 'date_mkvmyxgf',

    # Amounts due
    'booking_fee_amount': 'numeric_mkvt5vhm',
    'instalment_1_amount': 'numeric_mkvt5wym',
    'instalment_2_amount': 'numeric_mkvtn7fe',
    'instalment_3_amount': 'numeric_mkvtcr5w',
    'instalment_4_amount': 'numeric_mkvtq4d7',
    'instalment_5_amount': 'numeric_mkvteg65',

    # Payment status (status columns)
    'booking_fee_status': 'color_mksjjgs8',
    'instalment_1_status': 'color_mksj58qp',
    'instalment_2_status': 'color_mkvm35a8',
    'instalment_3_status': 'color_mkvmm56g',
    'instalment_4_status': 'color_mkvmj60x',
    'instalment_5_status': 'color_mkvmbs6q',

    # Amounts paid
    'booking_fee_paid': 'numeric_mkvttd71',
    'instalment_1_paid': 'numeric_mkvt65kz',
    'instalment_2_paid': 'numeric_mkvtvhaj',
    'instalment_3_paid': 'numeric_mks9ge93',
    'instalment_4_paid': 'numeric_mksay7t3',
    'instalment_5_paid': 'numeric_mkvmg7qw',

    # Paid dates
    'booking_fee_paid_date': 'date_mkvmnthc',
    'instalment_1_paid_date': 'date_mkvmv57g',
    'instalment_2_paid_date': 'date_mkvmmygn',
    'instalment_3_paid_date': 'date_mkvm7kh9',
    'instalment_4_paid_date': 'date_mkvmxnhd',
    'instalment_5_paid_date': 'date_mkvme5qn',

    # Totals
    'total_paid': 'formula_mksjgpyh',
    'balance': 'formula_mksj1fzq',
}


def get_column_value(item: Dict, column_id: str) -> Optional[str]:
    """Extract text value from a Monday item's column."""
    for cv in item.get('column_values', []):
        if cv['id'] == column_id:
            return cv.get('text') or None
    return None


def get_column_raw_value(item: Dict, column_id: str) -> Optional[Any]:
    """Extract raw JSON value from a Monday item's column."""
    for cv in item.get('column_values', []):
        if cv['id'] == column_id:
            val = cv.get('value')
            if val:
                try:
                    return json.loads(val)
                except:
                    return val
    return None


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """Parse date string to YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        # Monday dates come as "YYYY-MM-DD" in text field
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except:
        return None


def parse_number(value: Optional[str]) -> Optional[float]:
    """Parse number from string, handling currency formatting."""
    if not value:
        return None
    try:
        # Remove currency symbols and commas
        clean = str(value).replace('£', '').replace(',', '').replace(' ', '').strip()
        if clean:
            return float(clean)
    except:
        pass
    return None


def normalize_room_id(room_id: str) -> str:
    """
    Normalize room ID to match Unit Schedule format.
    - M10 -> MEZZ 10
    - -1.10 -> -1.1 (remove trailing zero)
    """
    if not room_id:
        return room_id

    room_id = room_id.strip()

    # Convert Mxx to MEZZ xx
    if room_id.upper().startswith('M') and room_id[1:].isdigit():
        return f"MEZZ {room_id[1:]}"

    # Normalize decimal format (e.g., -1.10 -> -1.1, 0.10 -> 0.1)
    # Match patterns like X.Y0 where Y0 ends in 0
    import re
    match = re.match(r'^(-?\d+)\.(\d)0$', room_id)
    if match:
        return f"{match.group(1)}.{match.group(2)}"

    return room_id


def parse_timeline(item: Dict, column_id: str) -> tuple:
    """Parse timeline column to get start and end dates."""
    raw = get_column_raw_value(item, column_id)
    if raw and isinstance(raw, dict):
        return raw.get('from'), raw.get('to')
    return None, None


def map_payment_status(status_text: Optional[str]) -> str:
    """Map Monday payment status to database status."""
    if not status_text:
        return 'pending'
    status_lower = status_text.lower()
    if 'paid' in status_lower or 'received' in status_lower:
        return 'paid'
    if 'partial' in status_lower:
        return 'partial'
    if 'overdue' in status_lower or 'late' in status_lower:
        return 'overdue'
    return 'pending'


def sync_rooms_from_monday(dry_run: bool = False):
    """
    Sync room inventory from Monday CRM (MH - Unit Schedule board).

    Board ID: 9376648770
    """
    from integrations.monday_client import MondayClient

    client = MondayClient()
    board_id = os.getenv("MONDAY_BOARD_ID_CONTRACTS", "9376648770")

    logger.info(f"Fetching rooms from Monday board {board_id}...")
    items = client.get_all_board_items(board_id)
    logger.info(f"Found {len(items)} rooms")

    if dry_run:
        logger.info("DRY RUN - no database changes will be made")

    connection_string = os.getenv("TIMESCALE_SERVICE_URL")
    if not connection_string:
        logger.error("TIMESCALE_SERVICE_URL not set")
        sys.exit(1)

    conn = psycopg2.connect(dsn=connection_string)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")

    stats = {'created': 0, 'updated': 0, 'skipped': 0}

    for item in items:
        room_id = item.get('name', '').strip()
        if not room_id:
            stats['skipped'] += 1
            continue

        floor = get_column_value(item, ROOM_COLUMN_MAP['floor'])
        category = get_column_value(item, ROOM_COLUMN_MAP['category'])
        sqm = parse_number(get_column_value(item, ROOM_COLUMN_MAP['sqm']))
        weekly_rate = parse_number(get_column_value(item, ROOM_COLUMN_MAP['weekly_rate']))
        mattress_size = get_column_value(item, ROOM_COLUMN_MAP['mattress_size'])

        if dry_run:
            logger.info(f"Would sync room: {room_id} | {floor} | {category} | {sqm}sqm | £{weekly_rate}/wk")
            continue

        # Check if room exists
        cursor.execute("SELECT room_id FROM rooms WHERE room_id = %s", (room_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE rooms SET
                    floor = %s,
                    category = %s,
                    sqm = %s,
                    weekly_rate = %s,
                    mattress_size = %s,
                    updated_at = NOW()
                WHERE room_id = %s
            """, (floor, category, sqm, weekly_rate, mattress_size, room_id))
            stats['updated'] += 1
        else:
            cursor.execute("""
                INSERT INTO rooms (room_id, floor, category, sqm, weekly_rate, mattress_size)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (room_id, floor, category, sqm, weekly_rate, mattress_size))
            stats['created'] += 1

    if not dry_run:
        conn.commit()

    cursor.close()
    conn.close()

    logger.info("\n=== Room Sync Complete ===")
    logger.info(f"Rooms created: {stats['created']}")
    logger.info(f"Rooms updated: {stats['updated']}")
    logger.info(f"Skipped: {stats['skipped']}")

    return stats


def sync_from_monday(clear_existing: bool = False, dry_run: bool = False):
    """
    Sync contracts and payment schedules from Monday CRM.

    Args:
        clear_existing: If True, delete all existing data before import
        dry_run: If True, don't write to database, just show what would happen
    """
    from integrations.monday_client import MondayClient

    client = MondayClient()
    board_id = os.getenv("MONDAY_BOARD_ID_PAYMENTS")

    if not board_id:
        logger.error("MONDAY_BOARD_ID_PAYMENTS not set in .env")
        sys.exit(1)

    logger.info(f"Fetching data from Monday board {board_id}...")
    items = client.get_all_board_items(board_id)
    logger.info(f"Found {len(items)} items")

    if dry_run:
        logger.info("DRY RUN - no database changes will be made")

    connection_string = os.getenv("TIMESCALE_SERVICE_URL")
    if not connection_string:
        logger.error("TIMESCALE_SERVICE_URL not set")
        sys.exit(1)

    conn = psycopg2.connect(dsn=connection_string)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")

    if clear_existing and not dry_run:
        logger.info("Clearing existing data...")
        cursor.execute("DELETE FROM payments_received")
        cursor.execute("DELETE FROM payment_schedule")
        cursor.execute("DELETE FROM contracts")
        conn.commit()

    stats = {
        'contracts_created': 0,
        'contracts_updated': 0,
        'payments_created': 0,
        'payments_updated': 0,
        'skipped': 0,
    }

    for item in items:
        monday_id = item['id']
        resident_name = item.get('name', '').strip()

        # Get contract data
        room_id_raw = get_column_value(item, COLUMN_MAP['unit'])
        room_id = normalize_room_id(room_id_raw) if room_id_raw else None
        gross_income = parse_number(get_column_value(item, COLUMN_MAP['gross_income']))
        rate_agreed = parse_number(get_column_value(item, COLUMN_MAP['rate_agreed']))
        payment_plan = get_column_value(item, COLUMN_MAP['payment_plan'])
        nationality = get_column_value(item, COLUMN_MAP['nationality'])
        university = get_column_value(item, COLUMN_MAP['university'])
        stage = get_column_value(item, COLUMN_MAP['stage'])

        # Parse timeline for start/end dates
        start_date, end_date = parse_timeline(item, COLUMN_MAP['length_of_stay'])

        # Skip if missing critical data
        if not resident_name or not room_id:
            logger.debug(f"Skipping item {monday_id}: missing name or room")
            stats['skipped'] += 1
            continue

        # Skip if missing dates (required by database)
        if not start_date or not end_date:
            logger.debug(f"Skipping item {monday_id} ({resident_name}): missing start/end dates")
            stats['skipped'] += 1
            continue

        # Calculate total value from installments if gross_income formula is empty
        if not gross_income:
            installment_amounts = [
                parse_number(get_column_value(item, COLUMN_MAP['booking_fee_amount'])),
                parse_number(get_column_value(item, COLUMN_MAP['instalment_1_amount'])),
                parse_number(get_column_value(item, COLUMN_MAP['instalment_2_amount'])),
                parse_number(get_column_value(item, COLUMN_MAP['instalment_3_amount'])),
                parse_number(get_column_value(item, COLUMN_MAP['instalment_4_amount'])),
                parse_number(get_column_value(item, COLUMN_MAP['instalment_5_amount'])),
            ]
            gross_income = sum(a for a in installment_amounts if a) or 0

        if dry_run:
            logger.info(f"Would sync: {resident_name} - Room {room_id} - £{gross_income:,.0f}")
            continue

        # Ensure room exists
        cursor.execute("SELECT room_id FROM rooms WHERE room_id = %s", (room_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO rooms (room_id, floor, category) VALUES (%s, 'TBD', 'TBD')",
                (room_id,)
            )
            logger.info(f"Created room: {room_id}")

        # Check if contract exists (by monday_id)
        cursor.execute(
            "SELECT id FROM contracts WHERE monday_id = %s",
            (monday_id,)
        )
        existing = cursor.fetchone()

        if existing:
            contract_id = existing[0]
            # Update existing contract
            cursor.execute("""
                UPDATE contracts SET
                    room_id = %s,
                    resident_name = %s,
                    start_date = %s,
                    end_date = %s,
                    total_value = %s,
                    weekly_rate = %s,
                    payment_plan = %s,
                    nationality = %s,
                    university = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                room_id, resident_name, start_date, end_date,
                gross_income or 0, rate_agreed,
                payment_plan or 'Unknown',
                nationality, university, contract_id
            ))
            stats['contracts_updated'] += 1
        else:
            # Create new contract
            cursor.execute("""
                INSERT INTO contracts (
                    monday_id, room_id, resident_name, start_date, end_date,
                    total_value, weekly_rate, payment_plan, status, nationality, university
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, %s)
                RETURNING id
            """, (
                monday_id, room_id, resident_name, start_date, end_date,
                gross_income or 0, rate_agreed, payment_plan or 'Unknown',
                nationality, university
            ))
            contract_id = cursor.fetchone()[0]
            stats['contracts_created'] += 1

        # Sync payment schedule
        installments = [
            (0, 'booking_fee'),
            (1, 'instalment_1'),
            (2, 'instalment_2'),
            (3, 'instalment_3'),
            (4, 'instalment_4'),
            (5, 'instalment_5'),
        ]

        for inst_num, inst_key in installments:
            due_date = parse_date(get_column_value(item, COLUMN_MAP[f'{inst_key}_due']))
            amount = parse_number(get_column_value(item, COLUMN_MAP[f'{inst_key}_amount']))
            status_text = get_column_value(item, COLUMN_MAP[f'{inst_key}_status'])
            status = map_payment_status(status_text)

            # Skip if no amount
            if not amount or amount <= 0:
                continue

            # Check if payment schedule entry exists
            cursor.execute("""
                SELECT id FROM payment_schedule
                WHERE contract_id = %s AND installment_number = %s
            """, (contract_id, inst_num))
            existing_payment = cursor.fetchone()

            if existing_payment:
                cursor.execute("""
                    UPDATE payment_schedule SET
                        due_date = %s,
                        amount = %s,
                        status = %s
                    WHERE id = %s
                """, (due_date, amount, status, existing_payment[0]))
                stats['payments_updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO payment_schedule (
                        contract_id, installment_number, due_date, amount, status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (contract_id, inst_num, due_date, amount, status))
                stats['payments_created'] += 1

        # Sync actual payments received
        for inst_num, inst_key in installments:
            paid_amount = parse_number(get_column_value(item, COLUMN_MAP[f'{inst_key}_paid']))
            paid_date = parse_date(get_column_value(item, COLUMN_MAP[f'{inst_key}_paid_date']))

            if paid_amount and paid_amount > 0 and paid_date:
                # Check if payment record exists
                cursor.execute("""
                    SELECT id FROM payments_received
                    WHERE contract_id = %s AND allocated_to_installment = %s
                """, (contract_id, inst_num))
                existing_received = cursor.fetchone()

                if existing_received:
                    cursor.execute("""
                        UPDATE payments_received SET
                            payment_date = %s,
                            amount = %s
                        WHERE id = %s
                    """, (paid_date, paid_amount, existing_received[0]))
                else:
                    cursor.execute("""
                        INSERT INTO payments_received (
                            contract_id, payment_date, amount,
                            payment_method, allocated_to_installment
                        )
                        VALUES (%s, %s, %s, 'monday_sync', %s)
                    """, (contract_id, paid_date, paid_amount, inst_num))

    if not dry_run:
        conn.commit()

    cursor.close()
    conn.close()

    logger.info("\n=== Sync Complete ===")
    logger.info(f"Contracts created: {stats['contracts_created']}")
    logger.info(f"Contracts updated: {stats['contracts_updated']}")
    logger.info(f"Payments created: {stats['payments_created']}")
    logger.info(f"Payments updated: {stats['payments_updated']}")
    logger.info(f"Items skipped: {stats['skipped']}")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync from Monday CRM")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before sync")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--rooms-only", action="store_true", help="Only sync rooms (Unit Schedule board)")
    parser.add_argument("--contracts-only", action="store_true", help="Only sync contracts (Won Deals board)")
    args = parser.parse_args()

    if args.rooms_only:
        sync_rooms_from_monday(dry_run=args.dry_run)
    elif args.contracts_only:
        sync_from_monday(clear_existing=args.clear, dry_run=args.dry_run)
    else:
        # Sync both: rooms first, then contracts
        logger.info("=== Syncing Rooms ===")
        sync_rooms_from_monday(dry_run=args.dry_run)
        logger.info("\n=== Syncing Contracts ===")
        sync_from_monday(clear_existing=args.clear, dry_run=args.dry_run)
