import sqlite3
from fastapi import FastAPI

app = FastAPI()

@app.get("/universities/{code}/downloads")
def get_downloads(code: str):
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT date, downloads FROM downloads_by_university WHERE university_code = ? ORDER BY date",
        (code,)
    ).fetchall()
    return [{"date": r[0], "downloads": r[1]} for r in rows]