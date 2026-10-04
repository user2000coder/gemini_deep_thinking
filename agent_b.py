"""Agent B - the critic. A FastAPI service that agent A calls to get its answers attacked.

    python agent_b.py          # serves on http://127.0.0.1:8002 (docs at /docs)

Endpoints:
    GET  /health  - who this agent is
    POST /turn    - {question, transcript} -> B's critique of A's latest answer;
                    opens with "ĐỒNG THUẬN" when nothing material is left to object to.

Env: AGENT_B_PORT (8002), DEBATE_MODEL_B (default GEMINI_MODEL).
"""

import os

import uvicorn
from fastapi import FastAPI

from debate_common import CONSENSUS, HOST, Agent, Turn, TurnRequest, banner, log

PORT = int(os.getenv("AGENT_B_PORT") or 8002)

# Appended to the instruction file. Sections are named, not numbered: instruction.md (V27.4) and
# instruction_v28.md number differently.
ROLE_PROMPT = f"""# VAI TRÒ TRONG TRANH LUẬN: NGƯỜI PHẢN BIỆN
Bạn kiểm tra câu trả lời mới nhất của agent kia cho câu hỏi của USER.
- Tự giải lại vấn đề một cách độc lập TRƯỚC, rồi mới so với câu trả lời (bước ATTACK của REASONING PROTOCOL).
- Tìm: tiền đề sai, đọc sai đề, tính sai, claim không có căn cứ, yêu cầu của đề bị bỏ sót, giả định ẩn.
- Chỉ nêu điểm làm thay đổi kết luận hoặc tính đúng đắn; không bắt bẻ câu chữ. Xếp theo mức độ nghiêm trọng; mỗi điểm nêu: sai ở đâu, vì sao, sửa thế nào.
- Không viết lại toàn bộ câu trả lời.
- Agent kia bác một điểm của bạn bằng lý do đúng → rút điểm đó, không lặp lại.
- Không còn điểm nào đáng kể → dòng đầu tiên ghi đúng "{CONSENSUS}", sau đó tối đa 2 câu giải thích."""

agent = Agent("B", "critic", ROLE_PROMPT, model=os.getenv("DEBATE_MODEL_B"))
app = FastAPI(title="Gemini debate agent B (critic)")


@app.get("/health")
def health():
    return {"agent": agent.name, "role": agent.role, "model": agent.model, "peer": None}


@app.post("/turn")
def turn(req: TurnRequest) -> Turn:
    log(agent.name, "nhận câu trả lời của agent A qua POST /turn")
    return agent.take_turn(req.question, req.transcript)


if __name__ == "__main__":
    banner(agent, PORT, f"chỉ nhận yêu cầu từ agent A; xem endpoint tại http://{HOST}:{PORT}/docs")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
