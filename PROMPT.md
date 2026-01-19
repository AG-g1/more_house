# More House - Build Prompt

## Project Context

This is a **new standalone project** for More House student accommodation (120 rooms in London). It is NOT related to the crypto_trading project in the parent directory.

**Project location:** `/Users/alexgilts/PycharmProjects/more_house`

## What I Need Built

A dashboard with two main views:

### 1. Occupancy Movement Tracker
- Monthly overview showing projected move-ins and move-outs based on signed contracts
- Weekly drill-down for more granular planning
- Net occupancy change per period (move-ins minus move-outs)
- **Sales Priority List**: Rooms becoming vacant with no follow-on booking (this is critical - sales team needs to know which rooms to fill)

### 2. Cash Flow View
- Monthly cash inflows (rent payments) and outflows (OPEX)
- Running balance to forecast liquidity
- Expected vs actual payment tracking
- Overdue payment alerts

## Data Sources

### Primary: Monday CRM
- **MH - Unit Schedule** (Board ID: 9376648770) - Room inventory
- **Qualified** (Board ID: 9188309936) - Bookings (Deal Stage = "10. Converted")
- **Won Deals board** (access pending) - Payment schedules with actual due dates

### Backup: Excel Files
Located in: `/Users/alexgilts/Library/Mobile Documents/com~apple~CloudDocs/AG Work/SAV Group/`
- `Installments.xlsx` - Payment schedules (131 contracts with booking fees + installments)
- `More House - Occupancy Report - 29 Nov 2025 (with Forecast).xlsx` - Room data, contracts

## Key Business Rules

### Payment Structure (IMPORTANT - Not Monthly!)
Payments are **termly**, not monthly:
- Booking Fee: At signing (Jul-Aug)
- Installment 1: Start of term (Aug)
- Installment 2: Autumn (Oct 9)
- Installment 3: Winter (Jan 9)
- Installment 4: Spring (Apr 10)
- Installment 5: If needed (variable)

### Payment Plans
| Plan | Structure |
|------|-----------|
| Installments | Booking fee + 4 termly payments |
| Single Payment | Booking fee + 1 full payment |
| Studentluxe | 3-4 agent remits, no booking fee |
| Special Payment Terms | Custom schedule |

## Current State

### Done
- Project structure created (FastAPI backend, React frontend)
- Database schema designed (`more_house` schema in existing TimescaleDB)
- Monday CRM client implemented and tested
- Excel importer for Installments.xlsx ready
- Basic React components scaffolded

### Not Done
- Database tables not yet created (run `python scripts/init_db.py`)
- No data imported yet
- Frontend components need to be connected to real API
- Monday sync not complete (waiting for payment board access)

## Technical Details

- **Backend**: FastAPI on port 8001
- **Frontend**: React 19 + Vite + Tailwind on port 5174
- **Database**: TimescaleDB (same instance as crypto project, different schema)
- **Monday API Token**: Already in `.env`

## To Get Started

```bash
cd /Users/alexgilts/PycharmProjects/more_house
source venv/bin/activate

# 1. Initialize database
python scripts/init_db.py

# 2. Import data (use Excel until Monday board is ready)
python scripts/import_installments.py

# 3. Start backend
uvicorn backend.main:app --reload --port 8001

# 4. Start frontend (in another terminal)
cd frontend && npm run dev
```

## What I Want You To Do

1. Make sure the database is initialized and working
2. Import data from Installments.xlsx
3. Get the backend API returning real data
4. Build out the frontend dashboard with:
   - Occupancy summary cards (total rooms, occupied, vacant, rate)
   - Monthly occupancy chart (move-ins vs move-outs)
   - Upcoming vacancies list (sales priority)
   - Cash flow chart (monthly inflows/outflows)
5. Make it look professional and clean

Read `README.md` for full technical documentation.
