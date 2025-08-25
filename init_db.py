import sqlite3

conn = sqlite3.connect("devices.db")
c = conn.cursor()

# إنشاء جدول الأجهزة
c.execute("""
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pc_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    mac TEXT NOT NULL,
    status TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("تم إنشاء قاعدة البيانات بنجاح ✅")
