# Overnight Brain 🌙

**Hand it off tonight. Read it with your coffee.**

Overnight Brain is a lazy person's AI assistant. During the day you drop questions, long articles, big goals, and messages you keep putting off into a queue. At night, a small open-weight model running on your own laptop works through them one at a time, slowly, while you sleep. In the morning you get a digest.

Built for the Hacktoberfest 2026 Open-Source AI Challenge, Week 3: **Slow and Steady**.

## Why slow on purpose

Most AI tools race to answer in seconds, which means a giant model in someone else's data center. Overnight Brain flips that. If the answer can wait until morning, a small open-weight model like Gemma on an ordinary laptop is plenty. It can take its time, run with fewer threads, rest between tasks, and nobody has to watch a spinner.

## Why open matters here

- **Private by default.** Nothing you type leaves your computer. That makes it safe for the half-formed thoughts, personal notes, and work drafts you wouldn't paste into a website.
- **Free to run.** No API keys, no per-token bill, no subscription. Your laptop is already on the desk at night.
- **Yours to change.** Swap the model, edit the prompts in `prompts.py`, add new task types. Open weights and open code mean nothing is a black box.

## What it does

| Task type | Good for |
|---|---|
| Answer a question | Something you've been meaning to look into |
| Summarize this | Articles, notes, long emails |
| Break it into steps | A goal that feels too big to start |
| Draft a message | The email or text you keep putting off |

## Setup (Mac)

1. **Install Ollama** from [ollama.com/download](https://ollama.com/download) (or `brew install ollama`), then open the Ollama app.
2. **Download Gemma 4 E4B**, a small open-weight model from Google:
   ```bash
   ollama pull gemma4:e4b
   ```
3. **Install the app:**
   ```bash
   cd overnight-brain
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Start it:**
   ```bash
   uvicorn app:app --port 8000
   ```
   Open http://localhost:8000.

Want to try the app before the model finishes downloading? Start it in test mode:
```bash
OB_FAKE=1 uvicorn app:app --port 8000
```

## Running it overnight

Add a few tasks, then in a second terminal:

```bash
caffeinate -i python worker.py --start-at 01:00 --gentle
```

- `--start-at 01:00` waits until 1 AM (24-hour time) before starting.
- `--gentle` uses fewer CPU threads and rests 20 seconds between tasks, so the laptop stays cool and quiet.
- `caffeinate -i` is built into macOS and keeps the Mac from sleeping while the worker runs. Keep the laptop plugged in.

In a hurry? Click **Start thinking now** in the app.

Each morning's digest also lands in `digests/YYYY-MM-DD.md`.

## Settings

| Variable | Default | What it does |
|---|---|---|
| `OB_MODEL` | `gemma4:e4b` | Any model you've pulled with Ollama |
| `OLLAMA_URL` | `http://localhost:11434` | Where Ollama is running |
| `OB_FAKE` | off | `1` returns canned answers for testing |

## How it works

```
browser ──► FastAPI (app.py) ──► SQLite queue (data/overnight.db)
                                        │
           worker.py (night shift) ◄────┘
               │  one task at a time
               ▼
           Ollama + open-weight model (local)
               │
               ▼
           morning digest (database + digests/*.md)
```

## License

MIT
