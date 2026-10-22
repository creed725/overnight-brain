"""SQLite storage for the task queue and morning digests."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.environ.get("OB_DB", Path(__file__).parent / "data" / "overnight.db"))


def now():
    return datetime.now().isoformat(timespec="seconds")


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        text TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        result TEXT,
        error TEXT,
        created_at TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT,
        seconds REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS digests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        summary TEXT,
        task_ids TEXT NOT NULL)""")
    conn.commit()
    return conn


def add_task(conn, kind, text):
    with conn:
        cur = conn.execute(
            "INSERT INTO tasks(kind, text, created_at) VALUES (?, ?, ?)", (kind, text, now()))
    return get_task(conn, cur.lastrowid)


def get_task(conn, task_id):
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks(conn, limit=50):
    rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def delete_task(conn, task_id):
    """Only queued tasks can be removed (the worker may be mid-thought on others)."""
    with conn:
        cur = conn.execute("DELETE FROM tasks WHERE id=? AND status='queued'", (task_id,))
    return cur.rowcount > 0


def counts(conn):
    rows = conn.execute("SELECT status, COUNT(*) n FROM tasks GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


def reset_stuck(conn):
    """If a previous run was interrupted, put half-done tasks back in line."""
    with conn:
        conn.execute("UPDATE tasks SET status='queued', started_at=NULL WHERE status='working'")


def claim_next(conn):
    with conn:
        row = conn.execute(
            "SELECT id FROM tasks WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        if not row:
            return None
        cur = conn.execute(
            "UPDATE tasks SET status='working', started_at=? WHERE id=? AND status='queued'",
            (now(), row["id"]))
    if cur.rowcount == 0:
        return claim_next(conn)
    return get_task(conn, row["id"])


def finish_task(conn, task_id, result, seconds):
    with conn:
        conn.execute(
            "UPDATE tasks SET status='done', result=?, finished_at=?, seconds=? WHERE id=?",
            (result, now(), round(seconds, 1), task_id))


def fail_task(conn, task_id, error, seconds):
    with conn:
        conn.execute(
            "UPDATE tasks SET status='error', error=?, finished_at=?, seconds=? WHERE id=?",
            (error, now(), round(seconds, 1), task_id))


def save_digest(conn, summary, task_ids):
    with conn:
        cur = conn.execute(
            "INSERT INTO digests(created_at, summary, task_ids) VALUES (?, ?, ?)",
            (now(), summary, ",".join(str(i) for i in task_ids)))
    return cur.lastrowid


def latest_digest(conn):
    row = conn.execute("SELECT * FROM digests ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    digest = dict(row)
    ids = [int(i) for i in digest["task_ids"].split(",") if i]
    digest["tasks"] = [t for t in (get_task(conn, i) for i in ids) if t]
    return digest
