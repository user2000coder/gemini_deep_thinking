"""Run a debate between two Gemini agents that talk to each other over FastAPI.

    python debate.py --ui                                     # web page: ask questions in the browser
    python debate.py "câu hỏi"                                # one debate in the terminal
    python debate.py --file question.txt --rounds 3
    python debate.py --model-b gemini-2.5-flash "câu hỏi"     # a different model as the critic

Starts agent_a.py (proposer, port 8001) and agent_b.py (critic, port 8002) as two FastAPI servers.
With --ui it opens http://127.0.0.1:8001/ and keeps both running until Ctrl+C. Otherwise it
asks A to debate, prints each turn as it arrives, then stops both servers.
A answers -> B critiques -> A revises -> ... until B opens with "ĐỒNG THUẬN" or the rounds run out.
The final answer is A's last turn.

Cost: at most 1 + 2 x rounds Gemini calls (fewer when the critic agrees early).
Models: DEBATE_MODEL_A / DEBATE_MODEL_B in .env, or --model-a / --model-b; default is GEMINI_MODEL.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

from gemini_mini import BOLD, CYAN, DIM, HERE, RESET  # importing it also loads .env and sets UTF-8 output

HOST = "127.0.0.1"
LABELS = {"proposer": "đề xuất", "critic": "phản biện"}


def port_free(port):
    with socket.socket() as s:
        return s.connect_ex((HOST, port)) != 0


def start_agents(args, quiet):
    """Launch agent_a.py and agent_b.py, telling each its port and A where to find B.

    quiet silences the agents' own activity lines (for the terminal debate, which prints the turns itself).
    """
    env = os.environ.copy()
    env.update(AGENT_A_PORT=str(args.port_a), AGENT_B_PORT=str(args.port_b),
               AGENT_B_URL=f"http://{HOST}:{args.port_b}")
    env.pop("AGENT_QUIET", None)
    if quiet:
        env["AGENT_QUIET"] = "1"
    for var, model in (("DEBATE_MODEL_A", args.model_a), ("DEBATE_MODEL_B", args.model_b)):
        if model:
            env[var] = model
    return [subprocess.Popen([sys.executable, script], cwd=HERE, env=env) for script in ("agent_a.py", "agent_b.py")]


def stop_agents(procs):
    for proc in procs:
        proc.terminate()
    for proc in procs:
        proc.wait(timeout=10)


def serve_ui(args):
    """Start both agents, open the web page, and keep them running until Ctrl+C."""
    procs = start_agents(args, quiet=False)
    url = f"http://{HOST}:{args.port_a}/"
    try:
        for port, proc in zip((args.port_a, args.port_b), procs):
            wait_ready(port, proc)
        print(f"\n{BOLD}Giao diện hỏi đáp: {url}{RESET}   (Ctrl+C để dừng cả hai agent)\n", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        while all(proc.poll() is None for proc in procs):
            time.sleep(0.5)
        print("Một agent đã dừng - tắt agent còn lại.")
    except KeyboardInterrupt:
        print(f"\n{DIM}(đã dừng){RESET}")
    finally:
        stop_agents(procs)


def wait_ready(port, proc, timeout=40):
    """Block until the agent answers /health; return what it reports."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            sys.exit(f"Agent on port {port} exited during startup (code {proc.returncode}) - see the error above.")
        try:
            return httpx.get(f"http://{HOST}:{port}/health", timeout=2).json()
        except httpx.HTTPError:
            time.sleep(0.3)
    sys.exit(f"Agent on port {port} did not start within {timeout}s.")


def main():
    p = argparse.ArgumentParser(description="Two Gemini agents debate over FastAPI.")
    p.add_argument("prompt", nargs="*", help="the question; or use --file; or omit to be asked")
    p.add_argument("--file", type=Path, help="read the question from a text file (UTF-8)")
    p.add_argument("--rounds", type=int, default=2, help="max critique rounds, 1-5 (default 2)")
    p.add_argument("--model-a", default=os.getenv("DEBATE_MODEL_A"), help="proposer model (default: GEMINI_MODEL)")
    p.add_argument("--model-b", default=os.getenv("DEBATE_MODEL_B"), help="critic model (default: GEMINI_MODEL)")
    p.add_argument("--port-a", type=int, default=8001)
    p.add_argument("--port-b", type=int, default=8002)
    p.add_argument("--ui", action="store_true", help="open the web page and keep both agents running until Ctrl+C")
    p.add_argument("--no-browser", action="store_true", help="with --ui: don't open the browser automatically")
    args = p.parse_args()

    for port in (args.port_a, args.port_b):
        if not port_free(port):
            sys.exit(f"Port {port} is already in use - stop that program or pass --port-a / --port-b.")
    if args.ui:
        return serve_ui(args)

    if args.file:
        question = args.file.read_text(encoding="utf-8-sig").strip()
    elif args.prompt:
        question = " ".join(args.prompt)
    else:
        question = input(f"{BOLD}Câu hỏi:{RESET} ").strip()
    if not question:
        sys.exit("Empty question.")
    if not 1 <= args.rounds <= 5:
        sys.exit("--rounds must be between 1 and 5.")

    procs = start_agents(args, quiet=True)
    failed = False
    try:
        for port, proc in zip((args.port_a, args.port_b), procs):
            h = wait_ready(port, proc)
            print(f"{DIM}agent {h['agent']} ({LABELS[h['role']]}) http://{HOST}:{port}  model: {h['model']}{RESET}")

        counts, totals = {}, {"prompt": 0, "thinking": 0, "answer": 0}
        with httpx.stream("POST", f"http://{HOST}:{args.port_a}/debate", timeout=None,
                          json={"question": question, "rounds": args.rounds}) as r:
            if r.status_code != 200:
                r.read()
                sys.exit(f"Agent A refused the debate ({r.status_code}): {r.text}")
            for raw in r.iter_lines():
                if not raw:
                    continue
                ev = json.loads(raw)
                if ev["event"] == "turn":
                    counts[ev["agent"]] = counts.get(ev["agent"], 0) + 1
                    tok = ev.get("tokens", {})
                    for k in totals:
                        totals[k] += tok.get(k, 0)
                    print(f"\n{BOLD}{CYAN}=== Agent {ev['agent']} · {LABELS.get(ev['role'], ev['role'])}"
                          f" · lượt {counts[ev['agent']]} ==={RESET}")
                    print(ev["text"])
                    print(f"{DIM}tokens: prompt {tok.get('prompt', 0)} | thinking {tok.get('thinking', 0)}"
                          f" | answer {tok.get('answer', 0)}{RESET}")
                elif ev["event"] == "error":
                    failed = True
                    print(f"\n{BOLD}LỖI:{RESET} {ev['detail']}")
                elif ev["event"] == "done":
                    verdict = ("B đồng thuận" if ev["consensus"]
                               else f"hết {args.rounds} vòng, bản sửa cuối của A chưa được B xem lại")
                    print(f"\n{BOLD}=== KẾT THÚC: {verdict} ({ev['turns']} lượt) ==={RESET}")
                    print("Câu trả lời cuối cùng là lượt gần nhất của Agent A ở trên.")
                    print(f"{DIM}tổng tokens: prompt {totals['prompt']} | thinking {totals['thinking']}"
                          f" | answer {totals['answer']}{RESET}")
    except KeyboardInterrupt:
        failed = True
        print(f"\n{DIM}(interrupted){RESET}")
    finally:
        stop_agents(procs)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
