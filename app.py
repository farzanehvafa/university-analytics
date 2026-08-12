import sqlite3
import datetime
import jwt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_KEY = "dev-admin-key-change-this-later"
SECRET_KEY = "dev-secret-change-this-later"
ALGORITHM = "HS256"


# Stand-in for a real users table — one row per university, storing a hash, never a real password
UNIVERSITY_CREDENTIALS = {
    "de_pum": '$2b$12$efX1KQc5dAMRx6NNKN35N.FPu8yq9/9rbNBByEu8/nFaG7pUmKj3C',  # paste your actual generated hash here
}

class LoginRequest(BaseModel):
    university_code: str
    password: str

@app.post("/login")
def login(request: LoginRequest):
    stored_hash = UNIVERSITY_CREDENTIALS.get(request.university_code)
    if not stored_hash:
        raise HTTPException(status_code=401, detail="Unknown university")

    if not bcrypt.checkpw(request.password.encode(), stored_hash.encode()):
        raise HTTPException(status_code=401, detail="Wrong password")

    payload = {
        "university_code": request.university_code,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

def get_current_university(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["university_code"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

@app.get("/universities")
def list_universities():
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