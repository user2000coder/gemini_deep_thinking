"""Offline checks for the benchmark harness (bench/run.py, bench/grade.py): no Gemini calls, no real key.

    python bench/test_harness.py        # ~35 s: the end-to-end cases wait out real retry delays

Every check here started as a reproduction of a harness defect (see bench/results/INDEX.md, "Lỗi harness"):
    grade      one answer per turn: a turn that failed or was retried mid-stream must not shift or pollute answers
    run.py     runs outside Windows, reruns a case only on real error lines, writes summary.json after every run,
               resumes an interrupted repeat without overwriting it, refuses a missing instruction file,
               records retries / draft fallbacks / the effective configuration of every run
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Same isolation as test_timeout.py: set before anything loads .env, so the real key is never read and every
# Gemini call goes to the local fake server.
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ.pop("GOOGLE_API_KEY", None)

BENCH = Path(__file__).parent
PROJECT = BENCH.parent
sys.path.insert(0, str(BENCH))
import grade  # noqa: E402
import run  # noqa: E402
from fake_gemini import ANSWER, FakeGemini  # noqa: E402

RESULTS = BENCH / "results"
OLD_FINALS = re.compile(r"Gemini:(.*?)\ntokens:", flags=re.S)  # grade.finals() before the fix: equivalence check
results = []


def check(name, cond, detail=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail and not cond else ""))


def finals_of(path):
    try:
        return grade.finals(path)
    except Exception as e:  # noqa: BLE001 - a crash is a failed check, not a crashed test run
        return e


# ---------------------------------------------------------------- grade: answers aligned with turns
# Real run from the V27.4 comparison: turn 3's review came back empty and the old program stored nothing.
# The old parser returned 2 answers, so `blind` (last answer) would have graded turn 2 as if it were turn 3.
answers = finals_of(RESULTS / "2026-10-04_rep_v274" / "T09_r2.txt")
check("unanswered last turn stays in its slot (rep_v274/T09_r2: 3 turns, turn 3 None)",
      isinstance(answers, list) and len(answers) == 3 and answers[2] is None and all(answers[:2]), repr(answers)[:200])

# Every transcript recorded so far: the fixed parser must return exactly what the old one did for every answered
# turn, so no past verdict changes. Only the alignment (None for unanswered turns) is new.
files = sorted(RESULTS.rglob("T*.txt"))
diffs, misaligned = [], []
for f in files:
    new = finals_of(f)
    if not isinstance(new, list):
        diffs.append(f"{f.parent.name}/{f.name}: {new!r}")
        continue
    old = [m.strip() for m in OLD_FINALS.findall(f.read_text(encoding="utf-8"))]
    if [a for a in new if a is not None] != old:
        diffs.append(f"{f.parent.name}/{f.name}")
    if len(new) != len(grade.case_turns(f.stem)):
        misaligned.append(f"{f.parent.name}/{f.name}")
check(f"all {len(files)} recorded transcripts: answered turns identical to the old parser", not diffs, str(diffs[:5]))
check(f"all {len(files)} recorded transcripts: one slot per turn of the case", not misaligned, str(misaligned[:5]))

# An answer that itself contains a dialogue line "You: ..." is not the start of a new turn.
text = ("banner\n\nYou: \nGemini: Ví dụ hội thoại:\nYou: xin chào\nBot: chào bạn\n"
        "tokens: prompt 1 | thinking 0 | answer 1\n\nYou: \nGemini: lượt hai\ntokens: prompt 1 | thinking 0 | answer 1\n"
        "\nYou: \n")
answers = grade.final_answers(text, 2)
check("answer line starting with 'You: ' does not split the turn",
      answers == ["Ví dụ hội thoại:\nYou: xin chào\nBot: chào bạn", "lượt hai"], repr(answers))

# ---------------------------------------------------------------- gemini_mini + fake server: real transcripts
server = FakeGemini()
os.environ["GOOGLE_GEMINI_BASE_URL"] = server.url
CHAT_ENV = {**os.environ, "GEMINI_TIMEOUT": "1", "GEMINI_MODEL": "gemini-test", "GEMINI_THINKING_BUDGET": "0",
            "GEMINI_INSTRUCTION": "instruction_v28.md", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


def chat(turns, behaviours, *args):
    """The real chat program, piped exactly like run.py does; returns its stdout."""
    server.queue = list(behaviours)
    p = subprocess.run([sys.executable, "gemini_mini.py", "--hide-thoughts", "--no-deepthink", *args], cwd=PROJECT,
                       env=CHAT_ENV, input="\n".join(turns) + "\n", capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    return p.stdout


# The answer stream stalls after its first chunk, the retry succeeds: the turn shows "Gemini:" twice.
text = chat(["câu 1"], ["stall_mid", "ok"])
answers = grade.final_answers(text, 1)
check("mid-stream retry: the transcript really has two 'Gemini:' headers for one turn", text.count("Gemini:") == 2,
      repr(text[-300:]))
check("mid-stream retry: graded answer is the retried answer only", answers == [ANSWER], repr(answers))
check("mid-stream retry: run.py counts 1 answered turn", run.count_answered(text, 1) == 1)

# The last turn fails for good (3 silent attempts): the chat reports it and goes on to EOF.
text = chat(["câu 1", "câu 2", "câu 3"], ["ok", "ok", "stall", "stall", "stall"])
answers = grade.final_answers(text, 3)
check("failed last turn: answers [A, A, None], not turn 2 graded as turn 3", answers == [ANSWER, ANSWER, None],
      repr(answers))

# ---------------------------------------------------------------- run.py, in process (run_case replaced)
check("run.py finds a Python interpreter on this OS", Path(run.python_exe()).is_file(), str(run.python_exe()))

BANNER = "gemini-test  thinking budget: 0  deepthink: on  timeout: 180s  instruction: instruction_v28.md\n"


def fake_transcript(n_turns, extra=""):
    turn = ("\n[draft] nháp\n--- reviewing draft ---\n\nGemini: đáp\n"
            "tokens: prompt 1 | thinking 0 | answer 1  (2 passes)\n")
    return BANNER + "".join("\nYou: " + turn for _ in range(n_turns)) + extra + "\nYou: \n"


def run_main(argv, outputs):
    """run.main() with run_case answering from `outputs` (str, or an exception to raise); returns (calls, exit)."""
    calls = []

    def run_case(turns, instruction, chat_args):
        calls.append(turns)
        out = outputs[min(len(calls), len(outputs)) - 1]
        if isinstance(out, BaseException):
            raise out
        return out, 1.0

    saved = run.run_case, run.time.sleep, sys.argv
    run.run_case, run.time.sleep, sys.argv = run_case, (lambda s: None), ["run.py", *argv]
    code = None
    try:
        run.main()
    except SystemExit as e:
        code = e.code
    except KeyboardInterrupt:
        code = "interrupted"
    finally:
        run.run_case, run.time.sleep, sys.argv = saved
    return calls, code


tmp = Path(tempfile.mkdtemp(prefix="bench_test_"))
try:
    # An answer that merely talks about "Network error" / "API error 500" is not an error line: no rerun.
    talk = fake_transcript(1).replace("Gemini: đáp",
                                      "Gemini: Log ghi 'Network error' và 'API error 500' khi tải cao")
    calls, _ = run_main(["--out", str(tmp / "a"), "T08"], [talk])
    check("answer mentioning 'Network error' / 'API error 500' mid-line: case not rerun", len(calls) == 1,
          f"calls={len(calls)}")
    calls, _ = run_main(["--out", str(tmp / "b"), "T08"], [fake_transcript(0, "\nNetwork error: ReadTimeout: x\n")])
    check("chat's own 'Network error:' line: case rerun 3 times (unchanged)", len(calls) == 3, f"calls={len(calls)}")
    calls, _ = run_main(["--out", str(tmp / "b2"), "T08"], [fake_transcript(0, "\n[stderr]\nAPI error 429: quota\n")])
    check("one-shot 'API error 429' on stderr: case rerun 3 times (unchanged)", len(calls) == 3, f"calls={len(calls)}")

    # Interrupted after the first of three runs: what ran so far is on disk, summary included.
    calls, code = run_main(["--out", str(tmp / "c"), "--repeat", "3", "T01"], [fake_transcript(1), KeyboardInterrupt()])
    summary = tmp / "c" / "summary.json"
    runs = json.loads(summary.read_text(encoding="utf-8"))["runs"] if summary.is_file() else []
    check("interrupted repeat: summary.json already holds the finished run", [r["id"] for r in runs] == ["T01_r1"],
          f"code={code} runs={runs}")

    # Resuming it: numbering continues, earlier transcripts and summary entries are kept.
    calls, code = run_main(["--out", str(tmp / "c"), "--start", "2", "--repeat", "2", "T01"], [fake_transcript(1)])
    runs = json.loads(summary.read_text(encoding="utf-8"))["runs"] if summary.is_file() else []
    check("--start 2 --repeat 2 resumes as r2, r3 and keeps r1 in summary.json",
          [r["id"] for r in runs] == ["T01_r1", "T01_r2", "T01_r3"] and len(calls) == 2,
          f"code={code} runs={[r.get('id') for r in runs]}")

    # Re-running into the same folder must not overwrite a recorded transcript.
    before = (tmp / "c" / "T01_r1.txt").read_text(encoding="utf-8") if (tmp / "c" / "T01_r1.txt").is_file() else None
    calls, code = run_main(["--out", str(tmp / "c"), "--repeat", "3", "T01"], [fake_transcript(1)])
    after = (tmp / "c" / "T01_r1.txt").read_text(encoding="utf-8") if (tmp / "c" / "T01_r1.txt").is_file() else None
    check("existing transcripts are never overwritten (refuses before running anything)",
          before is not None and before == after and calls == [] and code not in (None, 0), f"code={code}")

    calls, code = run_main(["--out", str(tmp / "d"), "--instruction", "no_such_instruction.md", "T01"],
                           [fake_transcript(1)])
    check("missing instruction file: refused before any run", calls == [] and code not in (None, 0), f"code={code}")

    # What every run records: retries the chat recovered from, draft fallbacks, the configuration it really used.
    noisy = fake_transcript(1).replace(
        "\n[draft] nháp\n", "\n(network error ConnectError - retrying in 5s, attempt 2/3)\n\n[draft] nháp\n"
    ).replace("--- reviewing draft ---\n",
              "--- reviewing draft ---\n(review pass returned nothing - using the draft)\n")
    calls, code = run_main(["--out", str(tmp / "e"), "T01"], [noisy])
    rec = json.loads((tmp / "e" / "summary.json").read_text(encoding="utf-8"))["runs"][0]
    check("summary records retries, draft fallbacks and the effective configuration",
          rec.get("retries") == 1 and rec.get("fallbacks") == 1 and rec.get("answered") == 1
          and rec.get("config") == BANNER.strip(), repr(rec))

    # ------------------------------------------------------------ run.py end to end: real chat, fake server
    out = tmp / "e2e"
    p = subprocess.run([sys.executable, str(BENCH / "run.py"), "--out", str(out), "--repeat", "2", "T09"],
                       cwd=PROJECT, env={**CHAT_ENV, "GEMINI_DEEPTHINK": "on", "GEMINI_TIMEOUT": "10"},
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8")) if (out / "summary.json").is_file() else {}
    graded = [grade.final_answers((out / f"T09_r{i}.txt").read_text(encoding="utf-8"), 3)
              for i in (1, 2) if (out / f"T09_r{i}.txt").is_file()]
    check("run.py end to end (T09 x 2, deepthink, fake server): 3 answered turns per run, 0 retries",
          [(r["answered"], r["retries"]) for r in summary.get("runs", [])] == [(3, 0), (3, 0)]
          and graded == [[ANSWER] * 3] * 2, f"code={p.returncode} stderr={p.stderr[-300:]!r} summary={summary}")
    check("run.py end to end: the recorded configuration says deepthink on and the timeout used",
          all("deepthink: on" in r.get("config", "") and "timeout: 10s" in r.get("config", "")
              for r in summary.get("runs", [])) and len(summary.get("runs", [])) == 2, repr(summary)[:300])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    server.close()

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
