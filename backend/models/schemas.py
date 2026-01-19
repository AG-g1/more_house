# backend/models/schemas.py

from pydantic import BaseModel
from datetime import date
from typing import Optional, List
from enum import Enum


class ContractStatus(str, Enum):
    PROSPECT = "prospect"
    UNDER_DISCUSSION = "under_discussion"
    SIGNED = "signed"
    ACTIVE = "active"
    ENDING = "ending"
    TERMINATED = "terminated"
    COMPLETED = "completed"


class PaymentPlan(str, Enum):
    SINGLE_PAYMENT = "Single Payment"
    INSTALLMENTS = "Installments"
    STUDENTLUXE = "Studentluxe"
    SPECIAL = "Special Payment Terms"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"


class RoomCategory(str, Enum):
    STANDARD = "Standard"
    CLASSIC = "Classic"
    DELUXE = "Deluxe"
    DELUXE_MEZZANINE = "Deluxe Mezzanine"


# Room schemas
class RoomBase(BaseModel):
    room_id: str
    floor: str
    category: RoomCategory
    sqm: float
    weekly_rate: float


class RoomResponse(RoomBase):
    current_tenant: Optional[str] = None
    status: str
    next_available: Optional[date] = None


# Contract schemas
class ContractBase(BaseModel):
    room_id: str
    resident_name: str
    start_date: date
    end_date: date
    weekly_rate: float
    total_value: float
    payment_plan: PaymentPlan


class ContractCreate(ContractBase):
    nationality: Optional[str] = None
    university: Optional[str] = None
    source: Optional[str] = None


class ContractResponse(ContractBase):
    id: int
    status: ContractStatus
    weeks_booked: float
    created_at: date


# Payment schemas
class PaymentBase(BaseModel):
    contract_id: int
    due_date: date
    amount: float
    payment_type: str


class PaymentResponse(PaymentBase):
    id: int
    status: PaymentStatus
    paid_date: Optional[date] = None
    paid_amount: Optional[float] = None


# Occupancy summary schemas
class OccupancySummary(BaseModel):
    total_rooms: int
    occupied: int
    vacant: int
    occupancy_rate: float
    as_of: date


class MonthlyOccupancy(BaseModel):
    month: str
    move_ins: int
    move_outs: int
    net_change: int
    start_occupancy: Optional[int] = None
    end_occupancy: Optional[int] = None


class UpcomingVacancy(BaseModel):
    room_id: str
    current_tenant: str
    vacates_on: date
    days_until_vacant: int
    weekly_rate: float
    status: str


# Cash flow schemas
class MonthlyCashFlow(BaseModel):
    month: str
    inflows: float
    outflows: float
    net_cashflow: float
    running_balance: float


class WeeklyCashFlow(BaseModel):
    week_start: str
    week_end: str
    expected_inflows: float
    payments_due: int
