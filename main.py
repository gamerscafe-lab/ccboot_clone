from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB_FILE = "devices.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# تحديث كل الحالات (مثال وهمي)
def update_all_statuses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ip FROM devices")
    devices = cursor.fetchall()
    for device in devices:
        # تحديث الحالة بشكل وهمي للعرض
        cursor.execute("UPDATE devices SET status='online' WHERE id=?", (device["id"],))
    conn.commit()
    conn.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    update_all_statuses()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices")
    devices = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("devices.html", {"request": request, "devices": devices})

@app.get("/devices", response_class=HTMLResponse)
def list_devices(request: Request):
    update_all_statuses()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices")
    devices = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("devices.html", {"request": request, "devices": devices})

@app.get("/edit/{device_id}", response_class=HTMLResponse)
def edit_device(request: Request, device_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE id=?", (device_id,))
    device = cursor.fetchone()
    conn.close()
    return templates.TemplateResponse("edit.html", {"request": request, "device": device})

@app.post("/update/{device_id}")
def update_device(device_id: int, pc_number: int = Form(...), name: str = Form(...), ip: str = Form(...), status: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE devices SET pc_number=?, name=?, ip=?, status=? WHERE id=?",
                   (pc_number, name, ip, status, device_id))
    conn.commit()
    conn.close()
    return {"result": "تم تحديث الجهاز بنجاح"}

# التحكم في الجهاز
@app.get("/api/{action}")
def device_control(action: str, mac: str):
    # هنا تقدر تحط التحكم الحقيقي بالجهاز (تشغيل، ايقاف، ريستارت)
    return JSONResponse({"result": f"تم {action} للجهاز {mac}"})
