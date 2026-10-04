"""Agent A - the proposer. A FastAPI service that answers, then argues with agent B over HTTP.

    python agent_a.py          # serves on http://127.0.0.1:8001 (web UI at /, API docs at /docs)

Endpoints:
    GET  /        - the question-and-answer web page (ui.html)
    GET  /status  - this agent's identity plus agent B's, or null if B is not reachable
    GET  /health  - who this agent is
    POST /turn    - {question, transcript} -> A's next turn
    POST /debate  - {question, rounds} -> NDJSON stream, one line per turn:
                    A answers, POSTs the transcript to B's /turn, revises, and repeats until
                    B opens its turn with "ĐỒNG THUẬN" or the rounds run out.

Env: AGENT_A_PORT (8001), AGENT_B_URL (http://127.0.0.1:8002), DEBATE_MODEL_A (default GEMINI_MODEL).
"""

import json
import os
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from debate_common import CONSENSUS, HOST, Agent, DebateRequest, Turn, TurnRequest, banner, log

PORT = int(os.getenv("AGENT_A_PORT") or 8001)
PEER_URL = (os.getenv("AGENT_B_URL") or f"http://{HOST}:8002").rstrip("/")
UI_FILE = Path(__file__).with_name("ui.html")

# Appended to the instruction file. No section numbers: instruction.md (V27.4) and instruction_v28.md number differently.
ROLE_PROMPT = """# VAI TRÒ TRONG TRANH LUẬN: NGƯỜI ĐỀ XUẤT
Bạn trả lời câu hỏi của USER; sau đó một agent khác phản biện bạn.
- Lượt đầu: trả lời đầy đủ câu hỏi.
- Các lượt sau: xét TỪNG điểm phản biện. Điểm đúng → nhận và sửa. Điểm sai → bác bỏ kèm lý do cụ thể. Không nhượng bộ vì lịch sự, không cố thủ vì đã lỡ nói.
- Mỗi lượt sau gồm 2 phần: "PHẢN HỒI PHẢN BIỆN" (ngắn, từng điểm: NHẬN hoặc BÁC + lý do), rồi "CÂU TRẢ LỜI ĐÃ SỬA" (bản đầy đủ, tự đứng được, gửi thẳng cho USER được)."""

agent = Agent("A", "proposer", ROLE_PROMPT, model=os.getenv("DEBATE_MODEL_A"))
app = FastAPI(title="Gemini debate agent A (proposer)")


def ask_peer(question, transcript):
    """POST the debate so far to agent B's /turn and return B's turn."""
    log(agent.name, f"gửi câu trả lời sang agent B: POST {PEER_URL}/turn")
    r = httpx.post(f"{PEER_URL}/turn", timeout=900,
                   json={"question": question, "transcript": [t.model_dump() for t in transcript]})
    if r.status_code != 200:
        raise HTTPException(502, f"agent B at {PEER_URL} answered {r.status_code}: {r.text[:500]}")
    theirs = Turn(**r.json())
    agreed = theirs.text.upper().startswith(CONSENSUS)
    log(agent.name, "nhận phản hồi từ agent B: " + ("B ĐỒNG THUẬN" if agreed else "B còn phản biện"))
    return theirs


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return UI_FILE.read_text(encoding="utf-8")  # read per request, so edits show on refresh


@app.get("/health")
def health():
    return {"agent": agent.name, "role": agent.role, "model": agent.model, "peer": PEER_URL}


@app.get("/status")
def status():
    """For the web page: who A is, and who B is (null when B is not running)."""
    try:
        b = httpx.get(f"{PEER_URL}/health", timeout=3).json()
    except (httpx.HTTPError, ValueError):
        b = None
    return {"a": health(), "b": b}


@app.post("/turn")
def turn(req: TurnRequest) -> Turn:
    return agent.take_turn(req.question, req.transcript)


@app.post("/debate")
def debate(req: DebateRequest):
    def run():
        def line(obj):
            return json.dumps(obj, ensure_ascii=False) + "\n"

        transcript, consensus = [], False
        log(agent.name, f"bắt đầu tranh luận (tối đa {req.rounds} vòng): {req.question[:80]}")
        try:
            transcript.append(agent.take_turn(req.question, transcript))
            yield line({"event": "turn", **transcript[-1].model_dump()})
            for _ in range(req.rounds):
                transcript.append(ask_peer(req.question, transcript))
                yield line({"event": "turn", **transcript[-1].model_dump()})
                if transcript[-1].text.upper().startswith(CONSENSUS):
                    consensus = True
                    break
                transcript.append(agent.take_turn(req.question, transcript))
                yield line({"event": "turn", **transcript[-1].model_dump()})
        except HTTPException as e:
            yield line({"event": "error", "detail": e.detail})
            return
        except httpx.HTTPError as e:
            yield line({"event": "error", "detail": f"cannot reach agent B at {PEER_URL}: {e!r}"})
            return
        log(agent.name, f"kết thúc sau {len(transcript)} lượt: " + ("B đồng thuận" if consensus else "hết vòng"))
        yield line({"event": "done", "consensus": consensus, "turns": len(transcript)})

    return StreamingResponse(run(), media_type="application/x-ndjson")


if __name__ == "__main__":
    banner(agent, PORT, f"giao diện hỏi đáp: http://{HOST}:{PORT}/")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
