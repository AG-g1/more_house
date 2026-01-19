# backend/services/cashflow_service.py

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class CashFlowService:
    """
    Service for calculating cash flow metrics.
    Works with actual payment schedules imported from Monday/Excel.

    Payment structure:
    - installment_number 0 = Booking Fee
    - installment_number 1-5 = Installments (termly, not monthly)

    Payment plans:
    - Installments: Booking fee + 4 termly installments
    - Single Payment: Booking fee + 1 full payment
    - Studentluxe: 3-4 installments (agent remits), no booking fee
    - Special Payment Terms: Custom schedule
    """

    INSTALLMENT_LABELS = {
        0: "Booking Fee",
        1: "Installment 1",
        2: "Installment 2",
        3: "Installment 3",
        4: "Installment 4",
        5: "Installment 5",
    }

    def __init__(self):
        pass

    def get_summary(self) -> Dict:
        """Get current cash flow summary."""
        try:
            from utils.db_connection import execute_query

            today = date.today()
            month_start = today.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)

            # Expected inflows this month
            query = """
                SELECT
                    COALESCE(SUM(amount), 0) as expected_inflows,
                    COUNT(*) as payment_count
                FROM more_house.payment_schedule
                WHERE due_date >= %s AND due_date < %s
                AND status = 'pending'
            """
            result = execute_query(query, (month_start, next_month))

            # Actual received this month
            received_query = """
                SELECT COALESCE(SUM(amount), 0) as received
                FROM more_house.payments_received
                WHERE payment_date >= %s AND payment_date < %s
            """
            received = execute_query(received_query, (month_start, next_month))

            # Overdue amount
            overdue_query = """
                SELECT COALESCE(SUM(amount), 0) as overdue
                FROM more_house.payment_schedule
                WHERE due_date < %s AND status = 'pending'
            """
            overdue = execute_query(overdue_query, (today,))

            return {
                "month": month_start.strftime("%Y-%m"),
                "expected_inflows": float(result[0]['expected_inflows']) if result else 0,
                "payments_due": int(result[0]['payment_count']) if result else 0,
                "received": float(received[0]['received']) if received else 0,
                "overdue": float(overdue[0]['overdue']) if overdue else 0,
            }
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return {
                "month": date.today().strftime("%Y-%m"),
                "expected_inflows": 0,
                "payments_due": 0,
                "received": 0,
                "overdue": 0,
                "note": "Database not initialized"
            }

    def get_monthly_cashflow(
        self,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> List[Dict]:
        """Get monthly cash flow projection."""
        try:
            from utils.db_connection import execute_query

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
                monthly_expected AS (
                    SELECT
                        DATE_TRUNC('month', due_date)::date as month,
                        SUM(amount) as expected,
                        COUNT(*) as payment_count
                    FROM more_house.payment_schedule
                    WHERE due_date IS NOT NULL
                    GROUP BY 1
                ),
                monthly_received AS (
                    SELECT
                        DATE_TRUNC('month', payment_date)::date as month,
                        SUM(amount) as received
                    FROM more_house.payments_received
                    GROUP BY 1
                ),
                monthly_opex AS (
                    SELECT
                        DATE_TRUNC('month', month_date)::date as month,
                        SUM(amount) as outflows
                    FROM more_house.opex_budget
                    GROUP BY 1
                )
                SELECT
                    TO_CHAR(m.month_start, 'YYYY-MM') as month,
                    COALESCE(e.expected, 0) as expected_inflows,
                    COALESCE(r.received, 0) as actual_inflows,
                    COALESCE(o.outflows, 0) as outflows,
                    COALESCE(e.payment_count, 0) as payments_due,
                    COALESCE(e.expected, 0) - COALESCE(o.outflows, 0) as net_cashflow,
                    SUM(COALESCE(e.expected, 0) - COALESCE(o.outflows, 0))
                        OVER (ORDER BY m.month_start) as running_balance
                FROM months m
                LEFT JOIN monthly_expected e ON e.month = m.month_start
                LEFT JOIN monthly_received r ON r.month = m.month_start
                LEFT JOIN monthly_opex o ON o.month = m.month_start
                ORDER BY m.month_start
            """
            return execute_query(query, (f"{start_month}-01", f"{end_month}-01"))
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_weekly_cashflow(
        self,
        start_date: Optional[str] = None,
        weeks: int = 8
    ) -> List[Dict]:
        """Get weekly cash flow breakdown."""
        try:
            from utils.db_connection import execute_query

            if not start_date:
                start_date = date.today().isoformat()

            query = """
                WITH weeks AS (
                    SELECT generate_series(
                        DATE_TRUNC('week', %s::date),
                        DATE_TRUNC('week', %s::date) + (%s * 7),
                        '1 week'::interval
                    )::date as week_start
                ),
                weekly_expected AS (
                    SELECT
                        DATE_TRUNC('week', due_date)::date as week,
                        SUM(amount) as expected,
                        COUNT(*) as payment_count
                    FROM more_house.payment_schedule
                    WHERE due_date IS NOT NULL
                    GROUP BY 1
                )
                SELECT
                    TO_CHAR(w.week_start, 'YYYY-MM-DD') as week_start,
                    TO_CHAR(w.week_start + 6, 'YYYY-MM-DD') as week_end,
                    COALESCE(we.expected, 0) as expected_inflows,
                    COALESCE(we.payment_count, 0) as payments_due
                FROM weeks w
                LEFT JOIN weekly_expected we ON we.week = w.week_start
                ORDER BY w.week_start
                LIMIT %s
            """
            return execute_query(query, (start_date, start_date, weeks, weeks))
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_expected_payments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get detailed expected payment schedule."""
        try:
            from utils.db_connection import execute_query

            if not start_date:
                start_date = date.today().isoformat()
            if not end_date:
                end_date = (date.today() + timedelta(days=90)).isoformat()

            query = """
                SELECT
                    ps.id,
                    ps.contract_id,
                    c.room_id,
                    c.resident_name,
                    c.payment_plan,
                    ps.installment_number,
                    ps.due_date,
                    ps.amount,
                    ps.status
                FROM more_house.payment_schedule ps
                JOIN more_house.contracts c ON c.id = ps.contract_id
                WHERE ps.due_date BETWEEN %s AND %s
                ORDER BY ps.due_date, c.resident_name
            """
            results = execute_query(query, (start_date, end_date))

            # Add installment label
            for r in results:
                r['installment_label'] = self.INSTALLMENT_LABELS.get(
                    r['installment_number'], f"Payment {r['installment_number']}"
                )

            return results
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_overdue_payments(self) -> List[Dict]:
        """Get overdue payments."""
        try:
            from utils.db_connection import execute_query

            query = """
                SELECT
                    ps.id,
                    c.room_id,
                    c.resident_name,
                    c.payment_plan,
                    ps.installment_number,
                    ps.due_date,
                    ps.amount,
                    CURRENT_DATE - ps.due_date as days_overdue
                FROM more_house.payment_schedule ps
                JOIN more_house.contracts c ON c.id = ps.contract_id
                WHERE ps.status = 'pending'
                AND ps.due_date < CURRENT_DATE
                ORDER BY ps.due_date
            """
            results = execute_query(query)

            for r in results:
                r['installment_label'] = self.INSTALLMENT_LABELS.get(
                    r['installment_number'], f"Payment {r['installment_number']}"
                )

            return results
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_payment_summary_by_plan(self) -> List[Dict]:
        """Get payment summary grouped by payment plan type."""
        try:
            from utils.db_connection import execute_query

            query = """
                SELECT
                    c.payment_plan,
                    COUNT(DISTINCT c.id) as contract_count,
                    SUM(c.total_value) as total_value,
                    SUM(CASE WHEN ps.status = 'pending' THEN ps.amount ELSE 0 END) as pending_amount,
                    SUM(CASE WHEN ps.status = 'paid' THEN ps.amount ELSE 0 END) as paid_amount
                FROM more_house.contracts c
                LEFT JOIN more_house.payment_schedule ps ON ps.contract_id = c.id
                GROUP BY c.payment_plan
                ORDER BY total_value DESC
            """
            return execute_query(query)
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []
