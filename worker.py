"""The night shift: works through the queue one task at a time, then writes a digest.

    python worker.py                      # run now
    python worker.py --start-at 01:00     # wait until 1 AM, then run
    python worker.py --gentle             # slower, cooler: fewer threads + rests between tasks
"""
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

import llm
import store
from prompts import DIGEST_PROMPT, KINDS

DIGEST_DIR = Path(__file__).parent / "digests"


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def wait_until(hhmm):
    hour, minute = map(int, hhmm.split(":"))
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    log(f"Resting until {target:%a %I:%M %p}. Go to bed.")
    time.sleep((target - now).total_seconds())


def write_digest(conn, task_ids, gentle):
    tasks = [store.get_task(conn, i) for i in task_ids]
    items = "\n\n".join(
        f"- {KINDS[t['kind']]['label']}: {t['text'][:200]}\n  Result: {(t['result'] or '')[:600]}"
        for t in tasks)
    try:
        summary = llm.generate(DIGEST_PROMPT.format(items=items), gentle=gentle)
    except Exception as e:  # the results still matter even if the note fails
        summary = f"Finished {len(tasks)} task(s) overnight. (Couldn't write the summary: {e})"
    store.save_digest(conn, summary, task_ids)

    DIGEST_DIR.mkdir(exist_ok=True)
    path = DIGEST_DIR / f"{datetime.now():%Y-%m-%d}.md"
    lines = [f"# Morning digest, {datetime.now():%A, %B %d}", "", summary, ""]
    for t in tasks:
        lines += [f"## {KINDS[t['kind']]['label']}", "", f"> {t['text']}", "",
                  t["result"] or "", "", f"_{t['seconds']}s of thinking_", ""]
    path.write_text("\n".join(lines))
    log(f"Digest saved to {path}")


def run(gentle=False, pause=None):
    conn = store.connect()
    store.reset_stuck(conn)
    if pause is None:
        pause = 20 if gentle else 0
    done = []

    while (task := store.claim_next(conn)) is not None:
        log(f"Thinking about #{task['id']} ({task['kind']}): {task['text'][:60]}")
        started = time.time()
        try:
            kind = KINDS.get(task["kind"], KINDS["ask"])
            result = llm.generate(kind["template"].format(text=task["text"]), gentle=gentle)
            store.finish_task(conn, task["id"], result, time.time() - started)
            done.append(task["id"])
            log(f"  done in {time.time() - started:.0f}s")
        except Exception as e:
            store.fail_task(conn, task["id"], str(e), time.time() - started)
            log(f"  couldn't finish: {e}")
        if pause:
            time.sleep(pause)

    if done:
        write_digest(conn, done, gentle)
    else:
        log("Nothing new in the queue.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Overnight Brain worker")
    p.add_argument("--start-at", metavar="HH:MM", help="wait until this time (24-hour) to start")
    p.add_argument("--gentle", action="store_true", help="fewer threads and rests between tasks")
    p.add_argument("--pause", type=int, help="seconds to rest between tasks")
    args = p.parse_args()
    if args.start_at:
        wait_until(args.start_at)
    run(gentle=args.gentle, pause=args.pause)
