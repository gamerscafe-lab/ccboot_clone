# add_ip_column.py
import sqlite3
import os
DB = r"K:\ccboot_clone\devices.db"  # غيّر إذا اسم القاعدة مختلف

if not os.path.exists(DB):
    print("ملف قاعدة البيانات غير موجود:", DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices';")
if not cursor.fetchone():
    print("لا يوجد جدول devices في القاعدة. الرجاء إنشاء الجدول أولاً أو استعمال db_modified.sql")
    conn.close()
    raise SystemExit(1)

cursor.execute("PRAGMA table_info(devices);")
cols = [r[1] for r in cursor.fetchall()]
if "ip" in cols:
    print("العمود 'ip' موجود بالفعل.")
else:
    cursor.execute("ALTER TABLE devices ADD COLUMN ip TEXT;")
    print("تم إضافة العمود 'ip' بنجاح.")
conn.commit()
conn.close()
