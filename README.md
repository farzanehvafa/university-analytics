# University Downloads Analytics

A practice project exploring embedded analytics: querying a real download-events mart, serving it through a FastAPI backend, and visualizing it in the browser — with a per-university self-service login on top of an admin view.

## Project structure

```
university-analytics/
├── backend/
│   ├── app.py                # FastAPI app: auth + API endpoints
│   ├── query.py               # ad hoc SQL queries against the mart
│   ├── combine_data.py         # one-off script: pulls a mart table in from an external dbt db
│   ├── add_university.py       # CLI: set/reset a university's login password
│   ├── generate_hash.py        # CLI: bcrypt-hash a password
│   ├── downloads.db            # SQLite db (gitignored, not included — see Setup)
│   ├── .env                    # secrets (gitignored — see Environment variables)
│   ├── pyproject.toml / uv.lock
│   └── .venv/                  # created by `uv sync`
└── frontend/
    ├── dashboard.html           # university self-service login + charts + report builder
    └── chart.html                # admin-only chart viewer with a university picker
```

## Data

Daily download counts and screen-view counts per university, loaded from a dbt mart. 397 universities, Feb–Aug 2026. Two tables in `downloads.db`:

- `downloads_by_university` (`university_code`, `date`, `downloads`)
- `screen_views_by_university` (`university_code`, `view_date`, `screen_views`)
- `university_credentials` (`university_code`, `password_hash`) — bcrypt hashes, populated via `add_university.py`

## Setup

```
cd backend
uv sync
```

`downloads.db` isn't included in this repo (see `.gitignore`). Rebuild it locally from the source mart CSVs, or copy an existing table over with `combine_data.py`, before running anything.

### Environment variables

Create `backend/.env` with:

| Variable | Used for |
|---|---|
| `SECRET_KEY` | Signs/verifies the JWTs issued by `/login` |
| `ADMIN_KEY` | Static key required in the `X-Admin-Key` header on admin-only data endpoints |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | HTTP Basic credentials for `GET /universities` |

### Adding a university login

```
cd backend
uv run python add_university.py <university_code> <password>
```

This bcrypt-hashes the password and upserts it into `university_credentials`. `generate_hash.py` is a standalone helper if you just want to see a hash without touching the db.

## Running it

```
cd backend
uv run uvicorn app:app --reload
```

Then open `frontend/dashboard.html` in a browser for the university login flow, or `frontend/chart.html` for the admin viewer. Both are static files with no build step — they call the API directly at `http://127.0.0.1:8000`, so the server must already be running.

## Auth model

The API mixes three auth mechanisms depending on the endpoint:

1. **HTTP Basic** (`ADMIN_USERNAME`/`ADMIN_PASSWORD`) — gates the raw university list.
2. **Static admin key** (`X-Admin-Key` header, checked against `ADMIN_KEY`) — gates per-university data lookups by code, used by `chart.html`.
3. **JWT bearer token** — a university logs in with its code + password (`POST /login`), gets a 1-hour token back, and uses it as `Authorization: Bearer <token>` to see only its own data. Used by `dashboard.html`.

## Endpoints

| Method & path | Auth | Description |
|---|---|---|
| `POST /login` | — | University code + password → JWT access token (1h expiry) |
| `GET /universities` | Basic | List all university codes |
| `GET /universities/{code}/downloads` | `X-Admin-Key` | Daily downloads for one university |
| `GET /universities/{code}/screen-views` | `X-Admin-Key` | Daily screen views for one university |
| `GET /my-downloads` | Bearer | Daily downloads for the logged-in university |
| `GET /my-screen-views` | Bearer | Daily screen views for the logged-in university |
| `GET /my-report?metric=&group_by=&start=&end=` | Bearer | Custom report: `metric` is `downloads` or `screen_views`, `group_by` is `day`/`week`/`month`, `start`/`end` are `YYYY-MM-DD` |

## Known limitations

This is a learning project, not production-hardened:

- `chart.html` has the admin Basic-auth password and `X-Admin-Key` hardcoded in client-side JS — fine for local dev, but don't deploy it as-is.
- CORS is wide open (`allow_origins=["*"]`).
- The JWT is stored in `localStorage` in `dashboard.html`, which is convenient for surviving page refreshes but readable by any JS on the page (no XSS protection beyond what the browser gives you by default).
