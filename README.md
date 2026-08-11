# University Downloads Analytics

A practice project exploring embedded analytics: querying a real download-events mart, serving it through an API, and visualizing it in a chart with a university picker.

## What's here
- `query.py` — example SQL queries against the mart (filtering, totals, rankings)
- `app.py` — FastAPI backend serving the data as JSON
- `chart.html` — frontend chart (Apache ECharts) with a dropdown to select any university
- `downloads.db` — SQLite database loaded from `mart_downloads_by_university.csv` (not tracked in git — see `.gitignore`)

## Data
Daily download counts per university. 397 universities, Feb–Aug 2026.

## Setup
uv sync
Note: `downloads.db` isn't included in this repo. Rebuild it locally from the source CSV before running anything.

## Run the API
uv run uvicorn app:app --reload

Then open `chart.html` in a browser (API must be running first).

## Endpoints
- `GET /universities` — list of all university codes
- `GET /universities/{code}/downloads` — daily downloads for one university
