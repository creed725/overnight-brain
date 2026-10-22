"""Web app: queue tasks during the day, read the digest in the morning.

    uvicorn app:app --port 8000
"""
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import llm
import store
from prompts import KINDS

HERE = Path(__file__).parent
app = FastAPI(title="Overnight Brain")
_worker = None  # the worker started from the "Run now" button, if any


def worker_running():
    return _worker is not None and _worker.poll() is None


class NewTask(BaseModel):
    kind: str = "ask"
    text: str = Field(min_length=1, max_length=20000)


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/status")
def status():
    reachable, ready, models = llm.status()
    with store.connect() as conn:
        counts = store.counts(conn)
    return {"model": llm.MODEL, "fake": llm.FAKE, "ollama": reachable,
            "model_ready": ready, "installed": models,
            "worker_running": worker_running(), "counts": counts}


@app.get("/api/kinds")
def kinds():
    return {k: {"label": v["label"], "hint": v["hint"]} for k, v in KINDS.items()}


@app.get("/api/tasks")
def tasks():
    with store.connect() as conn:
        return store.list_tasks(conn)


@app.post("/api/tasks", status_code=201)
def add(task: NewTask):
    if task.kind not in KINDS:
        raise HTTPException(400, f"Unknown kind: {task.kind}")
    with store.connect() as conn:
        return store.add_task(conn, task.kind, task.text.strip())


@app.delete("/api/tasks/{task_id}")
def remove(task_id: int):
    with store.connect() as conn:
        if not store.delete_task(conn, task_id):
            raise HTTPException(409, "Only queued tasks can be removed.")
    return {"ok": True}


@app.get("/api/digest")
def digest():
    with store.connect() as conn:
        return store.latest_digest(conn)


@app.post("/api/run")
def run_now():
    """For demos and impatient evenings: start the worker right away."""
    global _worker
    if worker_running():
        return {"started": False, "message": "Already thinking."}
    _worker = subprocess.Popen([sys.executable, str(HERE / "worker.py")], cwd=HERE)
    return {"started": True}
