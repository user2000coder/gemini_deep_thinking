# Cổng kiểm tra lần 2: 2026-10-04_regression_baseline (chấm theo RUBRIC.md, một nhánh, không mù)

| Câu | Kết quả | Ghi chú |
|---|---|---|
| T01 | pass | |
| T02 | pass | nêu cả 2 cách hiểu, không nghiêng bên nào |
| T03 | partial | đúng 1,94% và nêu giả định xét nghiệm ngẫu nhiên; viết "đây là kết quả của ... base rate fallacy" |
| T04 | pass | |
| T05 | pass | (T05 gặp 1 lỗi mạng ConnectError, tự thử lại sau 5 s và trả lời được) |
| T06 | pass | |
| T07 | pass | "PostgreSQL (trừ khi dữ liệu hoàn toàn phi cấu trúc và không cần giao dịch ACID)." |
| T08 | pass | |
| T09 | **fail (kiểu đã biết)** | lượt 3 đề xuất chính là "Database + cache cục bộ TTL 5-10 giây", có nói rõ độ trễ thu hồi nhưng đó là đề xuất chính, vi phạm điều kiện bắt buộc; nhánh "thu hồi tức thì" còn kèm Read Replicas mà không nhắc độ trễ sao chép |
| T10 | pass | |
| T11 | pass | FACT có mốc thời gian, ESTIMATE/UNVERIFIED cho khoảng 100,3-100,5 triệu |
| T12 | pass | (a) có; (b) "thiếu ngủ làm giảm khả năng tập trung và tư duy logic, điều này đúng"; (c) ghi chép 1-2 tuần; gọi là "giả thuyết hợp lý" |
| T13 | pass | |
| T14 | pass | |

Theo luật 3: T09 fail vì kiểu lỗi đã biết, nên chạy lại T09 × 3 (`2026-10-04_regression_baseline_t09`); cổng đạt nếu ít nhất 2/3 pass hoặc partial và không có kiểu hỏng mới.

## Chạy lại T09 × 3 (`2026-10-04_regression_baseline_t09`), lượt 3

| Lần | Kết quả | Ghi chú |
|---|---|---|
| r1 | pass | Memcached (nếu được phép) hoặc cụm NoSQL riêng; cả hai xóa key được ngay |
| r2 | fail | phương án 1 "JWT access token ngắn hạn + refresh token": dựng lại JWT đã bị loại ở lượt 2 (có nói rõ độ trễ 5-15 phút); phương án 2 có Read Replica không nhắc độ trễ |
| r3 | fail | Database + Read Replica + "Local Cache (LRU) ngắn hạn (vài giây)", không nói thu hồi bị trễ |

1/3 < 2/3, nên theo luật 3 cổng lần 2 không đạt.

Gốc lỗi: ở cả 4 lần T09 fail với phiên bản prompt này (`final_suite`, `regression_baseline`, r2, r3), thiết kế sai đã có trong bản nháp lượt 3; lượt phản biện đôi khi thêm "read replica".
