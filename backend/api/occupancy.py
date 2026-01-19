# backend/api/occupancy.py

from fastapi import APIRouter, Query
from datetime import date, datetime
from typing import Optional
from backend.services.occupancy_service import OccupancyService

router = APIRouter()
service = OccupancyService()


@router.get("/summary")
async def get_occupancy_summary():
    """
    Get current occupancy summary:
    - Total rooms
    - Occupied rooms
    - Vacant rooms
    - Occupancy rate
    """
    return service.get_summary()


@router.get("/monthly")
async def get_monthly_overview(
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM)")
):
    """
    Get monthly occupancy movements:
    - Move-ins per month
    - Move-outs per month
    - Net change
    - Running occupancy
    """
    return service.get_monthly_overview(start_month, end_month)


@router.get("/weekly")
async def get_weekly_overview(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    weeks: int = Query(8, description="Number of weeks to show")
):
    """
    Get weekly occupancy movements for granular planning.
    """
    return service.get_weekly_overview(start_date, weeks)


@router.get("/vacancies/upcoming")
async def get_upcoming_vacancies(
    days: int = Query(30, description="Days to look ahead")
):
    """
    Get rooms becoming vacant with no follow-on booking.
    Priority list for sales team.
    """
    return service.get_upcoming_vacancies(days)


@router.get("/rooms")
async def get_all_rooms():
    """
    Get all rooms with current status and next event.
    """
    return service.get_all_rooms()


@router.get("/rooms/{room_id}/timeline")
async def get_room_timeline(room_id: str):
    """
    Get full booking timeline for a specific room.
    """
    return service.get_room_timeline(room_id)
