# Kết quả đã chạy

Tất cả: `gemini-3.5-flash-lite`, thinking budget max (24576), deepthink bật, trừ khi ghi khác. Mỗi file `.txt` là toàn văn một lần chạy (`[draft]` = bản nháp, `Gemini:` = câu trả lời cuối).

Các thư mục ngày 2026-10-04 được tạo bằng phiên bản đầu của harness (trước khi có `bench/run.py`), nên dòng đầu file ghi lệnh hơi khác. Prompt thay đổi giữa các vòng; chỉ phiên bản cuối còn trong dự án (commit đầu tiên của git). Các phiên bản trung gian được mô tả dưới đây.

| Thư mục | Instruction | Yêu cầu phản biện (`REVIEW_PROMPT`) | Nội dung |
|---|---|---|---|
| `2026-10-04_results_v28` | V28 nguyên văn + phụ lục 17–18 | gọi mục theo tên, chưa thêm gì | 12 câu × 1 lần |
| `2026-10-04_rep_v28` | như trên | như trên | T02, T03, T09 × 3 |
| `2026-10-04_rep_v274` | `instruction.md` (V27.4) | như trên | T02, T03, T09 × 3 |
| `2026-10-04_rep_v28fix` | như `results_v28` nhưng sửa dòng "kết luận trước khi vấn đề đủ rõ" (`instruction_used.md`) | như trên | T02 × 3 |
| `2026-10-04_it2_suite`, `it2_rep` | vòng sửa 1: thêm đoạn hidden assumption (mục 4), sửa dòng mục 13, thêm "không biết ngày hôm nay" (mục 18) | thêm: kiểm ràng buộc lượt trước; giữ phần đúng của bản nháp; không LaTeX | 12 câu × 1; T03, T09, T11, T12 × 3 |
| `2026-10-04_it3_rep`, `it3_suite` | vòng sửa 2: thêm bước CALIBRATE (số liệu chung → trường hợp cụ thể), dòng "yêu cầu hình thức" (mục 13) | thêm: nêu giả định ngầm nếu kết luận phụ thuộc nó | T03, T07, T13, T14 × 3; 14 câu × 1 |
| `2026-10-04_final_suite` | bản cuối (= commit đầu tiên) | bản cuối: thêm "USER không nhìn thấy bản nháp" | 14 câu × 1 |
| `2026-10-04_final_debate.txt` | bản cuối | (debate không dùng REVIEW_PROMPT) | `debate.py --rounds 1`, câu startup |

Chấm các thư mục trên do Claude đọc, không mù; tiêu chí lúc đó chưa viết thành `RUBRIC.md`.

## So sánh có kiểm soát (chấm mù theo `RUBRIC.md`)

| Thư mục | Phiên bản | Nội dung |
|---|---|---|
| `2026-10-04_t12_on` | commit `8d4f9cc` (tag `v28-pre-bench`), deepthink bật | T12 × 20 |
| `2026-10-04_t12_off` | như trên, `--no-deepthink` | T12 × 20 |

Phiếu chấm mù, khóa, phán quyết và lý do (viết trước khi mở khóa): `blind/t12_deepthink.*`. Một người chấm (Claude).

| | deepthink bật | deepthink tắt |
|---|---|---|
| pass / partial / fail | 8 / 10 / 2 | 6 / 7 / 7 |
| fail vì LaTeX | 1 | 6 |
| fail vì mất hoặc phủ nhận bằng chứng (b) | 1 | 1 |
| (b) bị làm yếu (partial) | 3 | 1 |
| giữ (b) đầy đủ | 16/20 | 18/20 |
| ngoại lệ "short sleeper" | 2 (cả 2 do lượt phản biện thêm vào, bản nháp không có) | 0 |

Kết luận bước 2: tắt deepthink không sửa được T12. Tỷ lệ mất bằng chứng hai nhánh như nhau (1/20), còn LaTeX tăng từ 1 lên 6. Khác biệt 16 và 18 trên 20 không có ý nghĩa thống kê. Giả thuyết (chưa kiểm chứng): dòng "số liệu chung có áp dụng cho trường hợp cụ thể này không" trong `REVIEW_PROMPT` khiến lượt phản biện bịa ngoại lệ cá nhân cho một cơ chế sinh lý đã được xác lập.

## Sửa một dòng trong `REVIEW_PROMPT` (hướng B)

Thêm vào dòng hỏi "số liệu chung có áp dụng cho trường hợp cụ thể này không": "Nhưng không bịa ngoại lệ cá nhân để làm yếu một kết luận khoa học đã được xác lập vững: chỉ nêu ngoại lệ khi câu hỏi có dấu hiệu cụ thể, và nói rõ nếu ngoại lệ đó hiếm." Instruction, rubric, câu thử, model, deepthink giữ nguyên.

| Thư mục | Nội dung |
|---|---|
| `2026-10-04_t12_patch` | T12 × 20 |
| `2026-10-04_refclass_patch` | T03, T13, T14 × 10 (T14_r4 treo, bị loại) |
| `2026-10-04_refclass_patch_t14extra` | T14 × 1, chạy bù |

Luật quyết định viết trước khi chạy, và kết quả:

| Luật | Trước khi sửa | Sau khi sửa | Đạt? |
|---|---|---|---|
| T12: ngoại lệ "short sleeper" ≤ 2/20, mục tiêu 0 | 2/20 | 0/20 | đạt |
| T12: giữ bằng chứng đầy đủ ≥ 16/20 | 16/20 | 19/20 | đạt |
| T03, T13, T14: pass + partial ≥ 8/10 mỗi câu | (5/5 mỗi câu, 2026-10-04 it3 + final) | 10/10, 10/10, 10/10 | đạt |
| LaTeX không tăng | T12: 1/20 | T12: 2/20; T03/T13/T14: 0/30 | **không đạt theo nghĩa đen** (1 → 2, mức nhiễu) |
| Không có kiểu hỏng mới | | T12: 1 câu nhắc tới gợi ý trong bản nháp mà USER chưa thấy (không có chữ "bản nháp") | cùng loại với lỗi lộ bản nháp đã biết |

T12 chấm mù trộn với 20 câu cũ của `t12_on` (`blind/t12_patch.*`); người chấm nhận ra 20 câu cũ, nên phiếu này không thật sự mù giữa cũ và mới. Phán quyết cho các câu cũ trùng 20/20 với lần chấm trước. T03/T13/T14: `blind/refclass_patch.notes.md`.

Phát hiện phụ: T14_r4 treo ở lượt phản biện 415 giây. `gemini_mini.py` không đặt timeout cho request nên kết nối treo sẽ chờ vô hạn (chat tay thì Ctrl+C thoát được và giữ lịch sử).

## Cổng kiểm tra trước `baseline-v28` (luật viết trước khi chạy)

Phiên bản: dòng đã sửa trong `REVIEW_PROMPT` + timeout request (`GEMINI_TIMEOUT`, mặc định 180 s). Chạy T01–T14 × 1 vào `2026-10-04_regression`. Đây là kiểm tra hồi quy, không phải benchmark mới: nó chỉ hỏi pipeline còn chạy bình thường trên cả bộ câu thử không.

Cổng đạt nếu:
1. Cả 14 câu trả lời đủ mọi lượt (không crash, không treo; nếu có timeout thì phải được ghi nhận như lỗi có kiểm soát).
2. Mỗi câu pass hoặc partial theo `RUBRIC.md`.
3. Nếu một câu fail vì một kiểu lỗi đã biết là thỉnh thoảng xảy ra (T09 mất thu hồi tức thì; T12 mất hoặc làm yếu bằng chứng; LaTeX; nhắc tới bản nháp hoặc bước phản biện), chạy lại câu đó 3 lần; đạt nếu ít nhất 2/3 pass hoặc partial.
4. Fail kiểu chưa từng gặp: cổng không đạt, không gắn tag, báo lại.

### Kết quả cổng: **không đạt**

Pass 8, partial 4, fail 2 (`blind/regression.notes.md`). Hai lần fail là kiểu chưa từng gặp, nên theo luật 4 cổng không đạt và chưa gắn tag. Cả hai do lượt phản biện gây ra, theo đúng hướng câu chữ của dòng mới sửa ("chỉ nêu ngoại lệ khi câu hỏi có dấu hiệu cụ thể", "không làm yếu kết luận khoa học đã xác lập"):

- T07: bản nháp "PostgreSQL (trừ khi dữ liệu phi cấu trúc)." → câu trả lời cuối "PostgreSQL".
- T12: bản nháp có mục "Cách kiểm chứng nhanh" → câu trả lời cuối "Bạn không cần phải làm một bài nghiên cứu... để kiểm chứng thêm".

Mỗi lỗi thấy một lần: là giả thuyết có cơ chế rõ, chưa phải kết luận. Thử nghiệm 50 lần trước đó không có T07; T12 × 20 khi đó đều có phần kiểm chứng.

## Dòng sửa trong `REVIEW_PROMPT` bị loại khỏi baseline

Quyết định (2026-10-04): không đưa câu "Nhưng không bịa ngoại lệ cá nhân để làm yếu một kết luận khoa học đã được xác lập vững: chỉ nêu ngoại lệ khi câu hỏi có dấu hiệu cụ thể, và nói rõ nếu ngoại lệ đó hiếm." vào baseline. Nó cải thiện T12 trong mẫu đã đo, nhưng cổng kiểm tra bắt được hai kiểu hỏng mới do chính nó gây ra (T07, T12; xem trên). Đã gỡ câu này; `REVIEW_PROMPT` khớp từng ký tự với `v28-pre-bench`. Nếu muốn nghiên cứu tiếp, so sánh riêng `baseline-v28` với một phiên bản thử nghiệm có câu này, không sửa trực tiếp baseline.

## Cổng kiểm tra lần 2 (luật viết trước khi chạy)

Phiên bản: `REVIEW_PROMPT` và instruction như `v28-pre-bench` + timeout request (`GEMINI_TIMEOUT`, mặc định 180 s). Rubric, câu thử, model, cấu hình, deepthink giữ nguyên. Chạy T01–T14 × 1 vào `2026-10-04_regression_baseline`. Luật cổng giữ nguyên như lần 1 (luật 1–4 ở trên). Đây là phép đo mới cho baseline: không điền trước kết quả từ các lần chạy cũ (vd tỷ lệ "short sleeper" 2/20 của T12 trước đây). Đạt thì commit và gắn tag `baseline-v28`; không đạt thì báo lại, không commit.

### Kết quả cổng lần 2: **không đạt** (chưa commit, chưa gắn tag)

`blind/regression_baseline.notes.md`. 13/14 câu pass hoặc partial (12 pass, 1 partial). Hai kiểu hỏng mới của lần 1 (T07, T12) không còn. T05 gặp 1 lỗi mạng thật (ConnectError), tự thử lại và trả lời được. T09 fail vì kiểu lỗi đã biết (mất thu hồi tức thì); chạy lại × 3 chỉ đạt 1/3, dưới mức 2/3 của luật 3.

Điều chỉnh hồ sơ: con số "T09 5/6" trong README gộp nhiều phiên bản prompt. Riêng phiên bản `REVIEW_PROMPT` + instruction như `v28-pre-bench`, chấm theo `RUBRIC.md`, T09 đạt **1/5** (`final_suite` fail, `regression_baseline` fail, chạy lại 1/3). Lỗi này có từ trước khi thêm timeout (`final_suite`), và timeout không đổi nội dung prompt, nên không phải hồi quy do timeout. Luật 3 giả định lỗi T09 hiếm; dữ liệu cho thấy với phiên bản này thì không hiếm.

## Đo T09 × 20 (chỉ đo; giao thức viết trước khi chạy)

Cấu hình đúng như cổng lần 2 (prompt như `v28-pre-bench` + timeout); không đổi prompt, model, deepthink, rubric, timeout, chính sách thử lại. Chạy vào `2026-10-04_t09_baseline`. Chấm lượt 3 theo `RUBRIC.md`, ghi lý do của từng fail và lỗi có nằm sẵn trong bản nháp không. Không đặt ngưỡng: sau khi có số liệu, `baseline-v28` được cố định bất kể T09 đạt bao nhiêu, trừ khi phát sinh lỗi harness hoặc hạ tầng. 5 lần T09 trước đó với cùng phiên bản prompt (1/5) được báo riêng, không gộp vào n = 20.

### Trạng thái: dừng ở 16/20 (theo yêu cầu, trước khi đẩy lên GitHub)

Đã chạy xong 16 lần (`T09_r1` đến `T09_r16`, đều đủ 3 lượt), chưa chấm. Lần thứ 17 bị dừng giữa chừng nên không có file; thư mục chưa có `summary.json`. `baseline-v28` chưa được gắn tag; trạng thái hiện tại được commit dưới dạng WIP.

### Kết quả 16/20 (chấm theo `blind/t09_baseline.rules.md`, phiếu mù `blind/t09_baseline.*`)

Luật áp dụng rubric T09 được viết thành file trước khi mở phiếu. Một người chấm (Claude). Chưa chạy được r17–r20 vì phiên chấm không có `GEMINI_API_KEY`.

| | strict (chính thức) | lenient (chỉ tính read replica khi nói rõ dùng để đọc session) |
|---|---|---|
| pass / partial / fail | 4 / 1 / 11 | 6 / 2 / 8 |
| pass + partial | 5/16 (Wilson 95%: 14–56%) | 8/16 (28–72%) |

- Bản nháp lượt 3 đã fail ở 12/16 run (strict). Lượt phản biện: sửa được 2 (r7, r12), làm hỏng 1 (r11, thêm "hoặc polling ngắn"). Trong 11 fail, cơ chế hỏng có sẵn trong bản nháp ở 7, do lượt phản biện đưa vào ở 4.
- Cơ chế hỏng: read replica cho việc đọc session (3 nói rõ, 3 chung chung), cache cục bộ có TTL là phương án chính 2, JWT + cache `token_version` 1, polling 1, sticky session 1.
- 16/16 run: đủ 3 lượt, 1 lần chạy, 0 thử lại, 0 timeout, 0 lỗi kết nối; 1 lần dùng bản nháp vì phản biện rỗng (r7, lượt 2). Không có lỗi harness hay hạ tầng; 11 fail đều là MODEL_CAPABILITY / CURRENT_CONFIGURATION_LIMITATION.
- Thời gian từng run không có: harness chỉ ghi `summary.json` ở cuối, mà lần chạy bị dừng ở r17 (lỗi H4 dưới đây).

Mốc `baseline-v28` (định nghĩa, cấu hình, giới hạn, cách chạy nốt r17–r20): `bench/BASELINE.md`.

## Lỗi harness tìm thấy khi kiểm toán (2026-10-04, đã sửa)

Mỗi lỗi được tái hiện trên mã cũ trước khi sửa, rồi thành một kiểm tra trong `bench/test_harness.py` (hoặc `test_offline.py` / `test_timeout.py`). Không sửa nào chạm tới prompt, `REVIEW_PROMPT`, model, deepthink, rubric, câu thử, timeout hay chính sách thử lại.

| Mã | Lỗi | Tái hiện trên mã cũ | Sửa |
|---|---|---|---|
| H1 | `run.py` gọi cứng `.venv/Scripts/python.exe` (chỉ có trên Windows) | Linux: `FileNotFoundError`, không chạy được câu nào | dùng venv đúng hệ điều hành, không có thì dùng Python đang chạy |
| H2 | `grade.py` không gắn câu trả lời với lượt: lượt không có câu trả lời làm lệch, `blind` (lấy câu cuối) chấm nhầm lượt trước | dữ liệu thật `rep_v274/T09_r2` (lượt 3 rỗng): trả về 2 câu, phiếu mù sẽ chấm lượt 2 như lượt 3; lượt 3 lỗi mạng: chấm lượt 2 | cắt transcript theo lượt (`You: `), lượt không có câu trả lời là `(no answer)` |
| H3 | Stream đứt giữa câu rồi thử lại: câu trả lời được chấm gồm cả phần đứt, dòng báo lỗi và chữ `Gemini:` thứ hai; `answered` đếm 2 cho 1 lượt | chat thật + server giả (`stall_mid` rồi `ok`) | câu trả lời của lượt là `Gemini:` đầu tiên sau lần khởi động stream cuối cùng; `answered` đếm theo lượt |
| H4 | `summary.json` chỉ được ghi khi chạy xong toàn bộ | `2026-10-04_t09_baseline` không có `summary.json` (mất thời gian, số lần chạy của r1–r16) | ghi lại sau mỗi run |
| H5 | Chạy tiếp một lần lặp bị dừng sẽ ghi đè `T09_r1…` | `--repeat 4` vào thư mục cũ ghi đè `T09_r1.txt` | thêm `--start N`; từ chối ghi đè transcript đã có; nối `summary.json` cũ, từ chối nếu khác instruction / chat args |
| H6 | File instruction không tồn tại: chat chạy **không có system prompt**, `summary.json` vẫn ghi tên file | `--instruction no_such.md`: chạy xong, ghi `no_such.md` | từ chối trước khi chạy |
| H7 | Điều kiện chạy lại cả câu khớp chuỗi ở bất kỳ đâu (khác `ERROR_MARKERS` đã chuyển sang đầu dòng) | câu trả lời nhắc "Network error" giữa dòng: chạy lại 3 lần, chờ 420 s, giữ mẫu khác | chỉ khớp ở đầu dòng; lỗi thật của chat vẫn được chạy lại |
| H8 | `test_offline.py` cần key thật: không có key thì dừng ở kiểm tra 8 (exit 1) | phiên này không có key: 8/9 rồi thoát | đặt key giả như `test_timeout.py` |
| H9 | `GEMINI_TIMEOUT=-1` (dễ nhầm với `-1` = dynamic của thinking budget): crash `ValueError` ở lượt chat đầu, mất phiên | chat thật + server giả: traceback, 0 request | từ chối khi khởi động, kèm thông báo |

Thêm vào `summary.json` của mỗi run: `retries` (số lần thử lại trong chat), `fallbacks` (dùng bản nháp vì phản biện rỗng), `config` (dòng banner: model, budget, deepthink, timeout, instruction mà chat thực sự dùng). Banner của chat in thêm `timeout`.

Kiểm tra phép đo không đổi: với parser đã sửa, mọi lượt có câu trả lời trong 235 transcript đã lưu cho ra đúng văn bản như parser cũ (`test_harness.py`); phiếu mù `t09_baseline` sinh lại trùng từng byte. Không phán quyết cũ nào đổi; các phiếu T12 trước đây không chứa run nào bị H2/H3.
