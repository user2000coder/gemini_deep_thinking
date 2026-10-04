"""Read and grade benchmark results (criteria: RUBRIC.md). Keyword matching proved unreliable, so verdicts
are given by a reader; this script only extracts answers and keeps the reader blind to which run is which.

    python bench/grade.py show RESULTS_DIR [--case T12]       # final answers, with a LaTeX flag
    python bench/grade.py blind NAME DIR1 DIR2 ... --case T12  # shuffled sheet + hidden key
    python bench/grade.py unblind NAME                         # tally verdicts per results dir

Blind flow: `blind` writes results/blind/NAME.md (answers under random codes) and NAME.key.json.
The reader writes NAME.verdicts.json as {"code": "pass" | "fail" | "partial", ...}; `unblind` joins them.
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
BLIND = RESULTS / "blind"
LATEX = re.compile(r"\$[^$\n]+\$|\\(?:frac|times|text|mathbf|approx|rightarrow)")
sys.stdout.reconfigure(encoding="utf-8")


def finals(path):
    """Final answers of one run, in turn order (text after 'Gemini:' up to the token line)."""
    return [m.strip() for m in re.findall(r"Gemini:(.*?)\ntokens:", path.read_text(encoding="utf-8"), flags=re.S)]


def runs(folder, case):
    return [f for f in sorted((RESULTS / folder).glob("T*.txt")) if not case or f.stem.split("_")[0] == case]


def show(args):
    for f in runs(args.dir, args.case):
        answers = finals(f)
        fallback = "returned nothing" in f.read_text(encoding="utf-8")
        print(f"\n######## {args.dir}/{f.stem}  turns answered: {len(answers)}"
              f"  LaTeX: {'YES' if any(LATEX.search(a) for a in answers) else 'no'}  draft fallback: {fallback}")
        for i, a in enumerate(answers, 1):
            print(f"--- turn {i} ---\n{a}")


def blind(args):
    items = [(d, f.stem, finals(f)) for d in args.dirs for f in runs(d, args.case)]
    random.Random(args.name).shuffle(items)
    BLIND.mkdir(parents=True, exist_ok=True)
    key, sheet = {}, [f"# Blind sheet {args.name}: case {args.case}, {len(items)} answers\n"]
    for i, (d, stem, answers) in enumerate(items, 1):
        code = f"A{i:03d}"
        key[code] = {"dir": d, "run": stem}
        last = answers[-1] if answers else "(no answer)"
        sheet.append(f"\n## {code}\n\n{last}\n")
    (BLIND / f"{args.name}.md").write_text("".join(sheet), encoding="utf-8")
    (BLIND / f"{args.name}.key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"wrote {BLIND / (args.name + '.md')} ({len(items)} answers); key kept in {args.name}.key.json")


def unblind(args):
    key = json.loads((BLIND / f"{args.name}.key.json").read_text(encoding="utf-8"))
    verdicts = json.loads((BLIND / f"{args.name}.verdicts.json").read_text(encoding="utf-8"))
    missing = sorted(set(key) - set(verdicts))
    if missing:
        sys.exit(f"No verdict yet for: {', '.join(missing)}")
    tally = {}
    for code, where in key.items():
        tally.setdefault(where["dir"], {}).setdefault(verdicts[code], []).append(where["run"])
    for d, by_verdict in tally.items():
        total = sum(len(v) for v in by_verdict.values())
        print(f"{d}: " + "  ".join(f"{v} {len(r)}/{total}" for v, r in sorted(by_verdict.items())))
        for v, r in sorted(by_verdict.items()):
            if v != "pass":
                print(f"    {v}: {', '.join(sorted(r))}")


def main():
    p = argparse.ArgumentParser(description="Read and blind-grade benchmark results.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("dir")
    s.add_argument("--case")
    b = sub.add_parser("blind")
    b.add_argument("name")
    b.add_argument("dirs", nargs="+")
    b.add_argument("--case", required=True)
    u = sub.add_parser("unblind")
    u.add_argument("name")
    args = p.parse_args()
    {"show": show, "blind": blind, "unblind": unblind}[args.cmd](args)


if __name__ == "__main__":
    main()
