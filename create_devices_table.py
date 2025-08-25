import sqlite3

db_path = r"K:\ccboot_clone\database.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# إنشاء جدول devices لو مش موجود
cursor.execute("""
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    ip TEXT,
    status TEXT
);
""")

conn.commit()
conn.close()
print("تم إنشاء جدول devices بنجاح!")
