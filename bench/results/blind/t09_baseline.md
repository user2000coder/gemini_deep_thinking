# Blind sheet t09_baseline: case T09, 16 answers

## A001

Chọn **Database kết hợp Local Cache ngắn tại App (Hybrid)**, nhưng cần lưu ý điều kiện quyết định:

- **Giải pháp:** Dùng Database làm nguồn dữ liệu chuẩn (Single Source of Truth) để đảm bảo thu hồi tức thời, kết hợp cache session trong RAM app với thời gian rất ngắn (vài giây) nhằm giảm tải trực tiếp cho Database khi lượng truy cập tăng 10 lần.
- **Giả định ngầm & Rủi ro:** Do không có Redis để làm Pub/Sub đồng bộ cache giữa các server, việc cache ở RAM sẽ tạo ra độ trễ nhỏ (vài giây) trước khi lệnh logout ở server này được cập nhật sang các server khác. 
- **Nếu bắt buộc thu hồi tức thời tuyệt đối (0 giây độ trễ ở mọi server):** Phải chọn **Database thuần túy** và scale trực tiếp hạ tầng Database (tăng cường Index, Read Replica, Connection Pooling). Các phương án lưu RAM thuần túy (In-Memory) không thể scale khi tải tăng 10x trên nhiều instance mà không có Redis hỗ trợ đồng bộ.

## A002

Vẫn là **Database kết hợp Local Cache (TTL ngắn, khoảng 5-10 giây)**, nhưng cần lưu ý một đánh đổi cốt lõi về thời gian thu hồi:

- **Cách hoạt động:** Local cache trên từng server giúp giảm 90% lượng request đập thẳng vào Database khi tải tăng 10x.
- **Giả định ngầm & Đánh đổi quan trọng:** 
  Vì không có Redis để đồng bộ trạng thái giữa các server, Local Cache sẽ tạo ra độ trễ. Khi bạn bấm thu hồi session, session đó vẫn có thể tồn tại trên RAM của các server khác trong vòng 5-10 giây (theo thời gian TTL của cache).
- **Nếu yêu cầu thu hồi tức thì tuyệt đối (0 giây độ trễ):** 
  Bạn **không được dùng Local Cache**. Giải pháp duy nhất là scale trực tiếp Database chính (bổ sung Read Replicas, connection pooling, tối ưu index) để chịu tải 10x, chấp nhận I/O cao để đảm bảo mọi request đều check thẳng vào DB và bị chặn ngay lập tức.

## A003

Chọn **Database tối ưu hạ tầng (Read Replica + Connection Pooling)** kết hợp **Local Cache có cơ chế đồng bộ tức thì (như DB LISTEN/NOTIFY)**.

* **Lý do & Xử lý ràng buộc:**
  * Tải 10x khiến Database thuần dễ nghẽn I/O. Nếu dùng Local Cache với TTL thông thường (30-60 giây) sẽ **vi phạm yêu cầu thu hồi ngay lập tức** đã đặt ra ở bước trước.
  * Giải pháp: Vẫn dùng Local Cache để gánh tải, nhưng bắt buộc phải gắn thêm cơ chế thông báo sự kiện (ví dụ: PostgreSQL `LISTEN/NOTIFY` hoặc message broker) để **xóa cache ngay lập tức** trên tất cả app server khi có lệnh thu hồi session.
* **Phương án thay thế tối ưu:** Chuyển sang **Memcached** (nếu lệnh cấm của công ty chỉ áp dụng riêng cho Redis do vấn đề bản quyền/SSPL).

## A004

Phương án scale tốt nhất không dùng Redis: **Database quan hệ kết hợp Local Memory Cache (đồng bộ qua Postgres LISTEN/NOTIFY hoặc polling ngắn)**.

* **Lý do:** Giảm tải đọc cho Database chính (app đọc trực tiếp từ RAM), nhưng vẫn giữ được cơ chế thu hồi (revoke) tức thời khi có tín hiệu đồng bộ.
* **Giả định ngầm & Rủi ro:** Giải pháp này giả định hệ thống có năng lực kỹ thuật để duy trì kết nối pub/sub ổn định giữa các app server và Database.
* *Nếu giả định sai (không muốn code thêm cơ chế đồng bộ phức tạp):* Chuyển về **Database quan hệ thuần túy có tối ưu Index (`session_id`) kèm connection pooler (như PgBouncer)** để đơn giản hóa kiến trúc, chấp nhận việc Database phải chịu tải I/O lớn hơn.

## A005

**Database-backed Sessions (tối ưu bằng Read Replicas & Index)**.

**Lý do:**
* Đáp ứng trọn vẹn ràng buộc **thu hồi tức thời** và **không dùng Redis**.
* Để scale 10x mà không làm sập DB chính: Định tuyến các request đọc/kiểm tra session sang **Read Replicas**, đồng thời đánh Index tối ưu trên trường token/session ID. 

*(Lưu ý về phương án JWT + Blacklist: Không phù hợp khi không có Redis, vì việc tra cứu bảng blacklist trên DB cho mỗi request vẫn gây tải tương đương Database session truyền thống, còn nếu dùng local cache để giảm tải thì sẽ làm mất tính "tức thời" của việc thu hồi do độ trễ đồng bộ).*

## A006

Tùy thuộc vào việc bạn có giữ cứng ràng buộc "thu hồi tức thì tuyệt đối" hay không:

**1. Nếu giữ cứng ràng buộc thu hồi tức thì:**
* **Phương án:** **Database thuần túy (tối ưu Index trên cột `session_id` và dùng Connection Pool như PgBouncer).**
* **Lý do:** 10x tải hoàn toàn nằm trong khả năng của RDBMS (như PostgreSQL/MySQL) nếu được đánh index chuẩn và quản lý kết nối tốt. Đây là phương án duy nhất scale được mà vẫn giữ được tính tức thì, không vi phạm quy chế cấm Redis.

**2. Nếu chấp nhận đánh đổi (Trễ thu hồi 30-60 giây để giảm tải DB):**
* **Phương án:** **Database kết hợp Local In-Memory Cache (TTL ngắn).**
* **Lý do:** Local cache giúp chặn phần lớn request gọi vào DB, nhưng đánh đổi bằng việc user vừa logout có thể vẫn thao tác được thêm tối đa 30-60 giây trên các server khác. 

*Giả định ngầm:* 10x tải của bạn vẫn nằm trong giới hạn mà Database có hạ tầng chịu tải được (chưa đạt mức hàng triệu QPS). Nếu tải quá lớn đến mức DB sập, việc cấm Redis sẽ buộc bạn phải thiết kế lại cơ chế auth (ví dụ chuyển sang token có kiểm soát phụ).

## A007

Vẫn là **Database Session Store**.

* **Lý do:** Đây là phương án duy nhất vừa đáp ứng được yêu cầu thu hồi session tức thì, vừa cho phép scale ngang app server mà không cần Redis. Phương án In-Memory vẫn bị loại vì không thể đồng bộ trạng thái thu hồi giữa các server khi tăng quy mô.
* **Giả định ngầm & Rủi ro khi tải tăng 10x:** Kết luận này giả định rằng cơ sở dữ liệu hiện tại có khả năng chịu tải I/O tăng đột biến (vì mỗi request đều phải truy vấn session). 
* **Nếu giả định sai (Database bị nghẽn I/O):** Bạn buộc phải tách bảng session ra một Database riêng (hoặc dùng một NoSQL lưu trữ khác công ty cho phép thay thế Redis như DynamoDB/MongoDB) và tối ưu Index trên cột `session_id`, thay vì dồn toàn bộ tải vào database chính của ứng dụng.

## A008

Chọn **Managed NoSQL (DynamoDB / MongoDB)**.

*   **Lý do:** Hỗ trợ scale ngang tốt, thao tác tra cứu và xóa theo khóa chính (O(1)) với throughput cao, cách ly hoàn toàn tải session khỏi database quan hệ chính.
*   **Giả định ngầm cần lưu ý:** Kết luận này đúng nếu database quan hệ hiện tại không đủ tài nguyên dư để gánh thêm 10x lượt đọc/ghi. Nếu database quan hệ hiện tại còn rất nhiều dư địa và hệ thống có dùng connection pooler (như PgBouncer), bạn hoàn toàn có thể tiếp tục chọn **Database quan hệ** (với điều kiện index kỹ `session_id`) để tránh phải vận hành thêm hạ tầng mới.

## A009

Tùy thuộc vào chính sách hạ tầng của công ty:

1. **Nếu được dùng cache server ngoài:** **Memcached** scale tốt nhất. Do lưu hoàn toàn trên RAM và hỗ trợ phân tán (distributed caching), nó đáp ứng tốt lượng tải tăng 10x và cho phép thu hồi session tức thì bằng cách xóa key.
2. **Nếu bắt buộc dùng Database sẵn có:** **NoSQL phân tán** (như DynamoDB, MongoDB) hoặc **SQL có tối ưu index/replica** scale tốt hơn. 

*Giả định ngầm & Điều kiện đổi kết luận:* Câu trả lời trên giả định hệ thống được phép mở rộng hạ tầng (thêm node Memcached hoặc scale DB). Nếu công ty bắt buộc dùng duy nhất 1 database quan hệ (SQL monolith) hiện tại và cấm mọi cache ngoài, việc tải tăng 10x sẽ làm nghẽn IO/connection pool, khiến Database trở thành điểm nghẽn chí mạng bất kể có tối ưu thế nào.

## A010

Vẫn là **Database quan hệ (kết hợp tối ưu Read Replica và Connection Pooling)**.

**Lý do:** 
Yêu cầu **thu hồi ngay lập tức** mà không có Redis khiến phương án In-Memory bế tắc khi tải tăng 10x. Lý do là không thể đồng bộ trạng thái thu hồi giữa nhiều app server (nếu dùng cache TTL sẽ vi phạm độ trễ "ngay lập tức", còn nếu query DB liên tục thì mất nghĩa của In-Memory). 

Database quan hệ scale tốt hơn khi tăng tải nhờ kỹ thuật tách cụm đọc/ghi (Read Replica cho việc kiểm tra session trên mỗi request, Master cho việc ghi và thu hồi), vừa giữ được tính nhất quán dữ liệu, vừa đáp ứng chính xác ràng buộc thu hồi tức thì.

## A011

**JWT kết hợp Token Version lưu trong Database (hoặc DynamoDB).**

*Lý do:* Khác với JWT thuần túy (đã loại trước đó), phương án này dùng JWT để mang payload ở client giúp giảm tải I/O cho DB, nhưng vẫn giữ một trường `token_version` siêu nhẹ trong DB để đảm bảo thu hồi tức thì khi cần.

*Giả định ngầm quyết định:* Để scale 10x thành công, bạn **bắt buộc phải cache `token_version` ở RAM của app trong vài giây** hoặc dùng NoSQL (như DynamoDB). Nếu hệ thống dùng relational DB truyền thống và query trực tiếp mỗi request mà không cache, DB vẫn sẽ bị nghẽn khi tải tăng 10 lần.

## A012

Khi tải tăng 10x, phương án scale tốt nhất phụ thuộc vào chính sách in-memory cache của công ty:

1. **Memcached** (nếu chỉ cấm riêng Redis): **Scale tốt nhất**. Giữ được tốc độ của in-memory (tránh nghẽn I/O cho Database ở mức tải lớn) và hỗ trợ xóa/thu hồi session ngay lập tức qua lệnh `delete`.
2. **Sticky Sessions tại Load Balancer** (nếu cấm mọi In-Memory Cache): **Scale tạm ổn nhưng có hạn chế**. Lưu session trên RAM của app server, scale ngang bằng cách thêm server. Tuy nhiên, khi tải lớn dễ gặp rủi ro lệch tải (hotspot) và mất session nếu app server khởi động lại hoặc sập.

*(Assumption: Relational DB từ phương án trước sẽ bắt đầu quá tải I/O khi traffic tăng 10x, nên cần chuyển sang Memcached hoặc Sticky Sessions).*

## A013

1. **Nếu công ty chỉ cấm riêng Redis (cho phép cache khác):** Dùng **Memcached**. Đây là phương án scale tốt nhất về hiệu năng, giữ được tốc độ cao trên RAM và hỗ trợ thu hồi session tức thì.

2. **Nếu bắt buộc chỉ dùng Database hiện tại:** Dùng **Database kết hợp Connection Pooler (như PgBouncer)**.
* *Giả định & Lưu ý:* Thao tác ghi/cập nhật session diễn ra liên tục, do đó Read Replica không giúp ích nhiều cho việc ghi. Cần đảm bảo Master Database chịu được tải ghi tăng 10 lần, hoặc phân mảnh bảng session để tránh nghẽn.

## A014

Vẫn là **Database-backed (SQL)** (với điều kiện scale hạ tầng database).

**Lý do:**
Phương án In-Memory + Sticky Sessions không thể scale tốt ở mức tải 10x vì gây lệch tải (hot spot) ở một số server, mất session khi scale-in/out, và không thể đồng bộ việc hủy session tức thì giữa các server độc lập khi không có Redis. Database-backed là phương án duy nhất vừa đáp ứng yêu cầu thu hồi tức thì, vừa scale ngang được tầng ứng dụng.

**Giả định ngầm & Phương án dự phòng:**
*   **Giả định:** Database hiện tại có khả năng mở rộng (scale up/out, thêm Read Replicas, đánh Index tốt) để gánh thêm 10x lượng query session cho mỗi request.
*   **Nếu giả định này sai (Database bị nghẽn ở 10x tải):** Bắt buộc phải dùng mô hình lai (Hybrid): Vẫn dùng Database làm nguồn trung tâm để thu hồi tức thì, nhưng mỗi app server tự cache session trong RAM từ 3-5 giây. Khi đó, việc thu hồi session sẽ có độ trễ tối đa bằng thời gian cache, đổi lại bảo vệ được Database khỏi quá tải.

## A015

Chọn **Database (tối ưu với Read Replicas và Index)**.

* **Lý do:** Khi tải tăng 10x, bạn scale hệ thống Database theo chiều ngang (thêm Read Replicas cho các request đọc session) và đánh index cực tốt cho cột `session_id`. 
* **Lưu ý quan trọng về ràng buộc:** Tránh dùng Local Cache (In-Memory tại RAM server) kèm TTL như một số giải pháp thông thường, vì nếu có độ trễ TTL (ví dụ 30 giây), bạn sẽ **vi phạm ràng buộc thu hồi tức thì** (user bị logout vẫn tiếp tục truy cập được trong thời gian cache chưa hết hạn). Database vẫn là Source of Truth duy nhất đáp ứng được đồng thời bài toán scale và thu hồi real-time khi không có Redis.

## A016

**Cloud Key-Value (DynamoDB, Firestore)**.

* **Lý do:** Tốc độ O(1), scale ngang độc lập, không làm nghẽn Database chính khi tải tăng 10x, và vẫn đáp ứng hoàn hảo yêu cầu thu hồi session tức thì.
* **Giả định ngầm quan trọng:** Hệ thống phải chạy trên cloud hoặc được phép sử dụng dịch vụ managed ngoài. 
* *Nếu hệ thống là On-Premise hoàn toàn (không được dùng dịch vụ cloud):* Phương án scale tốt nhất đổi thành **Cluster/Sharded Database (tách bảng sessions ra một cụm DB riêng biệt)** để tránh nghẽn DB chính.
