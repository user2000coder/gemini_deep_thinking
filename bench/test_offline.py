"""Offline checks for gemini_mini.py (no Gemini calls): deepthink fallback, network retries, chat loop survival.

    python bench/test_offline.py
"""

import builtins
import os
import sys
from pathlib import Path

# main() refuses to start without a key (check 8). A dummy one, set before gemini_mini loads .env (which never
# overrides existing variables): the real key is never read, and no check here reaches the network.
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ.pop("GOOGLE_API_KEY", None)

import httpx  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))
import gemini_mini as gm  # noqa: E402

results = []


def check(name, cond):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name)


def fake_passes(outputs):
    calls = []

    def stream_pass(client, model, config, contents, final):
        calls.append(contents)
        return outputs[len(calls) - 1], None
    return stream_pass, calls


# 1. review empty -> draft used and stored
gm.stream_pass, calls = fake_passes(["bản nháp tốt", ""])
history = []
gm.ask(None, "m", None, history, "câu hỏi", deepthink=True)
check("two passes ran", len(calls) == 2)
check("history keeps question + draft", len(history) == 2 and history[1].parts[0].text == "bản nháp tốt")

# 2. review non-empty -> review answer stored, not the draft
gm.stream_pass, calls = fake_passes(["nháp", "cuối cùng"])
history = []
gm.ask(None, "m", None, history, "q", deepthink=True)
check("final answer stored", history[1].parts[0].text == "cuối cùng")

# 3. both empty -> nothing stored
gm.stream_pass, calls = fake_passes(["", ""])
history = []
gm.ask(None, "m", None, history, "q", deepthink=True)
check("both empty -> history untouched", history == [])

# 4. no deepthink, empty -> nothing stored
gm.stream_pass, calls = fake_passes([""])
history = []
gm.ask(None, "m", None, history, "q", deepthink=False)
check("single pass empty -> history untouched", history == [] and len(calls) == 1)

# 5. review prompt formats (no stray braces) and names sections instead of numbering them
text = gm.REVIEW_PROMPT.format(question="Q", draft="D")
check("REVIEW_PROMPT formats and names sections", "REASONING PROTOCOL" in text and "RUNTIME CONSTRAINTS" in text)

# 6-7. network drops are retried, then re-raised
gm.time.sleep = lambda s: None
n = {"calls": 0}


def flaky():
    n["calls"] += 1
    if n["calls"] < 3:
        raise httpx.ConnectError("SSL EOF")
    return "ok"


check("ConnectError retried until success", gm.with_retry(flaky) == "ok" and n["calls"] == 3)
try:
    gm.with_retry(lambda: (_ for _ in ()).throw(httpx.ReadError("drop")))
    check("persistent ReadError re-raised", False)
except httpx.ReadError:
    check("persistent ReadError re-raised", True)

# 8. interactive loop survives a network error and moves on (main() with fake input and ask)
seen = []
inputs = iter(["q1", "q2"])


def fake_input(prompt=""):
    try:
        return next(inputs)
    except StopIteration:
        raise EOFError


def fake_ask(client, model, config, history, question, deepthink):
    seen.append(question)
    if question == "q2":
        raise httpx.ConnectError("SSL EOF")


builtins.input, gm.ask = fake_input, fake_ask
sys.argv = ["gemini_mini.py", "--no-deepthink"]
try:
    gm.main()
    check("main loop survives network error and continues", seen == ["q1", "q2"])
except httpx.TransportError:
    check("main loop survives network error and continues", False)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
