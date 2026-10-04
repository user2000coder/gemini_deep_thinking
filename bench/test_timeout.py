"""Timeout checks for gemini_mini.py against a local fake Gemini server: no real API call, no real key.

    python bench/test_timeout.py        # ~45 s: the end-to-end cases wait out the real retry delays (5 s + 10 s)

The fake server and its per-connection behaviours (ok, slow:N, stall, stall_mid) are in fake_gemini.py.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Set before importing gemini_mini, whose load_dotenv() never overrides existing variables: the real key
# from .env is never loaded, and nothing can reach Google because every call goes to the fake server.
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ.pop("GOOGLE_API_KEY", None)

import httpx  # noqa: E402
from google.genai import types  # noqa: E402

PROJECT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT))
import gemini_mini as gm  # noqa: E402
from fake_gemini import ANSWER, FakeGemini  # noqa: E402

results = []


def check(name, cond, detail=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail and not cond else ""))


server = FakeGemini()
os.environ["GOOGLE_GEMINI_BASE_URL"] = server.url
config = types.GenerateContentConfig()


def ask_once(timeout, behaviours):
    """One single-pass question through the real SDK client; returns (history, error, seconds, connections)."""
    server.queue, server.connections = list(behaviours), 0
    history, error, start = [], None, time.monotonic()
    try:
        gm.ask(gm.make_client(timeout), "gemini-test", config, history, "câu hỏi", deepthink=False)
    except httpx.TransportError as e:
        error = e
    return history, error, time.monotonic() - start, server.connections


# --- configuration
os.environ.pop("GEMINI_TIMEOUT", None)
check("GEMINI_TIMEOUT unset -> 180 s", gm.load_timeout() == 180)
os.environ["GEMINI_TIMEOUT"] = "30"
check("GEMINI_TIMEOUT=30 -> 30 s", gm.load_timeout() == 30)
os.environ["GEMINI_TIMEOUT"] = "-1"  # -1 means "dynamic" for the thinking budget; here it used to crash the first call
try:
    gm.load_timeout()
    check("GEMINI_TIMEOUT=-1 rejected as invalid", False, "accepted")
except ValueError:
    check("GEMINI_TIMEOUT=-1 rejected as invalid", True)
os.environ.pop("GEMINI_TIMEOUT")
http_options = getattr(getattr(gm.make_client(2.5), "_api_client", None), "_http_options", None)
check("make_client(2.5) -> HttpOptions.timeout 2500 ms", getattr(http_options, "timeout", None) == 2500)

# --- in process, real SDK + fake server; retry waits skipped so these run fast
real_sleep = time.sleep
gm.time.sleep = lambda s: None

history, error, secs, conns = ask_once(2, ["ok"])
check("ok: answer received and stored", error is None and len(history) == 2 and history[1].parts[0].text == ANSWER,
      f"error={error!r} history={len(history)}")
check("only the dummy key ever reached the server", server.keys == {"test-key"}, f"keys={server.keys}")

history, error, secs, conns = ask_once(3, ["slow:1.5"])
check("slow answer inside the timeout is not cut", error is None and len(history) == 2 and secs >= 1.5,
      f"error={error!r} secs={secs:.1f}")

history, error, secs, conns = ask_once(1, ["stall"] * 3)
check("silent server -> ReadTimeout after 3 attempts, history untouched",
      isinstance(error, httpx.TimeoutException) and history == [] and conns == 3 and secs < 10,
      f"error={error!r} conns={conns} secs={secs:.1f}")

history, error, secs, conns = ask_once(1, ["stall_mid"] * 3)
check("stall mid-stream -> ReadTimeout after 3 attempts, history untouched",
      isinstance(error, httpx.TimeoutException) and history == [] and conns == 3 and secs < 10,
      f"error={error!r} conns={conns} secs={secs:.1f}")

history, error, secs, conns = ask_once(1, ["stall", "ok"])
check("one stall then ok -> retried and answered", error is None and len(history) == 2 and conns == 2,
      f"error={error!r} conns={conns}")

gm.time.sleep = real_sleep

# --- end to end: the real program in a subprocess, real retry waits
env = {**os.environ, "GEMINI_TIMEOUT": "1", "PYTHONIOENCODING": "utf-8"}


def run_chat(args, behaviours, stdin=""):
    server.queue = list(behaviours)
    start = time.monotonic()
    p = subprocess.run([sys.executable, "gemini_mini.py", "--no-deepthink", "--hide-thoughts", *args], cwd=PROJECT,
                       env=env, input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=120)
    return p, time.monotonic() - start


p, secs = run_chat(["xin chào"], ["stall"] * 3)
check("one-shot, server silent: exits with a network error instead of hanging",
      p.returncode == 1 and "Network error: ReadTimeout" in p.stderr
      and p.stdout.count("network error ReadTimeout - retrying") == 2 and secs < 40,
      f"code={p.returncode} secs={secs:.0f} stderr={p.stderr[-200:]!r}")

p, secs = run_chat([], ["stall"] * 3 + ["ok"], stdin="câu 1\ncâu 2\n")
check("chat, first message times out: error reported, chat continues, next message answered",
      p.returncode == 0 and "Network error: ReadTimeout" in p.stdout and "history kept" in p.stdout
      and f"Gemini: {ANSWER}" in p.stdout and secs < 60,
      f"code={p.returncode} secs={secs:.0f} out={p.stdout[-300:]!r}")

env["GEMINI_TIMEOUT"] = "-1"
p, secs = run_chat([], ["ok"], stdin="câu 1\n")
check("GEMINI_TIMEOUT=-1: refused at startup with a message, no traceback",
      p.returncode == 1 and "Invalid GEMINI_TIMEOUT '-1'" in p.stderr and "Traceback" not in p.stderr,
      f"code={p.returncode} stderr={p.stderr[-200:]!r}")

server.close()
print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
