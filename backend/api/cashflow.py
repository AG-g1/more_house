# backend/api/cashflow.py

from fastapi import APIRouter, Query
from typing import Optional
from backend.services.cashflow_service import CashFlowService

router = APIRouter()
service = CashFlowService()


@router.get("/summary")
async def get_cashflow_summary():
    """
    Get cash flow summary:
    - Current month inflows/outflows
    - Running balance
    - Forecast vs actual
    """
    return service.get_summary()


@router.get("/monthly")
async def get_monthly_cashflow(
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM)")
):
    """
    Get monthly cash flow view:
    - Inflows (rent payments, deposits)
    - Outflows (OPEX)
    - Net cash flow
    - Running balance
    """
    return service.get_monthly_cashflow(start_month, end_month)


@router.get("/weekly")
async def get_weekly_cashflow(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    weeks: int = Query(8, description="Number of weeks")
):
    """
    Get weekly cash flow for granular view.
    """
    return service.get_weekly_cashflow(start_date, weeks)


@router.get("/payments/expected")
async def get_expected_payments(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Get expected payment schedule based on contracts and payment plans.
    """
    return service.get_expected_payments(start_date, end_date)


@router.get("/payments/overdue")
async def get_overdue_payments():
    """
    Get list of overdue payments (when actuals are tracked).
    """
    return service.get_overdue_payments()
