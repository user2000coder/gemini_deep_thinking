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

Chấm ngày 2026-10-04 do Claude đọc, không mù; tiêu chí lúc đó chưa viết thành `RUBRIC.md`. Từ bước tiếp theo, chấm theo `RUBRIC.md` và `grade.py blind`.
