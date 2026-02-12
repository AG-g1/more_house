# More House - Session Handoff

## Project Overview
Dashboard for **More House** student accommodation (120 units) - tracking room occupancy and cash flow.

## Tech Stack
- **Backend**: Python 3.12, FastAPI (port 8001)
- **Frontend**: React 19, Vite, Tailwind CSS (port 5174)
- **Database**: TimescaleDB (PostgreSQL) - `more_house` schema
- **Integrations**: Monday CRM (live sync), Google Gemini API (ready)

## What Was Built This Session

### 1. Monday CRM Live Sync
- **Script**: `scripts/sync_monday.py`
- **Boards connected**:
  - `8606133913` - Won Deals/Installments (contracts, payments)
  - `9376648770` - MH Unit Schedule (120 rooms)
- **Syncs**: Contracts, payment schedules, rooms with proper ID normalization (M10 → MEZZ 10)
- **Usage**: `python scripts/sync_monday.py` (syncs both boards)

### 2. Dashboard Page (renamed from Occupancy)
- **Path**: `/`
- **Shows**:
  - Occupancy (103/120), Vacant (17), Avg Weekly Rent (£1,049), Net Income Signed (£4.32M)
  - Split chart: Top = Occupancy trend (area), Bottom = Move-ins/outs (bars)
- **Files**: `frontend/src/pages/OccupancyPage.jsx`, `frontend/src/components/OccupancyChart.jsx`

### 3. Rooms Map Page
- **Path**: `/rooms-map`
- **Shows**: Visual building with floors stacked vertically, rooms as clickable cards
- **Color-coded** by category (Classic, Deluxe, etc.), shows occupancy status
- **File**: `frontend/src/pages/RoomsMapPage.jsx`

### 4. Cash Flow Page
- **Path**: `/cashflow`
- **Shows**: Simple bar chart of expected income by month (next 12 months)
- **Summary cards**: Total Expected, Already Received, Payments Due
- **File**: `frontend/src/pages/CashFlowPage.jsx`

### 5. Sidebar Navigation
- Dashboard, Cash Flow, Rooms, Rooms Map
- **File**: `frontend/src/components/Layout/Sidebar.jsx`

## Database Schema
Tables in `more_house` schema:
- `rooms` - 120 units (room_id, floor, category, sqm, weekly_rate, mattress_size)
- `contracts` - Bookings (monday_id, room_id, resident_name, dates, total_value, weekly_rate, payment_plan)
- `payment_schedule` - Expected payments (contract_id, installment_number, due_date, amount, status)
- `payments_received` - Actual payments received

## API Endpoints
- `GET /api/occupancy/summary` - Current occupancy + metrics
- `GET /api/occupancy/monthly` - Monthly move-ins/outs
- `GET /api/occupancy/rooms` - All 120 rooms with status
- `GET /api/cashflow/monthly` - Expected income by month

## Environment Variables (.env)
```
TIMESCALE_SERVICE_URL=postgres://...
DB_SCHEMA=more_house
MONDAY_API_TOKEN=eyJ...
MONDAY_BOARD_ID_CONTRACTS=9376648770
MONDAY_BOARD_ID_PAYMENTS=8606133913
GOOGLE_AI_API_KEY=AIzaSyD6JR3yHi6BUITehbNxmLQAy0tsDRtsPTw
```

## Current Data
- 120 rooms (synced from Monday Unit Schedule)
- 137 contracts (synced from Monday Won Deals)
- 433 payment schedule entries
- Current occupancy: 103 rooms (85.8%)
- Net income signed: £4,321,632

## Numbers Comparison (Dashboard vs Monday)
- **Avg Weekly Rent**: £1,049 (Monday: £1,041) - close
- **Net Income**: £4,321,632 (Monday: £4,352,412) - ~£30K diff, likely formula differences

## What We Were About To Do
**Generate images with Google Gemini** to add visual flair to the site.
- API key is configured and tested
- Available models: Imagen 4.0, Gemini 2.5 Flash
- Ideas discussed:
  1. Building illustration for Rooms Map
  2. Dashboard hero image
  3. Room category images
  4. Floor icons

## How to Run
```bash
# Backend
cd /Users/alexgilts/PycharmProjects/more_house
source venv/bin/activate
uvicorn backend.main:app --reload --port 8001

# Frontend
cd frontend
npm run dev

# Sync from Monday
python scripts/sync_monday.py
```

## Key Files Modified
- `backend/services/occupancy_service.py` - Added avg_weekly_rent, total_signed_value
- `backend/main.py` - Added CORS for port 5174
- `scripts/sync_monday.py` - Full Monday sync with room ID normalization
- `frontend/src/pages/OccupancyPage.jsx` - Dashboard with split charts
- `frontend/src/pages/CashFlowPage.jsx` - Simple income bar chart
- `frontend/src/pages/RoomsMapPage.jsx` - Building visualization
- `frontend/src/components/OccupancySummary.jsx` - 4 metric cards
- `frontend/src/components/OccupancyChart.jsx` - Split area + bar charts

## Next Steps
1. Generate images with Gemini for the site
2. User can share this file in new context to continue
