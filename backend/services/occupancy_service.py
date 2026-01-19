# backend/services/occupancy_service.py

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

# Constants
TOTAL_ROOMS = 120


class OccupancyService:
    """
    Service for calculating occupancy metrics from contracts data.
    """

    def __init__(self):
        # Will be replaced with DB queries once tables are populated
        self._contracts = []

    def get_summary(self) -> Dict:
        """Get current occupancy summary."""
        try:
            from utils.db_connection import execute_query

            # Get current date
            today = date.today()

            # Count occupied rooms (contracts where today is between start and end)
            query = """
                SELECT COUNT(DISTINCT room_id) as occupied
                FROM more_house.contracts
                WHERE start_date <= %s AND end_date >= %s
                AND status = 'active'
            """
            result = execute_query(query, (today, today))
            occupied = result[0]['occupied'] if result else 0

            return {
                "total_rooms": TOTAL_ROOMS,
                "occupied": occupied,
                "vacant": TOTAL_ROOMS - occupied,
                "occupancy_rate": round(occupied / TOTAL_ROOMS * 100, 1),
                "as_of": today.isoformat()
            }
        except Exception as e:
            logger.warning(f"DB not ready, returning placeholder: {e}")
            return {
                "total_rooms": TOTAL_ROOMS,
                "occupied": 0,
                "vacant": TOTAL_ROOMS,
                "occupancy_rate": 0,
                "as_of": date.today().isoformat(),
                "note": "Database not initialized"
            }

    def get_monthly_overview(
        self,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> List[Dict]:
        """
        Get monthly move-ins, move-outs, and net change.
        """
        try:
            from utils.db_connection import execute_query

            # Default to next 12 months
            if not start_month:
                start_month = date.today().strftime("%Y-%m")
            if not end_month:
                end_date = date.today() + timedelta(days=365)
                end_month = end_date.strftime("%Y-%m")

            query = """
                WITH months AS (
                    SELECT generate_series(
                        %s::date,
                        %s::date,
                        '1 month'::interval
                    )::date as month_start
                ),
                move_ins AS (
                    SELECT DATE_TRUNC('month', start_date)::date as month, COUNT(*) as cnt
                    FROM more_house.contracts
                    WHERE status IN ('active', 'signed')
                    GROUP BY 1
                ),
                move_outs AS (
                    SELECT DATE_TRUNC('month', end_date)::date as month, COUNT(*) as cnt
                    FROM more_house.contracts
                    WHERE status IN ('active', 'signed')
                    GROUP BY 1
                )
                SELECT
                    TO_CHAR(m.month_start, 'YYYY-MM') as month,
                    COALESCE(mi.cnt, 0) as move_ins,
                    COALESCE(mo.cnt, 0) as move_outs,
                    COALESCE(mi.cnt, 0) - COALESCE(mo.cnt, 0) as net_change
                FROM months m
                LEFT JOIN move_ins mi ON mi.month = m.month_start
                LEFT JOIN move_outs mo ON mo.month = m.month_start
                ORDER BY m.month_start
            """
            return execute_query(query, (f"{start_month}-01", f"{end_month}-01"))
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_weekly_overview(
        self,
        start_date: Optional[str] = None,
        weeks: int = 8
    ) -> List[Dict]:
        """
        Get weekly move-ins and move-outs.
        """
        try:
            from utils.db_connection import execute_query

            if not start_date:
                start_date = date.today().isoformat()

            query = """
                WITH weeks AS (
                    SELECT generate_series(
                        %s::date,
                        %s::date + (%s * 7),
                        '1 week'::interval
                    )::date as week_start
                ),
                move_ins AS (
                    SELECT DATE_TRUNC('week', start_date)::date as week, COUNT(*) as cnt
                    FROM more_house.contracts
                    WHERE status IN ('active', 'signed')
                    GROUP BY 1
                ),
                move_outs AS (
                    SELECT DATE_TRUNC('week', end_date)::date as week, COUNT(*) as cnt
                    FROM more_house.contracts
                    WHERE status IN ('active', 'signed')
                    GROUP BY 1
                )
                SELECT
                    TO_CHAR(w.week_start, 'YYYY-MM-DD') as week_start,
                    TO_CHAR(w.week_start + 6, 'YYYY-MM-DD') as week_end,
                    COALESCE(mi.cnt, 0) as move_ins,
                    COALESCE(mo.cnt, 0) as move_outs,
                    COALESCE(mi.cnt, 0) - COALESCE(mo.cnt, 0) as net_change
                FROM weeks w
                LEFT JOIN move_ins mi ON mi.week = w.week_start
                LEFT JOIN move_outs mo ON mo.week = w.week_start
                ORDER BY w.week_start
                LIMIT %s
            """
            return execute_query(query, (start_date, start_date, weeks, weeks))
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_upcoming_vacancies(self, days: int = 30) -> List[Dict]:
        """
        Get rooms becoming vacant with no follow-on booking.
        This is the sales priority list.
        """
        try:
            from utils.db_connection import execute_query

            today = date.today()
            end_date = today + timedelta(days=days)

            query = """
                WITH ending_contracts AS (
                    SELECT
                        c.room_id,
                        c.resident_name,
                        c.end_date,
                        c.weekly_rate
                    FROM more_house.contracts c
                    WHERE c.end_date BETWEEN %s AND %s
                    AND c.status = 'active'
                ),
                follow_on AS (
                    SELECT DISTINCT room_id
                    FROM more_house.contracts
                    WHERE start_date <= %s
                    AND status IN ('active', 'signed')
                )
                SELECT
                    ec.room_id,
                    ec.resident_name as current_tenant,
                    ec.end_date as vacates_on,
                    ec.end_date - CURRENT_DATE as days_until_vacant,
                    ec.weekly_rate,
                    CASE WHEN fo.room_id IS NOT NULL THEN 'Has follow-on' ELSE 'No follow-on' END as status
                FROM ending_contracts ec
                LEFT JOIN follow_on fo ON fo.room_id = ec.room_id
                WHERE fo.room_id IS NULL
                ORDER BY ec.end_date
            """
            return execute_query(query, (today, end_date, end_date))
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_all_rooms(self) -> List[Dict]:
        """Get all rooms with current status."""
        try:
            from utils.db_connection import execute_query

            query = """
                SELECT
                    r.room_id,
                    r.floor,
                    r.category,
                    r.sqm,
                    c.resident_name as current_tenant,
                    c.start_date,
                    c.end_date,
                    CASE
                        WHEN c.id IS NOT NULL THEN 'Occupied'
                        ELSE 'Vacant'
                    END as status
                FROM more_house.rooms r
                LEFT JOIN more_house.contracts c ON c.room_id = r.room_id
                    AND c.start_date <= CURRENT_DATE
                    AND c.end_date >= CURRENT_DATE
                    AND c.status = 'active'
                ORDER BY r.room_id
            """
            return execute_query(query)
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_room_timeline(self, room_id: str) -> Dict:
        """Get booking timeline for a specific room."""
        try:
            from utils.db_connection import execute_query

            query = """
                SELECT
                    room_id,
                    resident_name,
                    start_date,
                    end_date,
                    weekly_rate,
                    total_value,
                    status
                FROM more_house.contracts
                WHERE room_id = %s
                ORDER BY start_date
            """
            bookings = execute_query(query, (room_id,))
            return {
                "room_id": room_id,
                "bookings": bookings
            }
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return {"room_id": room_id, "bookings": []}
