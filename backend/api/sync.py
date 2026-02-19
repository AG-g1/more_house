# backend/api/sync.py

from fastapi import APIRouter, BackgroundTasks
from datetime import datetime
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SCHEMA_NAME = os.getenv("DB_SCHEMA", "more_house")

# Track last sync state
_last_sync = {
    "status": "idle",
    "last_synced_at": None,
    "result": None,
}


def _get_db_counts():
    """Get current row counts from database."""
    conn = psycopg2.connect(dsn=os.getenv("TIMESCALE_SERVICE_URL"))
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA_NAME}, public")

    counts = {}
    for table in ["rooms", "contracts", "payment_schedule", "payments_received"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cur.fetchone()[0]

    cur.close()
    conn.close()
    return counts


def _get_monday_board_info():
    """Get Monday board last updated timestamps."""
    from integrations.monday_client import MondayClient
    client = MondayClient()

    query = '''
    query ($boardIds: [ID!]) {
        boards(ids: $boardIds) {
            id
            name
            updated_at
            items_count
        }
    }
    '''
    board_ids = [client.contracts_board_id, client.payments_board_id]
    result = client._execute_query(query, {'boardIds': board_ids})
    return result.get('boards', [])


def _run_sync():
    """Run the actual sync in background."""
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

    _last_sync["status"] = "syncing"
    _last_sync["result"] = None

    try:
        before = _get_db_counts()

        from scripts.sync_monday import sync_rooms_from_monday, sync_from_monday
        room_stats = sync_rooms_from_monday()
        contract_stats = sync_from_monday()

        after = _get_db_counts()

        _last_sync["status"] = "completed"
        _last_sync["last_synced_at"] = datetime.utcnow().isoformat() + "Z"
        _last_sync["result"] = {
            "rooms": room_stats,
            "contracts": contract_stats,
            "before": before,
            "after": after,
            "changes": {
                table: after[table] - before[table]
                for table in before
            }
        }
    except Exception as e:
        _last_sync["status"] = "error"
        _last_sync["result"] = {"error": str(e)}


@router.get("/status")
async def get_sync_status():
    """Get current sync status and Monday board info."""
    boards = []
    try:
        boards = _get_monday_board_info()
    except Exception:
        pass

    db_counts = {}
    try:
        db_counts = _get_db_counts()
    except Exception:
        pass

    return {
        "sync": _last_sync,
        "boards": boards,
        "db_counts": db_counts,
    }


@router.post("/run")
async def run_sync(background_tasks: BackgroundTasks):
    """Trigger a Monday sync."""
    if _last_sync["status"] == "syncing":
        return {"status": "already_syncing"}

    background_tasks.add_task(_run_sync)
    return {"status": "started"}
