# More House - Build Prompt

## Project Context

This is a **standalone project** for More House student accommodation (120 rooms in London). It is NOT related to the crypto_trading project.

**Project location:** `/Users/alexgilts/PycharmProjects/more_house`
**Live URL:** http://178.128.46.110/more_house/
**GitHub:** https://github.com/AG-g1/more_house

## Current State

### Working Features
- Dashboard with occupancy summary, activity table, trend charts, weekly schedule
- Cash flow page with monthly projections and payment tracking
- Rooms list with filtering
- Rooms map with visual building layout
- Monday CRM sync (rooms, contracts, payments) with "Sync Now" button
- Activity tracking: viewings and contracts signed (1d/3d/7d/1m/3m from Monday)
- Auto-deploy via GitHub Actions (push to main -> deploys to server)

### Tech Stack
- **Backend**: Python 3.12, FastAPI on port 8002
- **Frontend**: React 19, Vite, Tailwind CSS (base path `/more_house/`)
- **Database**: TimescaleDB (PostgreSQL) - `more_house` schema
- **Server**: DigitalOcean droplet (178.128.46.110), nginx, systemd
- **CI/CD**: GitHub Actions auto-deploy on push to main

### Data Sources
- **Monday CRM**: 3 boards (Unit Schedule, Won Deals, Qualified)
- **Database**: 120 rooms, 147 contracts, 459 payment schedules, 307 payments received
- **Excel**: Installments.xlsx (backup import)

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

## How to Run

### Local Development
```bash
# Backend
source venv/bin/activate
uvicorn backend.main:app --reload --port 8002

# Frontend (separate terminal)
cd frontend && npm run dev

# Sync Monday data
python scripts/sync_monday.py
```

### Production Deployment
Push to `main` branch triggers auto-deploy. Or manually:
```bash
ssh root@178.128.46.110
systemctl restart more-house
```

### Build Frontend for Production
```bash
cd frontend && npx vite build
# Commit dist/ and push to deploy
```

## Environment Variables (.env - not in git)
```
TIMESCALE_SERVICE_URL=postgres://...
DB_SCHEMA=more_house
MONDAY_API_TOKEN=eyJ...
MONDAY_BOARD_ID_CONTRACTS=9376648770
MONDAY_BOARD_ID_PAYMENTS=8606133913
GOOGLE_AI_API_KEY=AIzaSyD6...
API_PORT=8002
```

## What Needs Doing Next

1. **OPEX Import** - Import operating expenses from budget Excel
2. **Alerts** - Email/Slack notifications for overdue payments
3. **Pipeline/Leads** - Sales funnel tracking from Qualified board
4. **Image Generation** - Building illustrations with Google Gemini (API key configured)

## Important Notes
- Backend port is 8002 (not 8001, which is used by crypto trading)
- Frontend API calls use centralized `config.js` (`/more_house/api`)
- `frontend/dist/` is committed to git because the server has no Node.js
- `.env` must be manually copied to server (not in git)
- GitHub secret `SSH_PRIVATE_KEY` (ed25519) is configured for auto-deploy

Read `README.md` for full technical documentation.
