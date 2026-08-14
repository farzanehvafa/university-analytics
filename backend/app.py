import sqlite3
import datetime
import jwt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt
import os
from dotenv import load_dotenv
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Query


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_KEY = os.getenv("ADMIN_KEY")
ALGORITHM = "HS256"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
security = HTTPBasic()

def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return credentials.username

class LoginRequest(BaseModel):
    university_code: str
    password: str

@app.post("/login")
def login(request: LoginRequest):
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    row = cur.execute(
        "SELECT password_hash FROM university_credentials WHERE university_code = ?",
        (request.university_code,)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Unknown university")

    if not bcrypt.checkpw(request.password.encode(), row[0].encode()):
        raise HTTPException(status_code=401, detail="Wrong password")

    payload = {
        "university_code": request.university_code,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

def get_current_university(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        return payload["university_code"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

@app.get("/universities")
def list_universities(username: str = Depends(verify_basic_auth)):
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT DISTINCT university_code FROM downloads_by_university ORDER BY university_code"
    ).fetchall()
    return [r[0] for r in rows]

@app.get("/universities/{code}/downloads")
def get_downloads(code: str, x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT date, downloads FROM downloads_by_university WHERE university_code = ? ORDER BY date",
        (code,)
    ).fetchall()
    return [{"date": r[0], "downloads": r[1]} for r in rows]

@app.get("/my-downloads")
def get_my_downloads(university_code: str = Depends(get_current_university)):
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT date, downloads FROM downloads_by_university WHERE university_code = ? ORDER BY date",
        (university_code,)
    ).fetchall()
    return [{"date": r[0], "downloads": r[1]} for r in rows]

@app.get("/universities/{code}/screen-views")
def get_screen_views(code: str, x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT view_date, screen_views FROM screen_views_by_university WHERE university_code = ? ORDER BY view_date",
        (code,)
    ).fetchall()
    return [{"date": r[0], "screen_views": r[1]} for r in rows]

@app.get("/my-screen-views")
def get_my_screen_views(university_code: str = Depends(get_current_university)):
    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT view_date, screen_views FROM screen_views_by_university WHERE university_code = ? ORDER BY view_date",
        (university_code,)
    ).fetchall()
    return [{"date": r[0], "screen_views": r[1]} for r in rows]

#Semantic Layer
METRIC_TABLES = {
    "downloads": ("downloads_by_university", "downloads", "date"),
    "screen_views": ("screen_views_by_university", "screen_views", "view_date"),
}

GROUP_BY_EXPRESSIONS = {
    "day": lambda col: col,
    "week": lambda col: f"strftime('%Y-W%W', {col})",
    "month": lambda col: f"strftime('%Y-%m', {col})",
}

@app.get("/my-report")
def my_report(
    metric: str = Query(...),
    group_by: str = Query("day"),
    start: str = Query(...),
    end: str = Query(...),
    university_code: str = Depends(get_current_university)
):
    if metric not in METRIC_TABLES:
        raise HTTPException(status_code=400, detail=f"Unknown metric. Choose from: {list(METRIC_TABLES.keys())}")
    if group_by not in GROUP_BY_EXPRESSIONS:
        raise HTTPException(status_code=400, detail=f"Unknown group_by. Choose from: {list(GROUP_BY_EXPRESSIONS.keys())}")

    table, value_col, date_col = METRIC_TABLES[metric]
    group_expr = GROUP_BY_EXPRESSIONS[group_by](date_col)

    conn = sqlite3.connect("downloads.db")
    cur = conn.cursor()
    query = f"""
        SELECT {group_expr} as period, SUM({value_col}) as total
        FROM {table}
        WHERE university_code = ? AND {date_col} BETWEEN ? AND ?
        GROUP BY period
        ORDER BY period
    """
    rows = cur.execute(query, (university_code, start, end)).fetchall()
    return [{"period": r[0], "total": r[1]} for r in rows]
