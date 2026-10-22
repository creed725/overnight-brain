"""Tiny client for a local Ollama server. Standard library only."""
import json
import os
import time
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("OB_MODEL", "gemma4:e2b-it-qat")
FAKE = os.environ.get("OB_FAKE") == "1"  # test the app without downloading a model


def generate(prompt, gentle=False, timeout=1800):
    if FAKE:
        time.sleep(1.5)
        first_line = prompt.strip().splitlines()[-1][:80]
        return f"(fake model) A thoughtful overnight answer about: {first_line}"

    options = {"temperature": 0.4}
    if gentle:
        options["num_thread"] = 2  # fewer CPU threads: slower, cooler, quieter
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": options}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")
        raise RuntimeError(f"Ollama returned {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Can't reach Ollama at {OLLAMA_URL}. Is the Ollama app running?") from e
    return data.get("response", "").strip()


def status():
    """Return (reachable, model_ready, installed_models)."""
    if FAKE:
        return True, True, ["fake"]
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as resp:
            names = [m["name"] for m in json.loads(resp.read()).get("models", [])]
    except Exception:
        return False, False, []
    ready = MODEL in names or f"{MODEL}:latest" in names
    return True, ready, names
