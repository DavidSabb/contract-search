# GovContract Search

Search Canadian and US government contracts in one place. Built with Django + React.

---

## What It Does

Type a plain-English term like "packaging" or "construction" and get back active, relevant government contract opportunities from 4 official sources at once.

---

## Data Sources

| Source | Country | Key Required |
|---|---|---|
| ProcureData | 🇨🇦 Canada | Yes — RapidAPI |
| Open Canada | 🇨🇦 Canada | No |
| SAM.gov | 🇺🇸 United States | Yes — free account |
| USASpending | 🇺🇸 United States | No |

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## Environment Variables

Create `backend/.env` with the following:

```env
X_RAPIDAPI_KEY=your_key_here
X_RAPIDAPI_HOST=procuredata-canadian-government-procurement-api.p.rapidapi.com
SAM_GOV=your_sam_gov_key_here
```

**Where to get them:**
- ProcureData → https://rapidapi.com/nicolasprimeau/api/procuredata-canadian-government-procurement-api
- SAM.gov → https://sam.gov/profile/details (free account required)

> ⚠️ SAM.gov keys expire every 90 days — update your `.env` when you get the reminder email.

---

## Stack

- **Backend:** Python, Django, Django REST Framework
- **Frontend:** React 18, Tailwind CSS

---

## Notes

- Active contracts only by default — toggle in the UI to include closed ones
- Results are ranked by relevance, not just keyword match
- SAM.gov free tier: 1,000 requests/day with a registered account, 10/day without
