# More House - Occupancy & Cash Flow Management

Dashboard for tracking room occupancy and cash flow projections for More House student accommodation (120 units).

**Live**: http://178.128.46.110/more_house/

## Features

### Dashboard (Home Page)
- Occupancy summary: total rooms, occupied, vacant, occupancy rate
- Average weekly rent and net income signed
- **Activity table**: Viewings and contracts signed in last 1d/3d/7d/1m/3m (live from Monday CRM)
- Expandable contract details (name, unit, sign date, start/end dates, rate)
- Occupancy trend chart with move-in/move-out bars
- Weekly schedule table with net changes

### Cash Flow View
- Monthly cash inflows (rent payments)
- Expected vs received payment tracking
- Payment schedule by month
- Overdue payment alerts

### Rooms List
- All 120 rooms with current status
- Filter by floor, category, status

### Rooms Map
- Visual building layout by floor
- Color-coded by room category
- Shows occupancy status per room

### Monday CRM Sync
- **Sync Now** button in dashboard header
- Syncs rooms from MH - Unit Schedule board
- Syncs contracts and payments from Won Deals board
- Background sync via API endpoint

## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Frontend**: React 19, Vite, Tailwind CSS
- **Database**: TimescaleDB (PostgreSQL) - `more_house` schema
- **Integrations**: Monday CRM (live sync)
- **Deployment**: DigitalOcean droplet, nginx, systemd
- **CI/CD**: GitHub Actions auto-deploy on push to main

## Data Sources

### Monday CRM Boards

| Board | ID | Purpose |
|-------|-----|---------|
| MH - Unit Schedule | 9376648770 | Room inventory (120 units) |
| Won Deals | 8606133913 | Contracts, payment schedules, payment tracking |
| Qualified | 9188309936 | CRM deals, viewings, leads |

## Database Schema

### Tables

**`rooms`** - 120 unit inventory
```
room_id, floor, category, sqm, weekly_rate, mattress_size
```

**`contracts`** - Booking contracts
```
monday_id, room_id, resident_name, start_date, end_date,
total_value, weekly_rate, payment_plan, status, nationality, university
```

**`payment_schedule`** - Expected payments (actual due dates from Monday)
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

## Quick Start (Local Development)

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

### 3. Import / Sync Data

```bash
# Sync from Monday CRM (preferred)
python scripts/sync_monday.py

# Or import from Excel
python scripts/import_installments.py
```

### 4. Start Backend

```bash
source venv/bin/activate
uvicorn backend.main:app --reload --port 8002
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5174 in your browser.

## Deployment

### Production URL
http://178.128.46.110/more_house/

### Auto-Deploy
Push to `main` branch triggers GitHub Actions which:
1. Rsync files to DigitalOcean server
2. Install Python dependencies
3. Restart systemd service

### Server Setup
- **Server**: DigitalOcean droplet at 178.128.46.110
- **Nginx**: Reverse proxy `/more_house/` to uvicorn on port 8002
- **Systemd**: `more-house.service` runs the FastAPI backend
- **Config files**: `deploy/nginx-more-house.conf`, `deploy/more-house.service`

### Manual Server Commands
```bash
# Check service status
systemctl status more-house

# Restart backend
systemctl restart more-house

# View logs
journalctl -u more-house -f

# Nginx config
/etc/nginx/sites-available/more-house
```

## Project Structure

```
more_house/
├── backend/                 # FastAPI backend
│   ├── main.py              # API entry point + static file serving
│   ├── api/
│   │   ├── occupancy.py     # Occupancy endpoints
│   │   ├── cashflow.py      # Cash flow endpoints
│   │   ├── sync.py          # Monday sync endpoints
│   │   └── activity.py      # Viewings & contracts activity
│   ├── services/
│   │   ├── occupancy_service.py
│   │   └── cashflow_service.py
│   └── models/
│       └── schemas.py       # Pydantic schemas
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── config.js        # Shared API_BASE and BASE_PATH
│   │   ├── components/
│   │   │   ├── SyncStatusBar.jsx     # Sync Now button
│   │   │   ├── ActivityTable.jsx     # Viewings/contracts table
│   │   │   ├── OccupancySummary.jsx  # Summary stat cards
│   │   │   ├── OccupancyChart.jsx    # Occupancy trend chart
│   │   │   └── CashFlowChart.jsx
│   │   └── pages/
│   │       ├── OccupancyPage.jsx     # Dashboard (home)
│   │       ├── CashFlowPage.jsx
│   │       ├── RoomsPage.jsx
│   │       └── RoomsMapPage.jsx
│   ├── dist/                # Production build (committed)
│   ├── vite.config.js
│   └── package.json
├── integrations/
│   ├── monday_client.py     # Monday CRM API client
│   └── excel_importer.py    # Excel import utilities
├── scripts/
│   ├── init_db.py           # Create database schema
│   ├── sync_monday.py       # Sync rooms + contracts from Monday
│   ├── import_installments.py  # Import from Excel
│   └── import_excel.py      # Import from occupancy report
├── deploy/
│   ├── nginx-more-house.conf   # Nginx location block
│   └── more-house.service      # Systemd service file
├── utils/
│   └── db_connection.py     # Database connection helper
├── .github/workflows/
│   └── deploy.yml           # Auto-deploy on push to main
├── .env                     # Environment variables (not in git)
└── requirements.txt
```

## API Endpoints

### Occupancy
- `GET /api/occupancy/summary` - Current occupancy (total, occupied, vacant, rate)
- `GET /api/occupancy/monthly` - Monthly move-ins/move-outs
- `GET /api/occupancy/weekly` - Weekly breakdown
- `GET /api/occupancy/vacancies/upcoming?days=30` - Upcoming vacancies
- `GET /api/occupancy/rooms` - All rooms with current status
- `GET /api/occupancy/rooms/timelines` - All rooms with contract timelines
- `GET /api/occupancy/rooms/{room_id}/timeline` - Room booking history

### Cash Flow
- `GET /api/cashflow/summary` - Current month summary
- `GET /api/cashflow/monthly` - Monthly projections
- `GET /api/cashflow/weekly` - Weekly breakdown
- `GET /api/cashflow/payments/expected` - Detailed payment schedule
- `GET /api/cashflow/payments/overdue` - Overdue payments list
- `GET /api/cashflow/payments/schedule` - Monthly payment aggregation

### Sync
- `GET /api/sync/status` - Sync status, Monday board info, DB counts
- `POST /api/sync/run` - Trigger Monday sync (runs in background)

### Activity
- `GET /api/activity/summary` - Viewings and contracts signed by period (1d/3d/7d/1m/3m)

## Environment Variables

```bash
# Database (TimescaleDB)
TIMESCALE_SERVICE_URL=postgres://user:pass@host:port/dbname?sslmode=require
DB_SCHEMA=more_house

# Monday CRM
MONDAY_API_TOKEN=eyJhbGci...
MONDAY_BOARD_ID_CONTRACTS=9376648770
MONDAY_BOARD_ID_PAYMENTS=8606133913

# Application
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8002
```

## Next Steps

1. **OPEX Import** - Import operating expenses from budget Excel
2. **Alerts** - Email/Slack notifications for overdue payments
3. **Pipeline/Leads** - Sales funnel tracking from Qualified board
4. **Image Generation** - Building illustrations with Google Gemini
