# T09 × 20 (đo baseline): phán quyết phiếu mù `t09_baseline.md`

Luật: `t09_baseline.rules.md` (viết trước khi mở phiếu). Phần "Phán quyết" dưới đây viết **trước khi mở khóa**; phần "Sau khi mở khóa" viết sau.

Công khai: trước khi viết luật, người chấm đã đọc toàn văn `T09_r1` khi kiểm tra định dạng transcript (không chấm lúc đó). Mọi câu khác được đọc lần đầu trên phiếu mù.

## Phán quyết (strict, theo đúng luật đã viết)

| Mã | Kết quả | Luật | Đoạn quyết định |
|---|---|---|---|
| A001 | fail | G3 | phương án chính "Database kết hợp Local Cache ngắn tại App (Hybrid)", có nói trễ vài giây nhưng là đề xuất chính; nhánh "tuyệt đối" còn kèm Read Replica không nhắc độ trễ |
| A002 | fail | G3 | phương án chính "Database kết hợp Local Cache (TTL ngắn, khoảng 5-10 giây)" |
| A003 | fail | G6→G3 | phương án chính "Database tối ưu hạ tầng (Read Replica + Connection Pooling)", không nhắc độ trễ sao chép. Local cache được đồng bộ bằng LISTEN/NOTIFY (không tính là trễ). Memcached "nếu chỉ cấm Redis" không tính là vi phạm (tiền lệ) |
| A004 | fail | G3 | phương án chính: local cache "đồng bộ qua LISTEN/NOTIFY **hoặc polling ngắn**" và khẳng định vẫn thu hồi tức thời; polling làm trễ thu hồi bằng chu kỳ polling, không nói ra |
| A005 | fail | G6→G3 | "Định tuyến các request đọc/kiểm tra session sang **Read Replicas**", không nhắc độ trễ; nhắc JWT chỉ để loại |
| A006 | partial | G4 | nhánh giữ ràng buộc: Database thuần (index + PgBouncer), thu hồi tức thì; nhánh phụ local cache TTL có nói rõ trễ 30–60 giây |
| A007 | pass | G8 | Database session store; nếu nghẽn thì tách DB riêng / NoSQL, index `session_id`; không cơ chế trễ |
| A008 | pass | G8 | Managed NoSQL (DynamoDB / MongoDB), xóa theo khóa; dự phòng DB quan hệ + PgBouncer. (Ghi chú ngoài rubric: DynamoDB mặc định đọc eventually consistent; rubric không liệt kê nên không trừ) |
| A009 | fail | G6→G5 | nhánh 2 "SQL có tối ưu index/replica", không nhắc độ trễ sao chép; nhánh 1 Memcached không tính là vi phạm |
| A010 | fail | G6→G3 | "Read Replica cho việc kiểm tra session trên mỗi request, Master cho việc ghi và thu hồi" và khẳng định "đáp ứng chính xác ràng buộc thu hồi tức thì" |
| A011 | fail | G3 | phương án chính JWT + `token_version` trong DB, rồi "**bắt buộc phải cache `token_version` ở RAM của app trong vài giây**" mà vẫn nói thu hồi tức thì |
| A012 | fail | G3 | nhánh 2 "Sticky Sessions tại Load Balancer", session trên RAM từng app server, không có điểm thu hồi chung và không nhắc tới thu hồi; còn coi DB là sẽ quá tải |
| A013 | pass | G8 | Memcached nếu chỉ cấm Redis; nếu không thì DB + PgBouncer trên master, nói rõ Read Replica không giúp |
| A014 | fail | G6→G3 | giả định của phương án chính: "thêm Read Replicas ... để gánh thêm 10x lượng query session", không nhắc độ trễ; dự phòng cache RAM 3–5 giây có nói cái giá (G4) |
| A015 | fail | G6→G3 | "thêm **Read Replicas cho các request đọc session**", không nhắc độ trễ (dù có cảnh báo đúng về local cache TTL) |
| A016 | pass | G8 | Cloud key-value (DynamoDB, Firestore); on-premise thì tách cụm DB riêng |

Strict: pass 4, partial 1, fail 11.

## Độ nhạy: cách đọc G6 (read replica)

G6 là chỗ dễ tranh cãi nhất của rubric: nhắc "Read Replica" như một cách scale DB chung chung có phải là "đọc session từ read replica bất đồng bộ" không. Phiên bản lenient chỉ áp G6 khi câu trả lời **nói rõ** đưa việc đọc / kiểm tra session sang replica (A005, A010, A015). Các câu chỉ nhắc replica chung chung (A003, A009, A014) được chấm lại theo các luật còn lại. Không đổi luật nào khác.

| Mã | strict | lenient |
|---|---|---|
| A003 | fail | pass |
| A009 | fail | pass |
| A014 | fail | partial (G4) |

Lenient: pass 6, partial 2, fail 8. Kết quả chính thức của baseline là **strict** (đúng luật viết trước); lenient chỉ để thấy kết luận phụ thuộc cách đọc này bao nhiêu.

## Sau khi mở khóa

Khóa: `t09_baseline.key.json`. Phiếu được sinh lại bằng `grade.py` đã sửa (xem INDEX, "Lỗi harness"): phiếu và khóa trùng từng byte với bản đã chấm, nên việc sửa parser không đổi phép đo.

Chấm bản nháp lượt 3 (`[draft]`) theo cùng luật được làm **sau** khi mở khóa, không mù; chỉ dùng để biết lỗi sinh ra ở đâu. Siêu dữ liệu (lượt có câu trả lời, số lần thử lại, timeout, lỗi kết nối, fallback về bản nháp) đếm bằng `run.py` (`count_answered`, `RETRY`, `FALLBACK`) trên transcript.

| Run | Mã | Final strict | Final lenient | Bản nháp lượt 3 (strict) | Cơ chế hỏng ở câu trả lời cuối | Cơ chế đó sinh ra ở |
|---|---|---|---|---|---|---|
| r1 | A014 | fail | partial | fail ("Tách Read/Write Replicas") | read replica, chung chung (+ cache 3–5 s dự phòng, có nói giá) | DRAFT (replica); cache dự phòng do REVIEW thêm |
| r2 | A011 | fail | fail | fail (cache `token_version` vài giây) | JWT + `token_version`, cache RAM vài giây không nói trễ | DRAFT |
| r3 | A009 | fail | pass | fail ("SQL có sharding/replica") | read replica, chung chung | DRAFT |
| r4 | A002 | fail | fail | fail (local cache TTL 5–10 s là phương án chính) | local cache TTL là phương án chính | DRAFT (REVIEW thêm phần nói giá, vẫn là phương án chính) |
| r5 | A005 | fail | fail | fail (JWT + blacklist + local cache; replica ở nhánh dự phòng) | read replica cho việc đọc session, nói rõ | DRAFT (REVIEW đưa nhánh replica lên làm phương án chính) |
| r6 | A003 | fail | pass | fail (local cache TTL 30–60 s là phương án chính) | read replica, chung chung | REVIEW (bỏ TTL, thêm LISTEN/NOTIFY và Read Replica) |
| r7 | A013 | pass | pass | fail strict / pass lenient ("Database có Read Replicas") | — | REVIEW sửa: "Read Replica không giúp ích nhiều" |
| r8 | A010 | fail | fail | fail (sticky in-memory + cache TTL 30 s–1 phút) | read replica cho việc kiểm tra session, nói rõ | REVIEW (thay cơ chế hỏng này bằng cơ chế hỏng khác) |
| r9 | A007 | pass | pass | pass | — | — |
| r10 | A012 | fail | fail | fail (sticky sessions) | sticky session trên RAM, không có điểm thu hồi chung | DRAFT |
| r11 | A004 | fail | fail | **pass** (LISTEN/NOTIFY, xóa trong mili-giây) | thêm "hoặc polling ngắn" mà vẫn nói thu hồi tức thời | REVIEW |
| r12 | A006 | partial | partial | fail (cache TTL 30–60 s là phương án chính) | (partial) nhánh phụ cache TTL có nói giá | REVIEW sửa thành nhánh giữ ràng buộc + nhánh phụ có nói giá |
| r13 | A016 | pass | pass | pass | — | — |
| r14 | A001 | fail | fail | fail (hybrid cache 30–60 s là phương án chính) | local cache là phương án chính | DRAFT |
| r15 | A015 | fail | fail | fail (cache TTL ~30 s là phương án chính) | read replica cho việc đọc session, nói rõ | REVIEW (bỏ cache, thêm replica) |
| r16 | A008 | pass | pass | pass | — | — |

Mọi run: đủ 3/3 lượt, 1 lần chạy (`attempts: 1`), 0 lần thử lại trong chat, 0 timeout, 0 lỗi kết nối. Một lần lượt phản biện trả về rỗng và chat dùng bản nháp (r7, **lượt 2**; lượt 3 được chấm bình thường và pass). Thời gian chạy từng run: **không có** (xem INDEX: `summary.json` chỉ được ghi ở cuối, lần chạy bị dừng ở r17).

### Tổng hợp

| | strict | lenient |
|---|---|---|
| câu trả lời cuối: pass / partial / fail | 4 / 1 / 11 | 6 / 2 / 8 |
| pass + partial (RUBRIC: partial tính là pass) | 5/16 = 31% (Wilson 95%: 14–56%) | 8/16 = 50% (28–72%) |
| bản nháp lượt 3 pass | 4/16 | 7/16 |

Chuyển trạng thái bản nháp → câu trả lời cuối (strict): pass → pass 3 (r9, r13, r16); pass → fail 1 (r11); fail → pass/partial 2 (r7, r12); fail → fail 10.

11 câu fail theo nơi sinh ra cơ chế hỏng: 7 có sẵn trong bản nháp (r1, r2, r3, r4, r5, r10, r14), 4 do lượt phản biện đưa vào (r6, r8, r11, r15; trong đó r6, r8, r15 bản nháp cũng đã fail bằng một cơ chế khác).

11 câu fail theo cơ chế: read replica nói rõ cho việc đọc session 3 (r5, r8, r15); read replica chung chung 3 (r1, r3, r6); local cache TTL là phương án chính 2 (r4, r14); JWT + cache `token_version` 1 (r2); đồng bộ bằng polling 1 (r11); sticky session 1 (r10).

### Phân loại lỗi

| Loại | Số câu | Ghi chú |
|---|---|---|
| HARNESS / PARSER | 0 | phiếu sinh lại bằng parser đã sửa trùng từng byte |
| INFRASTRUCTURE / NETWORK / TIMEOUT / RETRY | 0 | 0 thử lại, 0 timeout, 0 lỗi kết nối trong cả 16 run |
| PLANNER / RECONSTRUCTION / CLASSIFICATION | không áp dụng | repo không có các thành phần này (pipeline: nháp → phản biện) |
| MODEL_CAPABILITY / CURRENT_CONFIGURATION_LIMITATION | 11 | thiết kế sai về thu hồi tức thì; 7/11 có sẵn trong bản nháp, 4/11 do lượt phản biện (cùng model) đưa vào |
| RUBRIC (độ nhạy, không phải nguyên nhân) | 3 trong 11 | r1, r3, r6 đổi kết quả theo cách đọc G6 |
| UNKNOWN | 0 | |

Kết luận đo: với cấu hình baseline, T09 lượt 3 đạt 5/16 (strict, pass + partial). Lỗi là lỗi thiết kế kỹ thuật của model (thu hồi tức thì khi scale mà không có Redis), xuất hiện ngay từ bản nháp ở 12/16 run; lượt phản biện sửa được 2 và làm hỏng 1, nên gần như không đổi tỷ lệ. Không có dấu hiệu lỗi harness, mạng hay timeout. Kết quả này **chưa đủ n = 20**: còn r17–r20.
