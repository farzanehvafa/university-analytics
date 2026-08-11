import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/universities")
def list_universities():
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT DISTINCT university_code FROM downloads_by_university ORDER BY university_code"
    ).fetchall()
    return [r[0] for r in rows]

@app.get("/universities/{code}/downloads")
def get_downloads(code: str):
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT date, downloads FROM downloads_by_university WHERE university_code = ? ORDER BY date",
        (code,)
    ).fetchall()
    return [{"date": r[0], "downloads": r[1]} for r in rows]