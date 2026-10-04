# baseline-v28

Mốc so sánh cho chat 1 agent (`gemini_mini.py`). Phiên bản thử nghiệm sau này so với mốc này bằng cùng harness, cùng rubric, cùng số lần chạy; không sửa trực tiếp mốc.

**Trạng thái (2026-10-04): đã xác định, phép đo T09 chưa đủ.** T09 × 20 mới chạy và chấm được 16/20 lần; còn r17–r20 (cần `GEMINI_API_KEY`, xem "Tái hiện"). Tag git `baseline-v28` **chưa** được tạo: theo giao thức, tag được gắn sau khi đủ 20 lần, bất kể T09 đạt bao nhiêu.

## Định nghĩa

Hành vi của baseline do hai thứ quyết định: phần gửi cho model, và cách gọi model.

| Thành phần | Giá trị | Bằng chứng |
|---|---|---|
| System prompt | `instruction_v28.md` (V28.0 LITE + phụ lục runtime 17–18) | sha256 `2a75310928fba07b…`, giống nhau ở `v28-pre-bench`, `979a4ac` và bản hiện tại |
| Yêu cầu phản biện | `REVIEW_PROMPT` trong `gemini_mini.py` | sha256 `57c95742f8d3d4b3…`, giống nhau ở cả ba bản. Dòng sửa "không bịa ngoại lệ…" đã bị loại (INDEX.md) |
| Model | `gemini-3.5-flash-lite` | dòng banner của cả 16 run T09 và 14 câu `regression_baseline` |
| Thinking budget | `max` → 24576 | như trên |
| Deepthink | bật (nháp → phản biện → trả lời) | như trên |
| Timeout request | 180 s (`GEMINI_TIMEOUT` không đặt). Kiểm độc lập bằng `bench/test_timeout.py` | README, INDEX; banner từ nay ghi `timeout: 180s` |
| Thử lại trong chat | lỗi 5xx và lỗi mạng (kể cả timeout): 3 lần, chờ 5 s rồi 10 s. Lỗi 4xx (gồm 429) không thử lại | `with_retry`; `test_offline.py`, `test_timeout.py` |
| Thử lại của SDK | tắt (google-genai mặc định `retry_options=None` → 1 lần) | mã nguồn google-genai 2.28.0, `_api_client.retry_args` |
| Thử lại của harness | cả câu chạy lại tối đa 3 lần, chờ 70 s rồi 140 s, khi transcript có dòng bắt đầu bằng `API error 429`, `API error 5…` hoặc `Network error` | `bench/run.py`, `test_harness.py` |
| Rubric | `bench/RUBRIC.md` (không đổi từ `979a4ac`); luật áp dụng cho T09: `results/blind/t09_baseline.rules.md` | |
| Câu thử | T01–T14 trong `bench/run.py` (không đổi) | |

Commit: r1–r16 của T09 và `regression_baseline` chạy ở `979a4ac`. Bản hiện tại khác `979a4ac` ở `gemini_mini.py` đúng hai chỗ, không chạm tới phần gửi cho model: banner in thêm timeout, và `GEMINI_TIMEOUT` âm bị từ chối khi khởi động (trước đây làm crash lượt chat đầu tiên). Các sửa còn lại nằm ở harness (`bench/`). Nên r17–r20 chạy bằng bản hiện tại đo cùng một hệ thống.

`.env` của baseline (không ghi key):

```
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_THINKING_BUDGET=max
GEMINI_DEEPTHINK=on
GEMINI_INSTRUCTION=instruction_v28.md
# GEMINI_TIMEOUT không đặt (= 180)
```

Không có `.env` thì `gemini_mini.py` dùng mặc định khác hẳn (`gemini-2.5-flash`, budget -1, deepthink tắt, `instruction.md`). `run.py` luôn truyền instruction, nhưng model, budget, deepthink lấy từ `.env`; vì vậy `summary.json` giờ ghi dòng cấu hình thật của từng run (`config`), cần kiểm tra trước khi so sánh.

## Kết quả

### Hồi quy T01–T14 (`results/2026-10-04_regression_baseline`, mỗi câu 1 lần, không mù)

| T01 | T02 | T03 | T04 | T05 | T06 | T07 | T08 | T09 | T10 | T11 | T12 | T13 | T14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pass | pass | partial | pass | pass | pass | pass | pass | **fail** | pass | pass | pass | pass | pass |

T03 partial: gọi base rate fallacy là nguyên nhân. T05: 1 lỗi mạng thật (ConnectError), chat tự thử lại và trả lời được, không phải lỗi logic. T09 fail: kiểu lỗi đã biết (mất thu hồi tức thì). Chi tiết: `results/blind/regression_baseline.notes.md`. Phiên này không chạy lại T01–T14 vì không có key; kết quả trên là bằng chứng có sẵn trong repo cho đúng cấu hình baseline.

### T09 × 20, chỉ đo (`results/2026-10-04_t09_baseline`, đã chạy 16/20)

| | strict (luật chính thức) | lenient (độ nhạy) |
|---|---|---|
| pass / partial / fail | 4 / 1 / 11 | 6 / 2 / 8 |
| pass + partial | **5/16 = 31%** (Wilson 95%: 14–56%) | 8/16 = 50% (28–72%) |

- Không đặt ngưỡng đạt. Con số này là đặc tính của baseline, không phải mục tiêu tối ưu.
- Lỗi là thiết kế sai về thu hồi tức thì (read replica cho việc đọc session, cache cục bộ có TTL, polling, sticky session). Có sẵn ngay trong bản nháp lượt 3 ở 12/16 run; lượt phản biện sửa được 2, làm hỏng 1.
- Phân loại 11 fail: MODEL_CAPABILITY / CURRENT_CONFIGURATION_LIMITATION 11; harness, parser, mạng, timeout, thử lại: 0. Strict và lenient khác nhau ở 3 run (r1, r3, r6), do cách đọc "read replica" trong rubric (luật G6).
- 16/16 run đủ 3 lượt, 1 lần chạy, 0 thử lại, 0 timeout, 0 lỗi kết nối, 1 lần dùng bản nháp vì lượt phản biện rỗng (r7 lượt 2). Thời gian từng run không được ghi (lỗi harness H4, đã sửa).
- 5 lần T09 trước đó với cùng prompt (`final_suite`, `regression_baseline`, `regression_baseline_t09` × 3): 1/5, báo riêng, không gộp.

Bảng từng run, luật chấm, phiếu mù, khóa: `results/blind/t09_baseline.*`.

### Kiểm tra không gọi API (chạy trong phiên này: Linux, Python 3.11.15, google-genai 2.28.0, httpx 0.28.1)

| Script | Kết quả |
|---|---|
| `bench/test_offline.py` | 9/9 |
| `bench/test_timeout.py` | 13/13 |
| `bench/test_harness.py` | 19/19 |

Các lần chạy thật trước đó dùng Windows và một phiên bản google-genai không ghi lại (`requirements.txt` chỉ ghi `>=1.0`).

## Giới hạn đã biết

- T09: baseline thường mất thu hồi tức thì khi được hỏi về scale (xem trên). Là giới hạn của model với cấu hình này; theo quyết định đã chốt, không sửa prompt để cứu T09.
- Mỗi câu T01–T14 chỉ có 1 lần chạy ở cấu hình baseline (riêng T09 có 16 + 5). Một lần chạy chỉ là dấu hiệu.
- Một người chấm (Claude). Bản nháp được chấm sau khi mở khóa. Rubric T09 có chỗ phải diễn giải (G6); có báo cả strict và lenient.
- `gemini-3.5-flash-lite` là tên model phía Google; nội dung phía sau tên có thể đổi theo thời gian, nên r17–r20 chạy muộn hơn có thể không cùng phân phối với r1–r16. So sánh cấu hình mới với baseline nên chạy hai nhánh xen kẽ trong cùng khoảng thời gian.
- Lượt phản biện rỗng được thay bằng bản nháp, nhưng transcript không ghi lý do (finish reason), nên không phân loại sâu hơn được.
- `ĐỒNG THUẬN` của agent B chỉ được nhận khi đứng đầu lượt; nếu model viết `**ĐỒNG THUẬN**` thì cuộc tranh luận chạy tiếp tới hết vòng. Chưa thấy xảy ra, chưa sửa. (Chỉ ảnh hưởng `debate.py`, không ảnh hưởng benchmark.)

## Tái hiện

Cài đặt (Windows: `.venv\Scripts\python`; Linux/macOS: `.venv/bin/python`):

```
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bench/test_offline.py && .venv/bin/python bench/test_timeout.py && .venv/bin/python bench/test_harness.py
```

Hoàn tất T09 × 20 (cần `GEMINI_API_KEY` và `.env` như trên; khoảng 4 × 45 s):

```
.venv/bin/python bench/run.py --out 2026-10-04_t09_baseline --start 17 --repeat 4 T09
```

`--start 17` đặt tên r17–r20 vào cùng thư mục; harness từ chối ghi đè r1–r16. Kiểm tra `summary.json`: 4 run, `answered` 3, `config` ghi `gemini-3.5-flash-lite  thinking budget: 24576  deepthink: on  timeout: 180s  instruction: instruction_v28.md`. Sau đó chấm mù cả 20 câu với một phiếu mới, theo đúng `t09_baseline.rules.md`:

```
.venv/bin/python bench/grade.py blind t09_baseline_n20 2026-10-04_t09_baseline --case T09
# viết results/blind/t09_baseline_n20.verdicts.json, rồi:
.venv/bin/python bench/grade.py unblind t09_baseline_n20
```

Báo kết quả n = 20, và độ khớp giữa phán quyết mới với phán quyết cũ của r1–r16. Rồi gắn tag cho commit đã chạy r17–r20:

```
git tag -a baseline-v28 -m "baseline-v28: V28 prompt as v28-pre-bench + request timeout; T09 x 20 measured"
git push origin baseline-v28
```
