import os
from pathlib import Path
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# =========================
# TEMEL AYARLAR
# =========================

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Fabrika Yönetim Sistemi")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL yok!")

db_pool = pool.SimpleConnectionPool(
    1,
    5,
    DATABASE_URL
)

# =========================
# DB HELPER
# =========================

def run_query(query, params=None, fetch=False):
    conn = db_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            result = cur.fetchall() if fetch else None
            conn.commit()
            return result
    finally:
        db_pool.putconn(conn)

# =========================
# STATIC + HTML
# =========================

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("templates/index.html")

@app.get("/stok")
def stok():
    return FileResponse("templates/stok.html")

@app.get("/uretim")
def uretim():
    return FileResponse("templates/uretim.html")

# =========================
# TEST API
# =========================

@app.get("/api/test")
def test():
    return {"status": "ok"}

# =========================
# DB TEST
# =========================

@app.get("/api/db-test")
def db_test():
    result = run_query("SELECT 1 as test", fetch=True)
    return result
