# backend/api/activity.py

from fastapi import APIRouter
from datetime import datetime, date, timedelta
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SCHEMA_NAME = os.getenv("DB_SCHEMA", "more_house")

# Column IDs for Qualified board (9188309936)
QUALIFIED_VIEWING_DATE = 'date_mkr5m8jk'
QUALIFIED_SIGN_DATE = 'date_mkr5cxqh'
QUALIFIED_STAGE = 'status__1'

# Column IDs for Won Deals board (8606133913)
WON_VIEWING_DATE = 'date_mks29j00'
WON_SIGN_DATE = 'date_mks2y4vg'
WON_UNIT = 'text_mktbxcap'
WON_LENGTH_OF_STAY = 'timerange_mkt9gsnr'
WON_RATE = 'numeric_mks2n5fp'
WON_GROSS_INCOME = 'formula_mks34v1y'


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _get_monday_items(board_id, columns):
    """Fetch items from a Monday board with specific columns."""
    from integrations.monday_client import MondayClient
    client = MondayClient()

    col_ids = list(columns.values())
    all_items = client.get_all_board_items(board_id)

    results = []
    for item in all_items:
        row = {'name': item.get('name', ''), 'monday_id': item['id']}
        for key, col_id in columns.items():
            for cv in item.get('column_values', []):
                if cv['id'] == col_id:
                    row[key] = cv.get('text') or None
                    # Also get raw value for timelines
                    import json
                    raw = cv.get('value')
                    if raw:
                        try:
                            row[f'{key}_raw'] = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    break
        results.append(row)
    return results


@router.get("/summary")
async def get_activity_summary():
    """
    Get viewings and new contracts signed in last 1d, 3d, 7d, 1m, 3m.
    Pulls from both Qualified and Won Deals boards.
    """
    today = date.today()
    periods = {
        '1d': today - timedelta(days=1),
        '3d': today - timedelta(days=3),
        '7d': today - timedelta(days=7),
        '1m': today - timedelta(days=30),
        '3m': today - timedelta(days=90),
    }

    # Fetch from both boards
    qualified_items = _get_monday_items('9188309936', {
        'viewing_date': QUALIFIED_VIEWING_DATE,
        'sign_date': QUALIFIED_SIGN_DATE,
    })

    won_items = _get_monday_items('8606133913', {
        'viewing_date': WON_VIEWING_DATE,
        'sign_date': WON_SIGN_DATE,
        'unit': WON_UNIT,
        'length_of_stay': WON_LENGTH_OF_STAY,
        'rate': WON_RATE,
        'gross_income': WON_GROSS_INCOME,
    })

    # Collect all viewing dates from both boards (deduplicate by name)
    all_viewings = []
    seen_names = set()

    for item in won_items:
        vd = _parse_date(item.get('viewing_date'))
        if vd:
            all_viewings.append({'name': item['name'], 'date': vd})
            seen_names.add(item['name'].lower().strip())

    for item in qualified_items:
        name_key = item['name'].lower().strip()
        if name_key not in seen_names:
            vd = _parse_date(item.get('viewing_date'))
            if vd:
                all_viewings.append({'name': item['name'], 'date': vd})

    # Collect signed contracts from Won Deals
    all_contracts = []
    for item in won_items:
        sd = _parse_date(item.get('sign_date'))
        if sd:
            raw_timeline = item.get('length_of_stay_raw', {})
            start = raw_timeline.get('from') if isinstance(raw_timeline, dict) else None
            end = raw_timeline.get('to') if isinstance(raw_timeline, dict) else None
            all_contracts.append({
                'name': item['name'],
                'sign_date': sd,
                'unit': item.get('unit'),
                'start_date': start,
                'end_date': end,
                'rate': item.get('rate'),
                'gross_income': item.get('gross_income'),
            })

    # Count by period
    viewings_by_period = {}
    for key, cutoff in periods.items():
        viewings_by_period[key] = len([v for v in all_viewings if v['date'] >= cutoff])

    contracts_by_period = {}
    for key, cutoff in periods.items():
        recent = [c for c in all_contracts if c['sign_date'] >= cutoff]
        contracts_by_period[key] = {
            'count': len(recent),
            'contracts': sorted(
                [
                    {
                        'name': c['name'],
                        'sign_date': c['sign_date'].isoformat(),
                        'unit': c['unit'],
                        'start_date': c['start_date'],
                        'end_date': c['end_date'],
                        'rate': c['rate'],
                        'gross_income': c['gross_income'],
                    }
                    for c in recent
                ],
                key=lambda x: x['sign_date'],
                reverse=True,
            )
        }

    return {
        'viewings': viewings_by_period,
        'contracts': contracts_by_period,
        'totals': {
            'total_viewings': len(all_viewings),
            'total_contracts': len(all_contracts),
        }
    }
