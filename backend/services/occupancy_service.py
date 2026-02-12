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
        """Get current occupancy summary with key metrics."""
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

            # Average weekly rent for all active contracts (Rate Agreed from Monday)
            avg_rent_query = """
                SELECT AVG(c.weekly_rate)
                FROM more_house.contracts c
                WHERE c.status = 'active'
                AND c.weekly_rate IS NOT NULL
            """
            avg_rent_result = execute_query(avg_rent_query)
            avg_weekly_rent = float(avg_rent_result[0]['avg']) if avg_rent_result and avg_rent_result[0]['avg'] else 0

            # Total signed contract value (net income signed)
            total_value_query = """
                SELECT SUM(total_value) as total, COUNT(*) as count
                FROM more_house.contracts
                WHERE status = 'active'
            """
            total_result = execute_query(total_value_query)
            total_signed = float(total_result[0]['total']) if total_result and total_result[0]['total'] else 0
            contract_count = total_result[0]['count'] if total_result else 0

            return {
                "total_rooms": TOTAL_ROOMS,
                "occupied": occupied,
                "vacant": TOTAL_ROOMS - occupied,
                "occupancy_rate": round(occupied / TOTAL_ROOMS * 100, 1),
                "avg_weekly_rent": round(avg_weekly_rent, 0),
                "total_signed_value": round(total_signed, 0),
                "contract_count": contract_count,
                "as_of": today.isoformat()
            }
        except Exception as e:
            logger.warning(f"DB not ready, returning placeholder: {e}")
            return {
                "total_rooms": TOTAL_ROOMS,
                "occupied": 0,
                "vacant": TOTAL_ROOMS,
                "occupancy_rate": 0,
                "avg_weekly_rent": 0,
                "total_signed_value": 0,
                "contract_count": 0,
                "as_of": date.today().isoformat(),
                "note": "Database not initialized"
            }

    def _get_current_occupancy(self) -> int:
        """Get the current occupancy count."""
        try:
            from utils.db_connection import execute_query
            today = date.today()
            query = """
                SELECT COUNT(DISTINCT room_id) as occupied
                FROM more_house.contracts
                WHERE start_date <= %s AND end_date >= %s
                AND status = 'active'
            """
            result = execute_query(query, (today, today))
            return result[0]['occupied'] if result else 0
        except Exception:
            return 0

    def get_monthly_overview(
        self,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> List[Dict]:
        """
        Get monthly move-ins, move-outs, and running occupancy.
        """
        try:
            from utils.db_connection import execute_query

            # Default to next 12 months
            if not start_month:
                start_month = date.today().strftime("%Y-%m")
            if not end_month:
                end_date = date.today() + timedelta(days=365)
                end_month = end_date.strftime("%Y-%m")

            # Get current occupancy as starting point
            current_occupancy = self._get_current_occupancy()

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
            results = execute_query(query, (f"{start_month}-01", f"{end_month}-01"))

            # Add running occupancy calculation
            running_occupancy = current_occupancy
            for i, row in enumerate(results):
                row['start_occupancy'] = running_occupancy
                running_occupancy = running_occupancy + row['move_ins'] - row['move_outs']
                row['end_occupancy'] = running_occupancy

            return results
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_weekly_overview(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        weeks: int = 8
    ) -> List[Dict]:
        """
        Get weekly move-ins and move-outs with running occupancy.
        If end_date is provided, weeks parameter is ignored.
        """
        try:
            from utils.db_connection import execute_query

            if not start_date:
                start_date = date.today().isoformat()

            # Get current occupancy as starting point
            current_occupancy = self._get_current_occupancy()

            if end_date:
                # Use end_date instead of weeks
                query = """
                    WITH weeks AS (
                        SELECT generate_series(
                            DATE_TRUNC('week', %s::date)::date,
                            %s::date,
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
                """
                results = execute_query(query, (start_date, end_date))
            else:
                query = """
                    WITH weeks AS (
                        SELECT generate_series(
                            DATE_TRUNC('week', %s::date)::date,
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
                results = execute_query(query, (start_date, start_date, weeks, weeks))

            # Add running occupancy calculation
            running_occupancy = current_occupancy
            for row in results:
                row['start_occupancy'] = running_occupancy
                running_occupancy = running_occupancy + row['move_ins'] - row['move_outs']
                row['end_occupancy'] = running_occupancy

            return results
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
                SELECT DISTINCT ON (r.room_id)
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
                ORDER BY r.room_id, c.start_date DESC
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

    def get_all_room_timelines(self) -> List[Dict]:
        """
        Get all rooms with their contract timelines in a single query.
        More efficient than making 120 individual API calls.
        """
        try:
            from utils.db_connection import execute_query

            # First get all rooms
            rooms_query = """
                SELECT room_id, floor, category, sqm
                FROM more_house.rooms
                ORDER BY room_id
            """
            rooms = execute_query(rooms_query)

            # Then get all contracts
            contracts_query = """
                SELECT
                    room_id,
                    resident_name,
                    start_date,
                    end_date,
                    status,
                    weekly_rate
                FROM more_house.contracts
                WHERE status IN ('active', 'signed', 'completed')
                ORDER BY room_id, start_date
            """
            contracts = execute_query(contracts_query)

            # Group contracts by room_id
            contracts_by_room = {}
            for contract in contracts:
                room_id = contract['room_id']
                if room_id not in contracts_by_room:
                    contracts_by_room[room_id] = []

                # Determine contract status for display
                today = date.today()
                start = contract['start_date']
                end = contract['end_date']

                if isinstance(start, str):
                    start = datetime.strptime(start, '%Y-%m-%d').date()
                if isinstance(end, str):
                    end = datetime.strptime(end, '%Y-%m-%d').date()

                if start > today:
                    display_status = 'future'
                elif end < today:
                    display_status = 'past'
                else:
                    display_status = 'active'

                contracts_by_room[room_id].append({
                    'resident_name': contract['resident_name'],
                    'start_date': contract['start_date'].isoformat() if hasattr(contract['start_date'], 'isoformat') else contract['start_date'],
                    'end_date': contract['end_date'].isoformat() if hasattr(contract['end_date'], 'isoformat') else contract['end_date'],
                    'status': display_status,
                    'weekly_rate': contract['weekly_rate']
                })

            # Build result
            result = []
            for room in rooms:
                room_id = room['room_id']
                result.append({
                    'room_id': room_id,
                    'floor': room['floor'],
                    'category': room['category'],
                    'contracts': contracts_by_room.get(room_id, [])
                })

            return result
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            # Return placeholder data for all 120 rooms
            return [
                {
                    'room_id': f"{floor}.{str(num).zfill(2)}",
                    'floor': str(floor),
                    'category': 'Standard',
                    'contracts': []
                }
                for floor in range(1, 7)
                for num in range(1, 21)
            ]
