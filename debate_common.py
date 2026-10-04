"""Shared plumbing for the two debate agents (agent_a.py, agent_b.py): message shapes and the Gemini call.

Settings come from .env (see gemini_mini.py): GEMINI_API_KEY, GEMINI_MODEL, GEMINI_THINKING_BUDGET,
GEMINI_INSTRUCTION, GEMINI_TIMEOUT.
"""

import os
import time

import httpx
from fastapi import HTTPException
from google.genai import errors, types
from pydantic import BaseModel, Field

from gemini_mini import load_instruction, load_timeout, make_client, parse_budget  # importing it also loads .env

HOST = "127.0.0.1"
CONSENSUS = "ĐỒNG THUẬN"  # the critic opens its turn with this when it has no material objection left
LABELS = {"proposer": "đề xuất", "critic": "phản biện"}
QUIET = bool(os.getenv("AGENT_QUIET"))  # set by debate.py, which prints the turns itself


def log(name, message):
    """Activity line in the agent's own terminal, so a hand-started agent visibly does something."""
    if not QUIET:
        print(f"[agent {name}] {message}", flush=True)


def banner(agent, port, hint):
    log(agent.name, f"({LABELS[agent.role]}) đang chạy tại http://{HOST}:{port}  |  model: {agent.model}")
    log(agent.name, f"{hint}  |  Ctrl+C để dừng")


class Turn(BaseModel):
    agent: str
    role: str
    text: str
    tokens: dict[str, int] = {}


class TurnRequest(BaseModel):
    question: str
    transcript: list[Turn] = []


class DebateRequest(BaseModel):
    question: str
    rounds: int = Field(2, ge=1, le=5, description="max critique rounds; each costs 2 Gemini calls")


class Agent:
    """One Gemini persona: instruction.md + a role prompt, and the turn-taking call."""

    def __init__(self, name, role, role_prompt, model=None):
        self.name, self.role = name, role
        self.model = model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        instruction, _ = load_instruction(None)
        self.config = types.GenerateContentConfig(
            system_instruction="\n\n".join(filter(None, [instruction, role_prompt])),
            thinking_config=types.ThinkingConfig(
                thinking_budget=parse_budget(os.getenv("GEMINI_THINKING_BUDGET") or "-1", self.model)),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # no tools
        )
        self.client = make_client(load_timeout())  # reads GEMINI_API_KEY / GOOGLE_API_KEY and GEMINI_TIMEOUT

    def build_prompt(self, question, transcript):
        """The whole debate so far as one user message, ending with whose turn it is."""
        parts = [f"CÂU HỎI CỦA USER:\n{question}"]
        if transcript:
            parts.append("DIỄN BIẾN TRANH LUẬN:")
            parts += [f"[Agent {t.agent} - {LABELS.get(t.role, t.role)}]\n{t.text}" for t in transcript]
        parts.append(f"Đến lượt bạn (agent {self.name}, {LABELS[self.role]}). Viết lượt của mình.")
        return "\n\n".join(parts)

    def call_gemini(self, prompt, attempts=3):
        """Return (text, token counts). Retries 5xx (overloaded), 429 (rate limit) and dropped connections."""
        for attempt in range(1, attempts + 1):
            try:
                r = self.client.models.generate_content(model=self.model, contents=prompt, config=self.config)
                break
            except errors.APIError as e:
                if attempt == attempts or not (e.code == 429 or (e.code or 0) >= 500):
                    raise
                wait = (20 if e.code == 429 else 5) * attempt
                print(f"[agent {self.name}] Gemini error {e.code} - retrying in {wait}s"
                      f" ({attempt + 1}/{attempts})", flush=True)
                time.sleep(wait)
            except httpx.TransportError as e:
                if attempt == attempts:
                    raise
                wait = 5 * attempt
                print(f"[agent {self.name}] network error {type(e).__name__} - retrying in {wait}s"
                      f" ({attempt + 1}/{attempts})", flush=True)
                time.sleep(wait)
        u = r.usage_metadata
        tokens = {"prompt": u.prompt_token_count or 0, "thinking": u.thoughts_token_count or 0,
                  "answer": u.candidates_token_count or 0} if u else {}
        return (r.text or "").strip(), tokens

    def take_turn(self, question, transcript):
        """This agent's next turn; Gemini failures become HTTP 502 for the caller."""
        log(self.name, f"đang hỏi Gemini để viết lượt {LABELS[self.role]} (đã có {len(transcript)} lượt trước)...")
        try:
            text, tokens = self.call_gemini(self.build_prompt(question, transcript))
        except errors.APIError as e:
            log(self.name, f"LỖI Gemini {e.code}: {e.message}")
            raise HTTPException(502, f"agent {self.name}: Gemini error {e.code}: {e.message}")
        except httpx.TransportError as e:
            log(self.name, f"LỖI mạng khi gọi Gemini: {type(e).__name__}: {e}")
            raise HTTPException(502, f"agent {self.name}: network error calling Gemini: {type(e).__name__}: {e}")
        if not text:
            raise HTTPException(502, f"agent {self.name}: Gemini returned an empty answer")
        log(self.name, f"viết xong: thinking {tokens.get('thinking', 0)} | answer {tokens.get('answer', 0)} tokens")
        return Turn(agent=self.name, role=self.role, text=text, tokens=tokens)
