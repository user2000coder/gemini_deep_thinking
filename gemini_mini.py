"""Mini Gemini chat with thinking - streams the model's thought summary, then its answer.

Setup:
    pip install -r requirements.txt
    put your key in .env next to this file:  GEMINI_API_KEY=...   (key: https://aistudio.google.com/apikey)
    optionally pick the model there too:     GEMINI_MODEL=gemini-3.5-flash-lite   (--model overrides it)

Instruction (system prompt) - steers how the model reasons and answers:
    edit instruction.md next to this file, or point GEMINI_INSTRUCTION in .env at another file.
    --system "..." overrides it for one run; /reset in chat reloads the file.

Deepthink (GEMINI_DEEPTHINK=on in .env, --deepthink / --no-deepthink, /deep in chat):
    each message runs twice - a draft, then an independent review of that draft that writes the final answer.
    Catches misread questions and hidden assumptions the first pass misses; costs ~2x tokens and time.

Usage:
    python gemini_mini.py                                   # interactive chat
    python gemini_mini.py "Why is the sky blue?"            # one-shot
    python gemini_mini.py --model gemini-2.5-flash --budget 2048
    python gemini_mini.py --budget 0 --hide-thoughts --no-deepthink   # fastest, cheapest

Thinking budget (tokens): max = deepest the model allows, -1 = dynamic (model decides), 0 = off.
Set GEMINI_THINKING_BUDGET in .env (--budget overrides it).
    gemini-2.5-flash       0 .. 24576
    gemini-3.5-flash-lite  accepts thinking_budget too (max -> 24576)
    gemini-2.5-flash-lite / gemini-2.5-pro: no longer available to new API users
"""

import argparse
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")  # loads the GEMINI_* settings; real env vars take precedence

sys.stdout.reconfigure(encoding="utf-8")  # Windows pipes/redirects default to cp1252, which can't print Vietnamese

if sys.stdout.isatty():
    DIM, BOLD, CYAN, RESET = "\033[2m", "\033[1m", "\033[36m", "\033[0m"
else:
    DIM = BOLD = CYAN = RESET = ""

# Second deepthink pass. Refers to instruction sections by name, not number, so it fits both
# instruction.md (V27.4) and instruction_v28.md, which number their sections differently.
REVIEW_PROMPT = """CÂU HỎI CỦA USER:
{question}

BẢN NHÁP TRẢ LỜI (chưa kiểm chứng):
{draft}

Đóng vai người phản biện độc lập cho bản nháp (bước ATTACK của REASONING PROTOCOL): đọc lại câu hỏi từng chữ, tìm bẫy về thì, phủ định, đơn vị, giả định ngầm, cách hiểu khác; kiểm tra bản nháp có tính sai hay kết luận vượt evidence không.
Nếu kết luận chỉ đúng khi một giả định ngầm đúng (vd: số liệu chung có thật sự áp dụng cho trường hợp cụ thể này không), câu trả lời phải nêu giả định đó và kết luận đổi thế nào nếu nó sai.
Nếu đề có nhiều cách hiểu hợp lý dẫn tới đáp án khác nhau, câu trả lời phải nêu rõ từng cách hiểu và đáp án tương ứng (phần COMMUNICATION), thay vì ngầm chọn một.
Kiểm tra câu trả lời không vi phạm ràng buộc, quyết định hay phương án đã bị loại mà USER nêu ở các lượt trước.
Giữ lại phần đúng của bản nháp: evidence, giả định đã nêu, nhãn UNVERIFIED / ước tính cho claim chưa kiểm chứng (kể cả khi USER đòi bỏ). Không thêm thuật ngữ hay số liệu mới khi không chắc. Tuân thủ RUNTIME CONSTRAINTS (không LaTeX).
Sau đó chỉ viết CÂU TRẢ LỜI CUỐI CÙNG gửi USER. USER không nhìn thấy bản nháp và không biết có bước phản biện, nên câu trả lời không được nhắc tới "bản nháp", "phản biện" hay quá trình này; viết như thể trả lời thẳng câu hỏi."""


def parse_budget(value, model):
    """Thinking budget from a number or "max" (the model's ceiling)."""
    if str(value).strip().lower() == "max":
        return 32768 if "pro" in model else 24576
    return int(value)


def load_instruction(override):
    """Return (system instruction text or None, label saying where it came from)."""
    if override:
        return override, "--system"
    configured = os.getenv("GEMINI_INSTRUCTION")
    path = HERE / (configured or "instruction.md")  # an absolute path in .env also works
    if not path.is_file():
        if configured:
            print(f"{DIM}(instruction file not found: {path}){RESET}")
        return None, None
    text = path.read_text(encoding="utf-8-sig").strip()
    return (text, path.name) if text else (None, None)


def stream_pass(client, model, config, contents, final):
    """One streamed generation: thoughts dimmed, answer normal if final else dimmed as a draft.

    Returns (answer text, usage metadata).
    """
    usage, section, answer = None, None, []
    for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
        usage = chunk.usage_metadata or usage
        if not chunk.candidates or not chunk.candidates[0].content:
            continue
        for part in chunk.candidates[0].content.parts or []:
            if not part.text:
                continue
            if part.thought:
                if section != "thought":
                    print(f"\n{DIM}[thinking]{RESET}")
                    section = "thought"
                print(f"{DIM}{part.text}{RESET}", end="", flush=True)
            else:
                if section != "answer":
                    print(f"\n{BOLD}{CYAN}Gemini:{RESET} " if final else f"\n{DIM}[draft]{RESET} ", end="")
                    section = "answer"
                answer.append(part.text)
                print(part.text if final else f"{DIM}{part.text}{RESET}", end="", flush=True)
    print()
    return "".join(answer), usage


def with_retry(fn, attempts=3):
    """Call fn, retrying 5xx (e.g. 503 overloaded) and dropped connections with a growing wait."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except (errors.ServerError, httpx.TransportError) as e:
            if attempt == attempts:
                raise
            wait = 5 * attempt
            what = f"server error {e.code}" if isinstance(e, errors.ServerError) else f"network error {type(e).__name__}"
            print(f"\n{DIM}({what} - retrying in {wait}s, attempt {attempt + 1}/{attempts}){RESET}")
            time.sleep(wait)


def ask(client, model, config, history, question, deepthink):
    """Answer one message (draft -> review -> final when deepthink) and append it to history on success.

    History keeps only the user's question and the final answer, never the draft or the review prompt.
    """
    user = types.Content(role="user", parts=[types.Part(text=question)])

    def run(contents, final):
        return with_retry(lambda: stream_pass(client, model, config, contents, final))

    if deepthink:
        draft, u1 = run(history + [user], final=False)
        print(f"{DIM}--- reviewing draft ---{RESET}")
        review = types.Content(role="user", parts=[types.Part(text=REVIEW_PROMPT.format(question=question, draft=draft))])
        answer, u2 = run(history + [review], final=True)
        if not answer.strip() and draft.strip():  # e.g. finish reason MALFORMED_RESPONSE on the review pass
            print(f"{DIM}(review pass returned nothing - using the draft){RESET}")
            print(f"{BOLD}{CYAN}Gemini:{RESET} {draft}")
            answer = draft
        usages = [u1, u2]
    else:
        answer, u = run(history + [user], final=True)
        usages = [u]

    if answer.strip():
        history += [user, types.Content(role="model", parts=[types.Part(text=answer)])]
    else:
        print(f"{DIM}(empty answer - not added to history){RESET}")

    usages = [u for u in usages if u]
    if usages:
        def total(field):
            return sum(getattr(u, field) or 0 for u in usages)
        passes = f"  ({len(usages)} passes)" if len(usages) > 1 else ""
        print(f"{DIM}tokens: prompt {total('prompt_token_count')} | thinking {total('thoughts_token_count')}"
              f" | answer {total('candidates_token_count')}{passes}{RESET}")


def main():
    p = argparse.ArgumentParser(description="Mini Gemini chat with thinking and deepthink.")
    p.add_argument("prompt", nargs="*", help="one-shot prompt; omit for interactive chat")
    p.add_argument("--model", default=os.getenv("GEMINI_MODEL") or "gemini-2.5-flash",
                   help="gemini-2.5-flash | gemini-3.5-flash-lite "
                        "(default: GEMINI_MODEL in .env, else gemini-2.5-flash)")
    p.add_argument("--budget", default=os.getenv("GEMINI_THINKING_BUDGET") or "-1",
                   help="thinking token budget: max, -1 = dynamic, 0 = off, or a number "
                        "(default: GEMINI_THINKING_BUDGET in .env, else -1)")
    p.add_argument("--deepthink", action=argparse.BooleanOptionalAction,
                   default=(os.getenv("GEMINI_DEEPTHINK") or "off").strip().lower() in ("on", "1", "true", "yes"),
                   help="draft -> review -> final answer, ~2x cost (default: GEMINI_DEEPTHINK in .env, else off)")
    p.add_argument("--hide-thoughts", action="store_true", help="think, but don't show the thought summary")
    p.add_argument("--system", help="system instruction text; overrides instruction.md for this run")
    args = p.parse_args()

    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        sys.exit("No API key - put GEMINI_API_KEY=... in .env (get a key at https://aistudio.google.com/apikey)")

    try:
        budget = parse_budget(args.budget, args.model)
    except ValueError:
        sys.exit(f"Invalid thinking budget {args.budget!r} - use max, -1 (dynamic), 0 (off) or a number")

    client = genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY
    thinking = types.ThinkingConfig(thinking_budget=budget, include_thoughts=not args.hide_thoughts)

    def load_config():
        instruction, source = load_instruction(args.system)
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            thinking_config=thinking,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # no tools; silences SDK warning
        )
        return config, source

    config, source = load_config()
    history = []
    deepthink = args.deepthink

    if args.prompt:
        try:
            ask(client, args.model, config, history, " ".join(args.prompt), deepthink)
        except errors.APIError as e:
            sys.exit(f"API error {e.code}: {e.message}")
        except httpx.TransportError as e:
            sys.exit(f"Network error: {type(e).__name__}: {e}")
        return

    print(f"{BOLD}{args.model}{RESET}  thinking budget: {budget}  deepthink: {'on' if deepthink else 'off'}"
          f"  instruction: {source or 'none'}")
    print(f"{DIM}/deep toggles deepthink, /reset clears history + reloads instruction, /exit quits{RESET}")
    while True:
        try:
            msg = input(f"\n{BOLD}You:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not msg:
            continue
        if msg in ("/exit", "/quit"):
            break
        if msg == "/reset":
            config, source = load_config()
            history.clear()
            print(f"{DIM}(history cleared, instruction: {source or 'none'}){RESET}")
            continue
        if msg == "/deep":
            deepthink = not deepthink
            print(f"{DIM}(deepthink {'on' if deepthink else 'off'}){RESET}")
            continue
        try:
            ask(client, args.model, config, history, msg, deepthink)
        except KeyboardInterrupt:
            print(f"\n{DIM}(interrupted){RESET}")
        except errors.APIError as e:
            print(f"\nAPI error {e.code}: {e.message}")
        except httpx.TransportError as e:
            print(f"\nNetwork error: {type(e).__name__}: {e}  (history kept - send the message again)")


if __name__ == "__main__":
    main()
