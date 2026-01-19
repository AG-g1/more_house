# More House - Occupancy & Cash Flow Management

Dashboard for tracking room occupancy and cash flow projections for More House student accommodation (120 units).

## Features

### Occupancy Movement Tracker
- Monthly overview of projected move-ins and move-outs
- Weekly drill-down for granular planning
- Net occupancy change per period
- Sales priority list: rooms becoming vacant with no follow-on booking

### Cash Flow View
- Monthly cash inflows (rent payments) and outflows (OPEX)
- Expected vs actual payment tracking
- Overdue payment alerts
- Running balance forecast

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Frontend**: React 19, Vite, Tailwind CSS
- **Database**: TimescaleDB (PostgreSQL) - `more_house` schema
- **Integrations**: Monday CRM, Excel imports

## Data Sources

### Monday CRM Boards

| Board | ID | Purpose |
|-------|-----|---------|
| MH - Unit Schedule | 9376648770 | Room inventory (120 units) |
| Qualified | 9188309936 | CRM deals - converted = active bookings |
| Won Deals (TBD) | - | Payment schedules and tracking |

### Excel Files

| File | Content |
|------|---------|
| Installments.xlsx | Payment schedules with actual due dates |
| More House - Occupancy Report.xlsx | Room data, contracts, cash flow projections |

## Database Schema

### Tables

**`rooms`** - 120 unit inventory
```
room_id, floor, category, sqm, weekly_rate, mattress_size
```

**`contracts`** - Booking contracts
```
room_id, resident_name, start_date, end_date,
total_value, payment_plan, status, nationality, university
```

**`payment_schedule`** - Expected payments (actual due dates from Monday/Excel)
```
contract_id, installment_number, due_date, amount, status
```
- `installment_number`: 0 = Booking Fee, 1-5 = Installments

**`payments_received`** - Actual payments received
```
contract_id, payment_date, amount, payment_method, allocated_to_installment
```

**`opex_budget`** - Operating expenses by month
```
month_date, category, amount
```

### Data Flow

```
┌─────────────────────┐     ┌─────────────────────┐
│  Installments.xlsx  │     │  Monday CRM Boards  │
│  (Won Deals export) │     │  (future live sync) │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          ▼                            ▼
    ┌─────────────────────────────────────────┐
    │         import_installments.py          │
    └─────────────────┬───────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌─────────┐ ┌───────────┐ ┌──────────────────┐
    │  rooms  │ │ contracts │ │ payment_schedule │
    └─────────┘ └───────────┘ └──────────────────┘
```

## Payment Structure

Payments are **termly** (not monthly). Typical schedule:

| Installment | Timing | Example Date |
|-------------|--------|--------------|
| Booking Fee | At signing | Jul-Aug |
| Installment 1 | Start of term | Aug |
| Installment 2 | Autumn | Oct 9 |
| Installment 3 | Winter | Jan 9 |
| Installment 4 | Spring | Apr 10 |
| Installment 5 | (if needed) | Variable |

### Payment Plans

| Plan | Structure | Count |
|------|-----------|-------|
| Installments | Booking fee + 4 termly payments | 91 |
| Single Payment | Booking fee + 1 full payment | 15 |
| Studentluxe | 3-4 agent remits, no booking fee | 13 |
| Special Payment Terms | Custom schedule | 7 |

## Quick Start

### 1. Setup Python Environment

```bash
cd /Users/alexgilts/PycharmProjects/more_house
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python scripts/init_db.py
```

### 3. Import Data

```bash
# Import payment schedules from Installments.xlsx
python scripts/import_installments.py

# Or specify a different file:
python scripts/import_installments.py /path/to/file.xlsx

# Clear and reimport:
python scripts/import_installments.py --clear
```

### 4. Start Backend

```bash
uvicorn backend.main:app --reload --port 8001
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5174 in your browser.

## Project Structure

```
more_house/
├── backend/                 # FastAPI backend
│   ├── main.py              # API entry point (port 8001)
│   ├── api/
│   │   ├── occupancy.py     # Occupancy endpoints
│   │   └── cashflow.py      # Cash flow endpoints
│   ├── services/
│   │   ├── occupancy_service.py
│   │   └── cashflow_service.py
│   └── models/
│       └── schemas.py       # Pydantic schemas
├── frontend/                # React frontend (port 5174)
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── OccupancySummary.jsx
│   │       ├── OccupancyChart.jsx
│   │       ├── UpcomingVacancies.jsx
│   │       └── CashFlowChart.jsx
│   └── package.json
├── integrations/
│   ├── monday_client.py     # Monday CRM API client
│   └── excel_importer.py    # Excel import utilities
├── scripts/
│   ├── init_db.py           # Create database schema
│   ├── import_installments.py  # Import payment schedules
│   └── import_excel.py      # Import from occupancy report
├── utils/
│   └── db_connection.py     # Database connection helper
├── .env                     # Environment variables
├── .env.example             # Template for .env
└── requirements.txt
```

## API Endpoints

### Occupancy
- `GET /api/occupancy/summary` - Current occupancy (total, occupied, vacant, rate)
- `GET /api/occupancy/monthly` - Monthly move-ins/move-outs
- `GET /api/occupancy/weekly` - Weekly breakdown
- `GET /api/occupancy/vacancies/upcoming?days=30` - Upcoming vacancies (sales priority)
- `GET /api/occupancy/rooms` - All rooms with current status
- `GET /api/occupancy/rooms/{room_id}/timeline` - Room booking history

### Cash Flow
- `GET /api/cashflow/summary` - Current month summary (expected, received, overdue)
- `GET /api/cashflow/monthly` - Monthly projections with running balance
- `GET /api/cashflow/weekly` - Weekly breakdown
- `GET /api/cashflow/payments/expected` - Detailed payment schedule
- `GET /api/cashflow/payments/overdue` - Overdue payments list

## Environment Variables

```bash
# Database (TimescaleDB)
TIMESCALE_SERVICE_URL=postgres://user:pass@host:port/dbname?sslmode=require
DB_SCHEMA=more_house

# Monday CRM
MONDAY_API_TOKEN=eyJhbGci...
MONDAY_BOARD_ID_CONTRACTS=9376648770

# Application
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8001
```

## Monday CRM Integration

### Current Status
- ✅ API connection working
- ✅ Board discovery implemented
- ✅ MH - Unit Schedule board mapped (rooms)
- ✅ Qualified board mapped (bookings)
- ⏳ Payment tracking board (pending access)

### Test Monday Connection

```bash
python integrations/monday_client.py
```

## Development

### Reset Database

```bash
# Drop and recreate schema (caution: deletes all data)
python scripts/init_db.py --drop
python scripts/init_db.py
```

### Run Tests

```bash
# Backend
pytest

# Frontend
cd frontend && npm test
```

## Next Steps

1. **Payment Board Integration** - Connect to Monday board with payment tracking
2. **Actual vs Expected** - Track received payments against schedule
3. **OPEX Import** - Import operating expenses from budget Excel
4. **Alerts** - Email/Slack notifications for overdue payments
5. **Pipeline/Leads** - Sales funnel tracking from Qualified board
