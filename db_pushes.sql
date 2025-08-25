-- db_pushes.sql
CREATE TABLE IF NOT EXISTS push_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id INTEGER,
  pc_number INTEGER,
  started_at TEXT,
  finished_at TEXT,
  status TEXT,      -- pending, running, success, failed
  progress INTEGER, -- 0..100
  message TEXT
);
