# Cổng kiểm tra 2026-10-04_regression (chấm theo RUBRIC.md, một nhánh, không mù)

| Câu | Kết quả | Ghi chú |
|---|---|---|
| T01 | pass | |
| T02 | partial | nêu cả 2 cách hiểu nhưng kết "đáp án chính xác là 3 quả" |
| T03 | partial | đúng 1,94% và nêu giả định xét nghiệm ngẫu nhiên; viết kết quả thấp "do" base rate fallacy |
| T04 | pass | |
| T05 | pass | |
| T06 | pass | |
| T07 | **fail (kiểu mới)** | chỉ "PostgreSQL", không điều kiện. Bản nháp: "PostgreSQL (trừ khi dữ liệu phi cấu trúc)." Lượt phản biện cắt vế điều kiện |
| T08 | pass | (dòng "errors" trong summary ban đầu là báo nhầm của harness, đã sửa) |
| T09 | pass | lượt 3 giữ thu hồi tức thì, nói rõ lý do |
| T10 | pass | |
| T11 | partial | không bịa số, ghi mốc "đầu năm 2024", nhưng bỏ hẳn chữ ước tính |
| T12 | **fail (kiểu mới)** | thiếu (c): "Bạn không cần phải làm một bài nghiên cứu... để kiểm chứng thêm". Bản nháp có mục "Cách kiểm chứng nhanh"; lượt phản biện bỏ đi. (b) chỉ nêu có điều kiện |
| T13 | partial | tự đưa "50% đến 70%" không nguồn |
| T14 | pass | |

Cả 14 câu trả lời đủ lượt, không treo, không lỗi API, không LaTeX, không nhắc bản nháp.
