# seed_devices.py
import sqlite3
from pathlib import Path

DB = "devices.db"

devices = [
    (1, "Test-PC-1", "AA:BB:CC:00:00:01", "192.168.1.101"),
    (2, "Test-PC-2", "AA:BB:CC:00:00:02", "192.168.1.102"),
    (3, "Test-PC-3", "AA:BB:CC:00:00:03", "192.168.1.103"),
]

conn = sqlite3.connect(DB)
c = conn.cursor()
for pc_number, name, mac, ip in devices:
    c.execute("INSERT INTO devices (pc_number, name, mac, ip, status) VALUES (?, ?, ?, ?, ?)",
              (pc_number, name, mac, ip, "offline"))
conn.commit()
conn.close()
print("Seeded devices.")
