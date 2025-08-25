# push_worker.py (معدل: verification + retry + simple logging)
import sqlite3
import shutil
import time
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

DB = Path("devices.db")
IMAGES_DIR = Path("images")
MASTER_IMAGE = IMAGES_DIR / "master_image.img"
LOG_FILE = Path("push_worker.log")

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def get_db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def update_task(task_id, **kwargs):
    conn = get_db_conn()
    cursor = conn.cursor()
    parts = []
    vals = []
    for k, v in kwargs.items():
        parts.append(f"{k}=?")
        vals.append(v)
    vals.append(task_id)
    cursor.execute(f"UPDATE push_tasks SET {', '.join(parts)} WHERE id=?", vals)
    conn.commit()
    conn.close()

def md5_of_file(path, chunk_size=4*1024*1024):
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def do_copy_for_device(task_row, max_retries=2):
    task_id = task_row["id"]
    pc_number = task_row["pc_number"]
    target_dir = IMAGES_DIR / f"device_{pc_number}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"image_{pc_number}.img"
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        try:
            update_task(task_id, status="running", progress=0, started_at=time.strftime("%Y-%m-%d %H:%M:%S"), message=f"started (attempt {attempt})")
            log(f"Task {task_id}: starting copy attempt {attempt} to {target_path}")
            if not MASTER_IMAGE.exists():
                raise FileNotFoundError(f"master image not found: {MASTER_IMAGE}")
            total = MASTER_IMAGE.stat().st_size
            copied = 0
            buf_size = 4 * 1024 * 1024  # 4MB
            with MASTER_IMAGE.open("rb") as src, target_path.open("wb") as dst:
                while True:
                    chunk = src.read(buf_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied += len(chunk)
                    progress = int((copied / total) * 100) if total > 0 else 100
                    if progress > 100: progress = 100
                    update_task(task_id, progress=progress)
            # تحقق: أولاً المقارنة بالحجم ثم MD5
            target_size = target_path.stat().st_size
            if target_size != total:
                raise IOError(f"Size mismatch: master {total} != target {target_size}")
            # MD5 check (اختياري ولكنه يعطي تأكيد قوي)
            master_md5 = md5_of_file(MASTER_IMAGE)
            target_md5 = md5_of_file(target_path)
            if master_md5 != target_md5:
                raise IOError(f"MD5 mismatch: {master_md5} != {target_md5}")
            # نجاح
            update_task(task_id, progress=100, status="success", finished_at=time.strftime("%Y-%m-%d %H:%M:%S"), message=f"copied (attempt {attempt})")
            log(f"Task {task_id}: success on attempt {attempt}")
            return True
        except Exception as e:
            log(f"Task {task_id}: attempt {attempt} failed: {e}")
            update_task(task_id, status="running", message=f"attempt {attempt} failed: {str(e)}")
            # حذف الملف الجزئي قبل المحاولة التالية
            try:
                if target_path.exists():
                    target_path.unlink()
            except Exception:
                pass
            if attempt > max_retries:
                update_task(task_id, status="failed", finished_at=time.strftime("%Y-%m-%d %H:%M:%S"), message=str(e))
                log(f"Task {task_id}: failed after {attempt} attempts")
                return False
            # تأخير بسيط قبل إعادة المحاولة
            time.sleep(2)
    return False

def start_push_tasks(device_list, max_workers=3):
    conn = get_db_conn()
    cursor = conn.cursor()
    created_tasks = []
    for device_id, pc_number in device_list:
        cursor.execute(
            "INSERT INTO push_tasks (device_id, pc_number, status, progress) VALUES (?, ?, ?, ?)",
            (device_id, pc_number, "pending", 0)
        )
        created_tasks.append(cursor.lastrowid)
    conn.commit()
    conn.close()

    conn = get_db_conn()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in created_tasks)
    cursor.execute(f"SELECT * FROM push_tasks WHERE id IN ({placeholders})", created_tasks)
    tasks = cursor.fetchall()
    conn.close()

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(do_copy_for_device, t) for t in tasks]
        for f in futures:
            try:
                f.result()
            except Exception as e:
                log(f"Worker exception: {e}")

    return created_tasks
