# More House - Session Handoff

## Project Overview
Dashboard for **More House** student accommodation (120 units) - tracking room occupancy, cash flow, and CRM activity.

**Live**: http://178.128.46.110/more_house/

## Tech Stack
- **Backend**: Python 3.12, FastAPI (port 8002)
- **Frontend**: React 19, Vite, Tailwind CSS (port 5174 dev / served by FastAPI in prod)
- **Database**: TimescaleDB (PostgreSQL) - `more_house` schema
- **Integrations**: Monday CRM (3 boards), Google Gemini API (ready)
- **Deployment**: DigitalOcean droplet (178.128.46.110), nginx, systemd, GitHub Actions CI/CD

## What Was Built

### 1. Monday CRM Live Sync
- **Script**: `scripts/sync_monday.py`
- **API**: `POST /api/sync/run` (background sync), `GET /api/sync/status`
- **Boards connected**:
  - `9376648770` - MH Unit Schedule (120 rooms)
  - `8606133913` - Won Deals (contracts, payment schedules, payments received)
  - `9188309936` - Qualified (viewings, leads)
- **Syncs**: Rooms, contracts, payment schedules, payments received
- Room ID normalization (M10 -> MEZZ 10)
- **Frontend**: "Sync Now" button with spinner and "Up to date" badge

### 2. Activity Table (Viewings & Contracts)
- **API**: `GET /api/activity/summary`
- Pulls viewings from both Qualified and Won Deals boards
- Pulls signed contracts from Won Deals board
- Shows counts for 1d, 3d, 7d, 1m, 3m periods
- Click on contract count to expand and see: name, unit, sign date, start/end dates, weekly rate
- **Files**: `backend/api/activity.py`, `frontend/src/components/ActivityTable.jsx`

### 3. Dashboard Page
- **Path**: `/`
- Occupancy summary cards (occupied/120, vacant, avg weekly rent, net income signed)
- Activity table (viewings + contracts signed)
- Occupancy trend chart (area) + move-in/move-out bars
- Weekly schedule table
- **Files**: `frontend/src/pages/OccupancyPage.jsx`, `frontend/src/components/OccupancyChart.jsx`

### 4. Cash Flow Page
- **Path**: `/cashflow`
- Monthly bar chart of expected income
- Summary cards: Total Expected, Already Received, Payments Due
- **File**: `frontend/src/pages/CashFlowPage.jsx`

### 5. Rooms Map Page
- **Path**: `/rooms-map`
- Visual building with floors stacked vertically, rooms as clickable cards
- Color-coded by category (Classic, Deluxe, etc.)
- **File**: `frontend/src/pages/RoomsMapPage.jsx`

### 6. Production Deployment
- Frontend built with `/more_house/` base path
- FastAPI serves both API and frontend static files
- Nginx reverse proxy on DigitalOcean (`/more_house/` -> port 8002)
- Systemd service (`more-house.service`) with auto-restart
- GitHub Actions auto-deploy on push to main
- **Files**: `deploy/`, `.github/workflows/deploy.yml`, `frontend/src/config.js`

## Database State
- 120 rooms (synced from Monday Unit Schedule)
- 147 contracts (synced from Monday Won Deals)
- 459 payment schedule entries
- 307 payments received
- Current occupancy: 107 rooms (89.2%)

## API Endpoints
- `GET /api/occupancy/summary` - Occupancy metrics
- `GET /api/occupancy/weekly` - Weekly move-ins/outs
- `GET /api/occupancy/rooms` - All rooms with status
- `GET /api/occupancy/rooms/timelines` - Room contract timelines
- `GET /api/cashflow/monthly` - Monthly income projections
- `GET /api/cashflow/payments/overdue` - Overdue payments
- `GET /api/cashflow/payments/schedule` - Monthly payment aggregation
- `GET /api/sync/status` - Sync status + Monday board info + DB counts
- `POST /api/sync/run` - Trigger Monday sync
- `GET /api/activity/summary` - Viewings/contracts by period
- `GET /api/health` - Health check

## Environment Variables (.env)
```
TIMESCALE_SERVICE_URL=postgres://...
DB_SCHEMA=more_house
MONDAY_API_TOKEN=eyJ...
MONDAY_BOARD_ID_CONTRACTS=9376648770
MONDAY_BOARD_ID_PAYMENTS=8606133913
GOOGLE_AI_API_KEY=AIzaSyD6...
API_PORT=8002
```

## How to Run

### Local Development
```bash
# Backend
cd /Users/alexgilts/PycharmProjects/more_house
source venv/bin/activate
uvicorn backend.main:app --reload --port 8002

# Frontend (separate terminal)
cd frontend
npm run dev

# Sync from Monday
python scripts/sync_monday.py
```

### Production
```bash
# On server (178.128.46.110)
systemctl restart more-house
systemctl status more-house
journalctl -u more-house -f
```

### Deploy
Push to `main` branch -> GitHub Actions auto-deploys.

## Key Architecture Decisions
- Backend port 8002 (8001 is used by crypto trading project)
- Frontend uses centralized `config.js` for API_BASE (`/more_house/api`)
- Production: FastAPI serves both API and built frontend (no separate web server for frontend)
- Nginx location block for IP-based access (not domain-based)
- `frontend/dist/` is committed to git (server has no Node.js)

## Next Steps
1. OPEX import from budget Excel
2. Email/Slack alerts for overdue payments
3. Sales pipeline tracking from Qualified board
4. Building illustrations with Google Gemini
