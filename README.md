# More House - Occupancy & Cash Flow Management

Dashboard for tracking room occupancy and cash flow projections for More House student accommodation.

## Features

### Occupancy Movement Tracker
- Monthly overview of projected move-ins and move-outs
- Weekly drill-down for granular planning
- Net occupancy change per period
- Sales priority list: rooms becoming vacant with no follow-on booking

### Cash Flow View
- Monthly cash inflows (rent payments) and outflows (OPEX)
- Running balance forecast
- Payment schedule based on contract payment plans

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Frontend**: React 19, Vite, Tailwind CSS
- **Database**: TimescaleDB (PostgreSQL)
- **Integrations**: Monday CRM (coming soon)

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
# Create schema and tables
python scripts/init_db.py
```

### 3. Import Excel Data

```bash
# Import from occupancy report
python scripts/import_excel.py "/Users/alexgilts/Library/Mobile Documents/com~apple~CloudDocs/AG Work/SAV Group/More House - Occupancy Report - 29 Nov 2025 (with Forecast).xlsx"
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

Open http://localhost:5173 in your browser.

## Project Structure

```
more_house/
├── backend/                 # FastAPI backend
│   ├── main.py              # API entry point
│   ├── api/                 # API routes
│   │   ├── occupancy.py     # Occupancy endpoints
│   │   └── cashflow.py      # Cash flow endpoints
│   ├── services/            # Business logic
│   │   ├── occupancy_service.py
│   │   └── cashflow_service.py
│   └── models/              # Pydantic schemas
│       └── schemas.py
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.jsx          # Main app
│   │   └── components/      # React components
│   └── package.json
├── integrations/            # External integrations
│   ├── monday_client.py     # Monday CRM API
│   └── excel_importer.py    # Excel import
├── scripts/                 # Utility scripts
│   ├── init_db.py           # Database setup
│   └── import_excel.py      # Data import
├── utils/                   # Shared utilities
│   └── db_connection.py     # Database connection
├── .env                     # Environment variables
└── requirements.txt         # Python dependencies
```

## API Endpoints

### Occupancy
- `GET /api/occupancy/summary` - Current occupancy summary
- `GET /api/occupancy/monthly` - Monthly move-ins/move-outs
- `GET /api/occupancy/weekly` - Weekly breakdown
- `GET /api/occupancy/vacancies/upcoming` - Rooms becoming vacant (sales priority)
- `GET /api/occupancy/rooms` - All rooms with status
- `GET /api/occupancy/rooms/{room_id}/timeline` - Room booking timeline

### Cash Flow
- `GET /api/cashflow/summary` - Cash flow summary
- `GET /api/cashflow/monthly` - Monthly inflows/outflows
- `GET /api/cashflow/weekly` - Weekly breakdown
- `GET /api/cashflow/payments/expected` - Expected payment schedule
- `GET /api/cashflow/payments/overdue` - Overdue payments

## Database Schema

The `more_house` schema contains:

- `rooms` - Room inventory (120 units)
- `contracts` - Booking contracts with dates and payment plans
- `payment_schedule` - Expected payment dates derived from contracts
- `opex_budget` - Operating expense budget by month

## Payment Plan Logic

| Plan | Cash Flow Timing |
|------|------------------|
| Single Payment | 100% at contract start |
| Installments | Monthly payments |
| Studentluxe | Agent remits mid-month |
| Special Payment Terms | Custom (needs per-contract definition) |

## Next Steps

1. **Monday CRM Integration**: Add API token to `.env` and map board columns
2. **Actual Payments**: Track received vs expected payments
3. **Deposits**: Add deposit tracking when structure is defined
4. **Pipeline/Leads**: Add prospect tracking for sales funnel

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database (same as crypto project)
TIMESCALE_SERVICE_URL=postgres://...

# Monday CRM
MONDAY_API_TOKEN=your_token
MONDAY_BOARD_ID_CONTRACTS=board_id
MONDAY_BOARD_ID_PAYMENTS=board_id
```
