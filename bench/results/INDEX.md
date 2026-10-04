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
