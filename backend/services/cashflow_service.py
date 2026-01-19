# backend/services/cashflow_service.py

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class CashFlowService:
    """
    Service for calculating cash flow metrics.
    Generates expected payment schedules from contracts based on payment plan rules.
    """

    # Payment plan rules - defines how each plan translates to payment schedule
    PAYMENT_PLAN_RULES = {
        "Single Payment": {"type": "upfront", "timing": "start"},
        "Installments": {"type": "monthly", "timing": "start_of_month"},
        "Studentluxe": {"type": "agent", "timing": "monthly"},  # Agent remits monthly
        "Special Payment Terms": {"type": "custom", "timing": "custom"},
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
                    COALESCE(SUM(amount), 0) as expected_inflows
                FROM more_house.payment_schedule
                WHERE due_date >= %s AND due_date < %s
            """
            inflows = execute_query(query, (month_start, next_month))

            return {
                "month": month_start.strftime("%Y-%m"),
                "expected_inflows": float(inflows[0]['expected_inflows']) if inflows else 0,
                "note": "Actuals tracking pending Monday CRM integration"
            }
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return {
                "month": date.today().strftime("%Y-%m"),
                "expected_inflows": 0,
                "note": "Database not initialized"
            }

    def get_monthly_cashflow(
        self,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> List[Dict]:
        """
        Get monthly cash flow projection.
        """
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
                monthly_inflows AS (
                    SELECT
                        DATE_TRUNC('month', due_date)::date as month,
                        SUM(amount) as inflows
                    FROM more_house.payment_schedule
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
                    COALESCE(i.inflows, 0) as inflows,
                    COALESCE(o.outflows, 0) as outflows,
                    COALESCE(i.inflows, 0) - COALESCE(o.outflows, 0) as net_cashflow,
                    SUM(COALESCE(i.inflows, 0) - COALESCE(o.outflows, 0))
                        OVER (ORDER BY m.month_start) as running_balance
                FROM months m
                LEFT JOIN monthly_inflows i ON i.month = m.month_start
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
                        %s::date,
                        %s::date + (%s * 7),
                        '1 week'::interval
                    )::date as week_start
                ),
                weekly_inflows AS (
                    SELECT
                        DATE_TRUNC('week', due_date)::date as week,
                        SUM(amount) as inflows,
                        COUNT(*) as payment_count
                    FROM more_house.payment_schedule
                    GROUP BY 1
                )
                SELECT
                    TO_CHAR(w.week_start, 'YYYY-MM-DD') as week_start,
                    TO_CHAR(w.week_start + 6, 'YYYY-MM-DD') as week_end,
                    COALESCE(wi.inflows, 0) as expected_inflows,
                    COALESCE(wi.payment_count, 0) as payments_due
                FROM weeks w
                LEFT JOIN weekly_inflows wi ON wi.week = w.week_start
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
                    ps.due_date,
                    ps.amount,
                    ps.payment_type,
                    ps.status
                FROM more_house.payment_schedule ps
                JOIN more_house.contracts c ON c.id = ps.contract_id
                WHERE ps.due_date BETWEEN %s AND %s
                ORDER BY ps.due_date
            """
            return execute_query(query, (start_date, end_date))
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    def get_overdue_payments(self) -> List[Dict]:
        """Get overdue payments (when actuals are tracked)."""
        try:
            from utils.db_connection import execute_query

            query = """
                SELECT
                    ps.id,
                    c.room_id,
                    c.resident_name,
                    ps.due_date,
                    ps.amount,
                    CURRENT_DATE - ps.due_date as days_overdue
                FROM more_house.payment_schedule ps
                JOIN more_house.contracts c ON c.id = ps.contract_id
                WHERE ps.status = 'pending'
                AND ps.due_date < CURRENT_DATE
                ORDER BY ps.due_date
            """
            return execute_query(query)
        except Exception as e:
            logger.warning(f"DB not ready: {e}")
            return []

    @staticmethod
    def generate_payment_schedule(
        contract_id: int,
        total_value: float,
        start_date: date,
        end_date: date,
        payment_plan: str
    ) -> List[Dict]:
        """
        Generate payment schedule based on contract and payment plan.
        This is used when importing contracts to create expected payments.
        """
        payments = []
        rule = CashFlowService.PAYMENT_PLAN_RULES.get(
            payment_plan,
            {"type": "monthly", "timing": "start_of_month"}
        )

        if rule["type"] == "upfront":
            # Single payment at start
            payments.append({
                "contract_id": contract_id,
                "due_date": start_date,
                "amount": total_value,
                "payment_type": "rent",
                "status": "pending"
            })

        elif rule["type"] == "monthly":
            # Monthly installments
            current = start_date.replace(day=1)
            months = 0
            while current <= end_date:
                months += 1
                current = (current + timedelta(days=32)).replace(day=1)

            monthly_amount = round(total_value / months, 2)

            current = start_date.replace(day=1)
            while current <= end_date:
                payments.append({
                    "contract_id": contract_id,
                    "due_date": current,
                    "amount": monthly_amount,
                    "payment_type": "rent",
                    "status": "pending"
                })
                current = (current + timedelta(days=32)).replace(day=1)

        elif rule["type"] == "agent":
            # Agent payment (e.g., Studentluxe) - assume monthly remittance
            current = start_date.replace(day=1)
            months = 0
            while current <= end_date:
                months += 1
                current = (current + timedelta(days=32)).replace(day=1)

            monthly_amount = round(total_value / months, 2)

            current = start_date.replace(day=1)
            while current <= end_date:
                payments.append({
                    "contract_id": contract_id,
                    "due_date": current + timedelta(days=14),  # Mid-month for agent remit
                    "amount": monthly_amount,
                    "payment_type": "agent_remit",
                    "status": "pending"
                })
                current = (current + timedelta(days=32)).replace(day=1)

        return payments
