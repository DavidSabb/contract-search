# GovContract Search

A full-stack government contract search platform built with **Django + React** that aggregates active procurement opportunities from Canadian and US federal government APIs into a single, unified search interface.

---

## Overview

GovContract Search allows users to search plain-English terms (e.g. "packaging", "construction", "IT consulting") and instantly retrieve relevant, active government contract opportunities from 4 official sources — 2 Canadian and 2 American — ranked by relevance and filtered to show only open/active contracts by default.

---

## Features

- **Unified search** across 4 government procurement APIs simultaneously
- **Relevance scoring** — results ranked by how closely the contract matches your search term, not just keyword presence
- **Active contracts only** by default — completed and closed contracts are hidden unless explicitly toggled on
- **Query expansion** — searches automatically include synonyms and related procurement terminology
- **Source filtering** — filter results by data source (ProcureData, Open Canada, SAM.gov, USASpending)
- **Bilingual support** — Canadian contracts returned in both English and French fields
- **Normalized results** — all contracts from all sources displayed in a consistent format
- **Relevance badge** — each result shows a % match score
- **Bookmarkable searches** — search state stored in URL params (`?q=packaging&page=1`)
- **No completed contracts** — date-based filtering ensures expired solicitations are excluded

---

## Data Sources

| Source | Country | Type | Auth |
|---|---|---|---|
| [ProcureData](https://www.procuredata.ca/) | 🇨🇦 Canada | Federal tenders, contracts, awards | RapidAPI key |
| [Open Canada](https://open.canada.ca/data/api) | 🇨🇦 Canada | Proactive disclosure, contracts >$10K | Public (no key) |
| [SAM.gov](https://sam.gov) | 🇺🇸 United States | Federal contract opportunities | API key required |
| [USASpending](https://api.usaspending.gov) | 🇺🇸 United States | Awarded federal contracts | Public (no key) |

---

## Tech Stack

**Backend**
- Python 3.11+
- Django 4.x
- Django REST Framework
- `requests` for API calls
- `concurrent.futures` for parallel API fetching
- `python-dotenv` for environment variable management
- `django-cors-headers`

**Frontend**
- React 18
- Hooks (`useState`, `useEffect`)
- Fetch API
- Tailwind CSS

---

## Project Structure

```
govcontract-search/
├── backend/
│   ├── .env                        # API keys (never commit this)
│   ├── manage.py
│   ├── core/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── contracts/
│       ├── __init__.py
│       ├── apps.py
│       ├── api_clients.py          # All 4 API integrations
│       ├── normalizers.py          # Data normalization per source
│       ├── relevance.py            # Relevance scoring logic
│       ├── query_expander.py       # Synonym/procurement term expansion
│       ├── views.py                # Search endpoint
│       ├── urls.py
│       └── tests.py
│
└── frontend/
    ├── public/
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── ContractSearch.jsx  # Main search page
        │   ├── ContractCard.jsx    # Individual result card
        │   ├── SearchFilters.jsx   # Source + status filters
        │   └── LoadingSkeleton.jsx # Loading state UI
        └── hooks/
            └── useContractSearch.js # Search logic custom hook
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- pip
- npm or yarn

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourname/govcontract-search.git
cd govcontract-search
```

---

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Create your `.env` file

```bash
touch .env
```

Add the following to `backend/.env`:

```env
# ProcureData (via RapidAPI)
# Sign up at: https://rapidapi.com/nicolasprimeau/api/procuredata-canadian-government-procurement-api
X_RAPIDAPI_KEY=your_rapidapi_key_here
X_RAPIDAPI_HOST=procuredata-canadian-government-procurement-api.p.rapidapi.com

# SAM.gov
# Get your key at: https://sam.gov/profile/details (requires free account)
SAM_GOV=your_sam_gov_api_key_here

# Open Canada and USASpending are public APIs — no keys needed
```

#### Run migrations and start the server

```bash
python manage.py migrate
python manage.py runserver
```

Backend runs at: `http://localhost:8000`

---

### 3. Frontend Setup

```bash
cd ../frontend
npm install
npm start
```

Frontend runs at: `http://localhost:3000`

---

## API Keys

| Key | Where to Get It | Free? |
|---|---|---|
| `X_RAPIDAPI_KEY` | [RapidAPI — ProcureData](https://rapidapi.com/nicolasprimeau/api/procuredata-canadian-government-procurement-api) | ✅ Free tier available |
| `X_RAPIDAPI_HOST` | Same as above — copy from RapidAPI dashboard | ✅ Free |
| `SAM_GOV` | [sam.gov/profile/details](https://sam.gov/profile/details) (login required) | ✅ Free |
| Open Canada | No key needed | ✅ Always free |
| USASpending | No key needed | ✅ Always free |

> ⚠️ SAM.gov API keys rotate every 90 days. You will receive email reminders. Update your `.env` when it expires.

> ⚠️ Without a registered SAM.gov account role, you are limited to 10 requests/day. With a registered account you get 1,000/day.

---

## API Endpoint

### `POST /api/contracts/search/`

**Request body:**
```json
{
  "query": "packaging",
  "page": 1,
  "show_closed": false
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | ✅ Yes | — | Plain-English search term |
| `page` | integer | No | 1 | Page number for pagination |
| `show_closed` | boolean | No | false | Include closed/completed contracts |

**Response:**
```json
{
  "results": [
    {
      "id": "unique-string",
      "title": "Ammunition Packaging Services",
      "description": "Packaging and labeling of 5.56mm ammunition...",
      "value": 250000.00,
      "currency": "USD",
      "awarded_date": "2025-11-01",
      "close_date": "2026-05-15",
      "vendor": "ABC Packaging Corp",
      "department": "Dept of Defense",
      "country": "US",
      "source": "sam_gov",
      "status": "active",
      "is_active": true,
      "relevance_score": 0.92,
      "url": "https://sam.gov/opp/..."
    }
  ],
  "total": 47,
  "page": 1,
  "sources": {
    "procuredata": 12,
    "open_canada": 8,
    "sam_gov": 20,
    "usa_spending": 7
  }
}
```

**Zero results response:**
```json
{
  "results": [],
  "total": 0,
  "message": "No contracts found matching 'packaging'. Try related terms like 'packing services' or 'containerization'.",
  "suggested_terms": ["packing", "containerization", "labeling"]
}
```

---

## How Relevance Scoring Works

Raw API results are scored 0.0–1.0 before being returned:

| Match Condition | Score |
|---|---|
| Exact query term in title | +0.50 |
| Synonym in title | +0.30 |
| Exact query term in description | +0.30 |
| Synonym in description | +0.20 |
| Contract has a dollar value | +0.10 |
| No match in title OR description | 0.00 (excluded) |

Results scoring `0.0` are discarded entirely — they never reach the frontend. This prevents irrelevant results like "Electric Meter Installation" appearing when searching for "packaging".

---

## Active Contract Filtering

By default, only **open and active** contracts are returned. A contract is considered inactive if:

- Its `close_date` or response deadline is in the past
- Its status field is one of: `closed`, `completed`, `cancelled`, `expired`, `awarded`

This is enforced at two levels:
1. **At the API level** — active-only filters are passed in each API request where supported
2. **Post-fetch safety net** — a date-based Python check is applied to all results regardless of source

Users can toggle **"Include Closed Contracts"** in the UI to see historical/completed contracts.

---

## Search Examples

| Search Term | Example Results You Should See |
|---|---|
| `packaging` | Ammunition packaging, medical supply packaging, food labeling |
| `construction` | Base infrastructure, building renovation, road work |
| `IT consulting` | Software development, network services, platform analyst |
| `aircraft` | Tactical aviation support, aerospace maintenance |
| `security` | Cybersecurity services, facility security, guard services |

---

## Environment Variables Reference

```env
# Required
X_RAPIDAPI_KEY=          # ProcureData API key via RapidAPI
X_RAPIDAPI_HOST=         # ProcureData RapidAPI host string
SAM_GOV=                 # SAM.gov personal API key

# Optional (for Django)
DEBUG=True
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Rate Limits

| API | Limit | Notes |
|---|---|---|
| ProcureData | Depends on RapidAPI plan | Free tier has monthly request cap |
| Open Canada | No limit | Public government API |
| SAM.gov | 1,000 req/day (registered user) | 10/day without account role |
| USASpending | No hard limit | Public API |

---

## Known Limitations

- SAM.gov API keys **expire every 90 days** and must be manually renewed in `.env`
- ProcureData free tier has limited monthly requests — upgrade for production use
- USASpending reflects **awarded** contracts only, not open solicitations
- Canadian provincial contracts (BC Bid, Ontario Tenders, SEAO) are not included — federal only

---

## Roadmap

- [ ] Add Canadian provincial procurement portals (BC Bid, Ontario Tenders, SEAO Quebec)
- [ ] Email alerts for new contracts matching saved searches
- [ ] Export results to CSV
- [ ] Contract detail page with full description
- [ ] NAICS/GSIN commodity code filtering
- [ ] Saved searches and user accounts
- [ ] Mobile app

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

MIT License — see `LICENSE` file for details.

---

## Disclaimer

This tool aggregates publicly available government procurement data. All contract information is sourced directly from official government APIs. This project is not affiliated with, endorsed by, or sponsored by the Government of Canada, the US General Services Administration, or any other government body.
