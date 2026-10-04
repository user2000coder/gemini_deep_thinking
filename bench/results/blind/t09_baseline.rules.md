# Luật chấm T09 × 20 (viết trước khi mở phiếu `t09_baseline.md`)

Nguồn: dòng T09 trong `bench/RUBRIC.md` và tiền lệ chấm ở `regression_baseline.notes.md`. Không thêm điều kiện mới; chỉ viết rõ cách áp dụng để chấm nhất quán.

Chấm **lượt 3** (câu trả lời cuối cho "Giờ tải tăng gấp 10 lần, phương án nào scale tốt nhất? Trả lời ngắn.").

| Mã | Điều kiện | Kết quả |
|---|---|---|
| G1 | Đề xuất Redis như một phương án dùng được (nhắc Redis chỉ để nói là bị cấm thì không tính) | fail |
| G2 | Đề xuất JWT stateless / JWT ngắn hạn như một phương án (dựng lại phương án đã bị loại ở lượt 2). Nhắc JWT chỉ để loại thì không tính | fail |
| G3 | Phương án **chính** (câu trả lời cho "phương án nào scale tốt nhất") làm mất thu hồi tức thì: cache cục bộ / in-process cache có TTL, đọc session từ read replica bất đồng bộ, in-memory + sticky session không có điểm thu hồi chung | fail, kể cả khi có nói cái giá (tiền lệ `regression_baseline` T09) |
| G4 | Gợi ý **phụ** / dự phòng làm trễ thu hồi, **có** nói rõ cái giá (thu hồi bị trễ tối đa bằng TTL / độ trễ sao chép) | partial |
| G5 | Gợi ý phụ làm trễ thu hồi **không** nói cái giá | fail |
| G6 | Read replica được đề xuất để phục vụ việc đọc / kiểm tra session mà không nhắc độ trễ sao chép hoặc không nói kiểm tra thu hồi phải đọc từ primary | xử lý như cơ chế làm trễ không nói ra (G3 nếu nằm trong phương án chính, G5 nếu là gợi ý phụ) |
| G7 | Áp dụng cho mọi câu (RUBRIC): LaTeX, nói đã tra cứu, nhắc "bản nháp" hoặc bước phản biện | fail |
| G8 | Không dính G1–G7, phương án đề xuất vẫn thu hồi tức thì được | pass |

Khi nhiều điều kiện cùng đúng, lấy kết quả nặng nhất (fail > partial > pass). Mỗi phán quyết ghi mã điều kiện và trích đoạn quyết định.

Sau khi mở khóa, với mỗi fail / partial: đọc bản nháp lượt 3 (`[draft]`) và ghi lỗi đã có sẵn trong bản nháp (DRAFT) hay do lượt phản biện thêm vào (REVIEW). Không đổi phán quyết sau khi mở khóa.

Người chấm: Claude (một người chấm). Chỉ một nhánh (không so sánh hai phiên bản), nên phiếu mù chỉ che thứ tự chạy.
