# app.py (معدّل لتحسين الأداء ودقة الحالة)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import subprocess
import concurrent.futures
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
DB_PATH = "devices.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_and_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_number INTEGER,
        name TEXT,
        mac TEXT,
        ip TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db_and_schema()

# ----- دوال الـ ping -----
def ping_once(host, timeout_ms=1000):
    """
    Ping واحد سريع. يرجّع True لو reachable، False لو لا.
    يعمل على Windows: يستخدم '-n 1' و '-w timeout_ms'
    """
    if not host:
        return False
    try:
        # استخدام subprocess مع timeout أيضاً كحماية إضافية
        # نمرّر timeout بالثواني إلى subprocess.run
        timeout_sec = max(1, timeout_ms // 1000)
        # أمر ping لويندوز
        completed = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms), host],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout_sec + 1)
        return completed.returncode == 0
    except Exception:
        return False

def ping_device_tuple(device_row):
    """
    device_row: sqlite Row أو tuple يحتوي id, mac, ip
    نستخدم ip أولاً ثم mac كـ fallback.
    نرجع dict {id, status}
    """
    device_id = device_row["id"]
    ip = (device_row["ip"] or "").strip()
    mac = (device_row["mac"] or "").strip()
    host = ip if ip else mac  # الأفضل أن ip يكون موجود
    reachable = ping_once(host, timeout_ms=1000) if host else False
    return {"id": device_id, "status": "online" if reachable else "offline"}

# ----- Endpoints -----
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/devices")

@app.get("/devices", response_class=HTMLResponse)
def list_devices(request: Request):
    """
    لا ننفّذ ping هنا حتى لا نبطئ تحميل الصفحة.
    الصفحة ستحمّل بسرعة ثم الـ JS سيستدعي /api/statuses لتحديث الحالة.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, pc_number, name, mac, ip, status FROM devices ORDER BY pc_number ASC")
    rows = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("devices.html", {"request": request, "devices": rows})

@app.get("/api/statuses")
def api_statuses():
    """
    نعيد حالة كل جهاز بسرعة — نقوم بـ ping متوازي بحد أقصى 20 thread.
    لا نكتب في قاعدة البيانات هنا (قراءة فقط) لتسريع الاستجابة.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, mac, ip FROM devices")
    devices = cursor.fetchall()
    conn.close()

    results = []
    # نعمل ping متوازي للحصول على استجابة أسرع
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(ping_device_tuple, d) for d in devices]
        for f in concurrent.futures.as_completed(futures):
            try:
                results.append(f.result())
            except Exception:
                pass

    return JSONResponse(results)

@app.get("/api/wol")
def api_wol(mac: str):
    # إرسال WOL: استخدم مكتبة wakeonlan أو send_magic_packet مباشرة
    try:
        from wakeonlan import send_magic_packet
        send_magic_packet(mac)
        return {"status": "sent"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# حذف endpoints الإيقاف/ريستارت من هنا (بناءً على طلبك)
# لو في حاجة تريد استعادتها نضيفها لاحقًا.

