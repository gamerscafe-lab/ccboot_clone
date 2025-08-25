# run_sql.py
# ---------
# يقرأ ملف db_pushes.sql وينفّذه على قاعدة devices.db
# يقوم بعمل backup لملف devices.db إن كان موجوداً، ثم ينفّذ SQL ويطبع نتيجة الجدول push_tasks.
#
# حفظ: K:\ccboot_clone\run_sql.py
# تشغيل: فتح CMD ثم -> cd /d K:\ccboot_clone  -> python run_sql.py

import sqlite3
from pathlib import Path
import shutil
import time
import sys

PROJECT_DIR = Path.cwd()  # يفضل تشغيل الملف من داخل K:\ccboot_clone
SQL_FILE = PROJECT_DIR / "db_pushes.sql"
DB_FILE = PROJECT_DIR / "devices.db"

def backup_db(db_path: Path) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.bak_{ts}")
    shutil.copy2(db_path, backup_path)
    return backup_path

def execute_sql(sql_text: str, db_path: Path):
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(sql_text)
        conn.commit()
    finally:
        conn.close()

def print_table_info(db_path: Path, table_name: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name});")
        cols = cursor.fetchall()
        if not cols:
            print(f"لم يتم العثور على جدول '{table_name}' في القاعدة.")
            return
        print(f"\nأعمدة جدول '{table_name}':")
        for c in cols:
            # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
            print(f" - {c[1]} ({c[2]}) notnull={c[3]} pk={c[5]}")
        # عدد السجلات إن وُجد جدول
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        cnt = cursor.fetchone()[0]
        print(f"عدد السجلات في '{table_name}': {cnt}")
    except sqlite3.Error as e:
        print(f"خطأ عند قراءة معلومات الجدول: {e}")
    finally:
        conn.close()

def main():
    print("Working directory:", PROJECT_DIR)
    if not SQL_FILE.exists():
        print(f"الملف {SQL_FILE.name} غير موجود في المجلد. ضع db_pushes.sql في نفس المجلد ثم أعد المحاولة.")
        sys.exit(1)

    # نسخ احتياطي إن وجد DB
    if DB_FILE.exists():
        try:
            backup_path = backup_db(DB_FILE)
            print(f"تم أخذ نسخة احتياطية من '{DB_FILE.name}' باسم: {backup_path.name}")
        except Exception as e:
            print(f"فشل في أخذ النسخة الاحتياطية: {e}")
            sys.exit(1)
    else:
        print(f"لم يتم العثور على '{DB_FILE.name}'. سيتم إنشاء قاعدة جديدة عند تنفيذ SQL.")

    # قراءة SQL
    try:
        sql_text = SQL_FILE.read_text(encoding="utf-8")
    except Exception as e:
        print(f"خطأ في قراءة {SQL_FILE.name}: {e}")
        sys.exit(1)

    # تنفيذ SQL
    try:
        execute_sql(sql_text, DB_FILE)
        print("تم تنفيذ محتوى db_pushes.sql بنجاح.")
    except Exception as e:
        print(f"خطأ أثناء تنفيذ SQL: {e}")
        sys.exit(1)

    # عرض معلومات الجدول
    print_table_info(DB_FILE, "push_tasks")
    print("\nانتهى التنفيذ بنجاح.")

if __name__ == "__main__":
    main()
