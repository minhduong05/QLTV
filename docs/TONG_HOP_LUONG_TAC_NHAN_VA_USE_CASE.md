# Tổng hợp luồng nghiệp vụ theo tác nhân và use case

Tài liệu này mô tả toàn bộ luồng nghiệp vụ của hệ thống quản lý thư viện theo 3 tác nhân:

- Quản trị viên
- Thủ thư
- Bạn đọc

Đồng thời tài liệu cũng chỉ rõ luồng nào tương ứng với 5 use case trong báo cáo:

- UC001: Tìm kiếm sách
- UC002: Mượn sách
- UC003: Nhận trả sách
- UC004: Thêm sách
- UC005: Đăng ký thẻ đọc

## 1. Khái niệm dữ liệu chính

### 1.1. Tài khoản đăng nhập

Bảng chính: `users`

`users` lưu tài khoản đăng nhập hệ thống. Mỗi tài khoản có vai trò:

| Role | Ý nghĩa |
|---|---|
| `admin` | Quản trị viên |
| `librarian` | Thủ thư |
| `reader` | Bạn đọc |

Tài khoản bạn đọc mới đăng ký chỉ tạo dòng trong `users`. Tài khoản này chưa được mượn sách cho đến khi có thẻ đọc hợp lệ trong bảng `readers`.

### 1.2. Thẻ bạn đọc

Bảng chính: `readers`

`readers` là thẻ đọc thật của bạn đọc. Một bạn đọc muốn mượn sách phải có:

- `is_active = true`
- `expires_at` chưa quá hạn
- không vượt quá số sách đang mượn tối đa

Ví dụ thẻ đọc:

```text
card_number: DG-0005
full_name: Nguyễn Văn A
email: a@example.com
expires_at: 2027-06-25
is_active: true
balance: 0
```

### 1.3. Yêu cầu cấp thẻ đọc online

Bảng chính: `card_requests`

Khi bạn đọc tự đăng ký tài khoản ở nhà, họ chưa có thẻ đọc. Họ gửi yêu cầu cấp thẻ online. Thủ thư duyệt yêu cầu đó.

Trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| `pending` | Đang chờ thủ thư duyệt |
| `approved` | Đã duyệt, hệ thống đã tạo thẻ đọc |
| `rejected` | Bị từ chối, bạn đọc cần gửi lại thông tin |
| `cancelled` | Đã hủy |

### 1.4. Đầu sách và bản sao vật lý

Bảng chính:

- `book_titles`
- `book_copies`

`book_titles` là đầu sách, ví dụ “Clean Code”.

`book_copies` là từng cuốn vật lý cụ thể, có mã vạch riêng, ví dụ:

```text
IT-0101 - Clean Code
IT-0102 - Clean Code
```

Trạng thái bản sao:

| Trạng thái | Ý nghĩa |
|---|---|
| `available` | Đang sẵn sàng cho mượn |
| `reserved` | Đã được duyệt online và đang giữ chỗ, chờ bạn đọc đến lấy |
| `on_loan` | Đang được mượn thật |
| `lost` | Mất |
| `damaged` | Hỏng |
| `retired` | Ngừng phục vụ |

### 1.5. Phiếu đăng ký mượn online

Bảng chính:

- `borrow_tickets`
- `borrow_ticket_items`

`borrow_tickets` là phiếu bạn đọc gửi online để xin mượn sách. Phiếu này chưa phải phiếu mượn thật.

`borrow_ticket_items` là từng đầu sách trong phiếu đăng ký.

Trạng thái phiếu online:

| Trạng thái | Ý nghĩa |
|---|---|
| `pending_review` | Bạn đọc vừa gửi, chờ thủ thư kiểm tra |
| `changes_requested` | Một số sách hết bản sao, cần bạn đọc phản hồi |
| `approved_waiting_pickup` | Đã duyệt, sách đã giữ chỗ, chờ bạn đọc đến lấy |
| `borrowed` | Bạn đọc đã đến lấy, phiếu đã sinh phiếu mượn thật |
| `rejected` | Thủ thư từ chối |
| `cancelled` | Bạn đọc hủy |

### 1.6. Phiếu mượn thật

Bảng chính:

- `loans`
- `loan_items`

`loans` là phiếu mượn thật. Phiếu này chỉ được tạo khi bạn đọc đã đến thư viện lấy sách và thủ thư bấm xác nhận.

`loan_items` là từng cuốn vật lý trong phiếu mượn thật.

Ví dụ:

```text
loans
- id: 12
- reader_id: 5
- loaned_at: 2026-06-25 20:30
- due_at: 2026-07-09 20:30
- status: open

loan_items
- loan_id: 12
- book_copy_id: IT-0101
- returned_at: null
- fine_amount: 0
```

## 2. Luồng tổng quát ngoài đời

Luồng đầy đủ từ người mới đến lúc mượn và trả sách:

```text
Người mới đăng ký tài khoản
→ Gửi yêu cầu cấp thẻ đọc online
→ Thủ thư duyệt yêu cầu cấp thẻ
→ Hệ thống tạo thẻ đọc
→ Bạn đọc tra cứu sách
→ Bạn đọc lập phiếu đăng ký mượn online
→ Thủ thư kiểm tra bản sao vật lý
→ Nếu thiếu sách, bạn đọc sửa phiếu hoặc đồng ý mượn phần còn sẵn
→ Thủ thư/hệ thống giữ chỗ sách còn sẵn
→ Bạn đọc đến thư viện lấy sách
→ Thủ thư xác nhận đã lấy
→ Hệ thống tạo phiếu mượn thật
→ Bạn đọc trả sách
→ Thủ thư nhận trả
→ Hệ thống tính phạt nếu quá hạn
```

Điểm quan trọng:

- Duyệt online chưa phải mượn thật.
- Khi duyệt online, sách chỉ chuyển sang `reserved`.
- Hạn trả không tính từ lúc duyệt online.
- Hạn trả tính từ lúc thủ thư bấm **Xác nhận đã lấy**.
- Lúc đó hệ thống mới tạo `loans` và `loan_items`.

## 3. Luồng của quản trị viên

Quản trị viên có quyền cao nhất. Quản trị viên có thể làm nghiệp vụ của thủ thư và có thêm quyền quản lý hệ thống.

### 3.1. Đăng nhập hệ thống

Tác nhân: quản trị viên

Mục đích: vào hệ thống để quản lý.

Cách thực hiện:

1. Mở web tại `http://localhost:5173`.
2. Nhập email và mật khẩu.
3. Với dữ liệu mẫu:

```text
Email: admin@example.com
Mật khẩu: admin123
```

Backend xử lý:

- Frontend gọi `POST /api/auth/login`.
- Backend kiểm tra `users.email`.
- Backend kiểm tra mật khẩu đã hash.
- Nếu đúng, backend trả JWT token.

Bảng đọc:

- `users`

Kết quả:

- Quản trị viên vào được giao diện quản trị nội bộ.

Thuộc UC báo cáo: không.

### 3.2. Quản lý tài khoản

Tác nhân: quản trị viên

Mục đích: tạo, sửa, khóa tài khoản quản trị viên hoặc thủ thư.

Cách thực hiện:

1. Vào màn **Quản trị**.
2. Tạo tài khoản mới.
3. Chọn role:
   - `admin`
   - `librarian`
4. Lưu.

Backend xử lý:

- Ghi tài khoản vào `users`.
- Mật khẩu được hash trước khi lưu.
- Admin có thể khóa/mở tài khoản bằng `is_active`.

Bảng ghi:

- `users`

Kết quả hiển thị:

- Tài khoản mới xuất hiện trong danh sách người dùng.
- Người dùng đó có thể đăng nhập theo role được cấp.

Thuộc UC báo cáo: không.

### 3.3. Quản lý quy định hệ thống

Tác nhân: quản trị viên

Mục đích: thay đổi các quy định vận hành thư viện mà không sửa code.

Cách thực hiện:

1. Vào màn **Quản trị**.
2. Sửa các quy định như:
   - số ngày mượn
   - tiền phạt mỗi ngày
   - số sách tối đa được mượn
   - số lần gia hạn tối đa
   - hạn thẻ đọc
3. Lưu.

Bảng ghi:

- `system_settings`

Một số key quan trọng:

| Key | Ý nghĩa |
|---|---|
| `loan_days` | Số ngày được mượn sách |
| `fine_per_day` | Tiền phạt mỗi ngày quá hạn |
| `max_active_loans` | Số cuốn tối đa được mượn cùng lúc |
| `max_renewals` | Số lần gia hạn tối đa |
| `card_validity_months` | Thời hạn thẻ đọc tính theo tháng |

Kết quả:

- Các nghiệp vụ mượn, trả, gia hạn, cấp thẻ dùng quy định mới.

Thuộc UC báo cáo: không.

### 3.4. Tra cứu sách

Tác nhân: quản trị viên

Mục đích: tìm đầu sách, kiểm tra tồn kho.

Cách thực hiện:

1. Vào màn **Sách & kho**.
2. Nhập tên sách, ISBN hoặc tác giả.
3. Bấm tìm.

Backend xử lý:

- Frontend gọi `GET /api/catalog/books?search=...`.
- Backend tìm trong:
  - `book_titles.title`
  - `book_titles.isbn`
  - `authors.name`

Bảng đọc:

- `book_titles`
- `book_copies`
- `authors`
- `categories`
- `publishers`

Kết quả:

- Hiển thị danh sách đầu sách.
- Hiển thị số bản sao sẵn có.
- Hiển thị bản sao đang giữ chỗ hoặc đang mượn.

Thuộc UC báo cáo: UC001 - Tìm kiếm sách.

### 3.5. Thêm sách

Tác nhân: quản trị viên

Mục đích: thêm đầu sách mới và bản sao vật lý vào kho.

Cách thực hiện:

1. Vào màn **Sách & kho**.
2. Tạo thể loại nếu chưa có.
3. Tạo tác giả nếu chưa có.
4. Tạo nhà xuất bản nếu chưa có.
5. Tạo đầu sách:
   - tên sách
   - ISBN
   - năm xuất bản
   - mô tả
   - thể loại
   - tác giả
   - nhà xuất bản
6. Thêm bản sao vật lý:
   - mã vạch
   - vị trí kệ
   - ngày nhập
   - tình trạng

Bảng ghi:

- `categories`
- `authors`
- `publishers`
- `book_titles`
- `book_title_authors`
- `book_copies`

Kết quả:

- Đầu sách xuất hiện ở **Sách & kho**.
- Bạn đọc có thể thấy đầu sách ở **Cổng bạn đọc**.
- Nếu bản sao ở trạng thái `available`, bạn đọc có thể đưa đầu sách đó vào phiếu đăng ký mượn.

Thuộc UC báo cáo: UC004 - Thêm sách.

### 3.6. Duyệt yêu cầu cấp thẻ

Tác nhân: quản trị viên

Mục đích: duyệt yêu cầu cấp thẻ online của bạn đọc.

Cách thực hiện:

1. Vào màn **Bạn đọc và thu tiền**.
2. Xem khối **Yêu cầu cấp thẻ online**.
3. Kiểm tra thông tin:
   - họ tên
   - email
   - số điện thoại
   - ngày sinh
   - địa chỉ
4. Bấm **Duyệt cấp thẻ** hoặc **Từ chối**.

Nếu duyệt:

- Frontend gọi `POST /api/readers/card-requests/{id}/approve`.
- Backend sinh mã thẻ `DG-xxxx`.
- Backend ghi dòng mới vào `readers`.
- Backend cập nhật `card_requests.status = approved`.

Nếu từ chối:

- Frontend gọi `POST /api/readers/card-requests/{id}/reject`.
- Backend cập nhật `card_requests.status = rejected`.
- Backend ghi lý do từ chối.

Bảng đọc/ghi:

- `card_requests`
- `readers`
- `system_settings`

Kết quả:

- Nếu duyệt, bạn đọc có thẻ đọc và được lập phiếu đăng ký mượn.
- Nếu từ chối, bạn đọc thấy trạng thái bị từ chối và có thể gửi lại.

Thuộc UC báo cáo: UC005 - Đăng ký thẻ đọc.

### 3.7. Xử lý mượn/trả

Tác nhân: quản trị viên

Mục đích: xử lý các phiếu mượn như thủ thư.

Quản trị viên có thể:

- kiểm tra phiếu đăng ký mượn online
- duyệt phần sách còn sẵn
- xác nhận bạn đọc đến lấy sách
- lập phiếu mượn trực tiếp
- nhận trả sách
- gia hạn phiếu

Bảng liên quan:

- `borrow_tickets`
- `borrow_ticket_items`
- `book_copies`
- `loans`
- `loan_items`
- `readers`

Thuộc UC báo cáo:

- UC002 - Mượn sách
- UC003 - Nhận trả sách

### 3.8. Nhập sách

Tác nhân: quản trị viên

Mục đích: ghi nhận sách nhập từ nhà cung cấp.

Cách thực hiện:

1. Vào màn **Nhập sách**.
2. Tạo nhà cung cấp nếu chưa có.
3. Tạo phiếu nhập.
4. Chọn đầu sách.
5. Nhập số lượng, đơn giá, vị trí kệ.
6. Lưu phiếu.

Bảng ghi:

- `suppliers`
- `acquisitions`
- `acquisition_items`
- `book_copies`

Kết quả:

- Hệ thống ghi phiếu nhập.
- Hệ thống tạo thêm bản sao vật lý tương ứng.
- Số lượng sách sẵn có tăng lên.

Thuộc UC báo cáo: mở rộng UC004 - Thêm sách.

### 3.9. Thu tiền phạt

Tác nhân: quản trị viên

Mục đích: ghi nhận bạn đọc thanh toán công nợ do trả sách quá hạn.

Cách thực hiện:

1. Vào màn **Bạn đọc và thu tiền**.
2. Chọn bạn đọc có công nợ.
3. Nhập số tiền thu.
4. Lưu phiếu thu.

Bảng ghi:

- `payments`
- `readers.balance`

Kết quả:

- Công nợ của bạn đọc giảm.
- Có chứng từ thu tiền trong `payments`.

Thuộc UC báo cáo: không.

### 3.10. Xem báo cáo

Tác nhân: quản trị viên

Mục đích: theo dõi tình hình hoạt động thư viện.

Cách thực hiện:

1. Vào màn **Báo cáo**.
2. Xem:
   - sách quá hạn
   - sách được mượn nhiều
   - lượt mượn theo thể loại
   - công nợ

Bảng đọc:

- `loans`
- `loan_items`
- `book_copies`
- `book_titles`
- `categories`
- `readers`

Kết quả:

- Có số liệu phục vụ quản lý.

Thuộc UC báo cáo: không.

## 4. Luồng của thủ thư

Thủ thư là người vận hành thư viện hằng ngày.

### 4.1. Đăng nhập

Tác nhân: thủ thư

Mục đích: vào hệ thống để xử lý nghiệp vụ.

Cách thực hiện:

1. Quản trị viên tạo tài khoản thủ thư ở màn **Quản trị**.
2. Thủ thư đăng nhập bằng email/mật khẩu được cấp.

Bảng đọc:

- `users`

Kết quả:

- Thủ thư vào được các màn nghiệp vụ.
- Thủ thư không có quyền quản trị tài khoản/quy định nếu hệ thống phân quyền chặt.

Thuộc UC báo cáo: không.

### 4.2. Tra cứu sách

Tác nhân: thủ thư

Cách thực hiện:

1. Vào màn **Sách & kho**.
2. Nhập từ khóa.
3. Xem đầu sách và bản sao.

Dữ liệu:

- Đọc `book_titles`, `book_copies`, `authors`, `categories`, `publishers`.

Thuộc UC báo cáo: UC001 - Tìm kiếm sách.

### 4.3. Thêm đầu sách và bản sao

Tác nhân: thủ thư

Cách thực hiện:

1. Vào màn **Sách & kho**.
2. Tạo danh mục liên quan nếu cần.
3. Tạo đầu sách.
4. Thêm mã vạch từng cuốn vật lý.

Bảng ghi:

- `book_titles`
- `book_copies`
- `authors`
- `categories`
- `publishers`

Kết quả:

- Sách có thể được tìm kiếm.
- Bản sao `available` có thể được mượn.

Thuộc UC báo cáo: UC004 - Thêm sách.

### 4.4. Nhập sách từ nhà cung cấp

Tác nhân: thủ thư

Cách thực hiện:

1. Vào màn **Nhập sách**.
2. Chọn hoặc tạo nhà cung cấp.
3. Chọn đầu sách.
4. Nhập số lượng.
5. Lưu phiếu nhập.

Bảng ghi:

- `suppliers`
- `acquisitions`
- `acquisition_items`
- `book_copies`

Kết quả:

- Kho tăng số bản sao.
- Có lịch sử phiếu nhập.

Thuộc UC báo cáo: mở rộng UC004 - Thêm sách.

### 4.5. Duyệt yêu cầu cấp thẻ online

Tác nhân: thủ thư

Mục đích: duyệt hồ sơ bạn đọc gửi online.

Cách thực hiện:

1. Vào **Bạn đọc và thu tiền**.
2. Xem danh sách yêu cầu cấp thẻ.
3. Nếu hợp lệ, bấm **Duyệt cấp thẻ**.
4. Nếu chưa hợp lệ, bấm **Từ chối**.

Khi duyệt:

- Hệ thống tạo mã thẻ `DG-xxxx`.
- Hệ thống tạo dòng `readers`.
- Yêu cầu chuyển `approved`.

Khi từ chối:

- Yêu cầu chuyển `rejected`.
- Bạn đọc thấy lý do từ chối.

Bảng ghi:

- `card_requests`
- `readers`

Thuộc UC báo cáo: UC005 - Đăng ký thẻ đọc.

### 4.6. Tạo thẻ tại quầy

Tác nhân: thủ thư

Mục đích: tạo thẻ cho bạn đọc khi họ đến trực tiếp thư viện.

Cách thực hiện:

1. Vào **Bạn đọc và thu tiền**.
2. Nhập:
   - mã thẻ
   - họ tên
   - email
   - số điện thoại
   - loại bạn đọc
   - hạn thẻ
3. Bấm lưu.

Bảng ghi:

- `readers`

Kết quả:

- Bạn đọc có thẻ và có thể mượn sách.

Thuộc UC báo cáo: UC005 - Đăng ký thẻ đọc.

### 4.7. Kiểm tra phiếu đăng ký mượn online

Tác nhân: thủ thư

Mục đích: kiểm tra phiếu bạn đọc gửi online.

Cách thực hiện:

1. Vào **Mượn, trả và gia hạn**.
2. Tại khối **Phiếu đăng ký mượn online**, xem các phiếu `pending_review`.
3. Bấm **Kiểm tra**.

Backend xử lý:

- Frontend gọi `POST /api/loans/tickets/{id}/review`.
- Backend kiểm tra từng đầu sách còn bản sao `available` không.

Nếu tất cả còn bản sao:

- Backend chọn bản sao vật lý.
- Đổi `book_copies.status` sang `reserved`.
- Đổi phiếu sang `approved_waiting_pickup`.

Nếu có sách hết bản sao:

- Backend đánh dấu dòng đó là `unavailable`.
- Ghi lý do thiếu bản sao.
- Đổi phiếu sang `changes_requested`.

Bảng đọc/ghi:

- `borrow_tickets`
- `borrow_ticket_items`
- `book_copies`

Kết quả:

- Bạn đọc thấy sách nào còn, sách nào hết.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 4.8. Duyệt phần sách còn sẵn

Tác nhân: thủ thư

Mục đích: trong trường hợp phiếu thiếu một số sách, vẫn duyệt các sách còn bản sao.

Cách thực hiện:

1. Ở màn **Mượn, trả và gia hạn**.
2. Chọn phiếu đang chờ xử lý hoặc đang chờ bạn đọc phản hồi.
3. Bấm **Duyệt phần có sẵn**.

Backend xử lý:

- Frontend gọi `POST /api/loans/tickets/{id}/approve-available`.
- Backend giữ chỗ các bản sao còn sẵn.
- Dòng hết sách chuyển `skipped`.
- Phiếu chuyển `approved_waiting_pickup`.

Bảng ghi:

- `borrow_tickets`
- `borrow_ticket_items`
- `book_copies`

Kết quả:

- Các sách còn bản sao được giữ chỗ.
- Bạn đọc có thể đến lấy phần đã duyệt.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 4.9. Xác nhận bạn đọc đến lấy sách

Tác nhân: thủ thư

Mục đích: chuyển phiếu online đã duyệt thành phiếu mượn thật.

Cách thực hiện:

1. Bạn đọc đến thư viện.
2. Thủ thư mở phiếu trạng thái `approved_waiting_pickup`.
3. Thủ thư bấm **Xác nhận đã lấy**.

Backend xử lý:

- Frontend gọi `POST /api/loans/tickets/{id}/pickup`.
- Backend tạo `loans`.
- Backend tạo `loan_items`.
- Backend đổi bản sao từ `reserved` sang `on_loan`.
- Backend tính hạn trả:

```text
due_at = loaned_at + loan_days
```

Trong đó `loaned_at` là thời điểm thủ thư bấm xác nhận đã lấy.

Bảng ghi:

- `loans`
- `loan_items`
- `borrow_tickets`
- `book_copies`

Kết quả:

- Bạn đọc chính thức đang mượn sách.
- Sách xuất hiện ở khối **Sách đang mượn**.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 4.10. Lập phiếu mượn trực tiếp tại quầy

Tác nhân: thủ thư

Mục đích: cho bạn đọc mượn ngay tại thư viện, không qua phiếu online.

Cách thực hiện:

1. Vào **Mượn, trả và gia hạn**.
2. Chọn bạn đọc.
3. Chọn một hoặc nhiều bản sao vật lý đang `available`.
4. Bấm **Xác nhận mượn**.

Backend xử lý:

- Frontend gọi `POST /api/loans/checkout`.
- Backend kiểm tra:
  - thẻ còn hạn
  - thẻ đang hoạt động
  - sách đang `available`
  - chưa vượt số sách tối đa
- Backend tạo `loans`, `loan_items`.
- Backend đổi sách sang `on_loan`.

Bảng ghi:

- `loans`
- `loan_items`
- `book_copies`

Thuộc UC báo cáo: UC002 - Mượn sách.

### 4.11. Nhận trả sách

Tác nhân: thủ thư

Mục đích: ghi nhận bạn đọc trả sách.

Cách thực hiện:

1. Vào **Mượn, trả và gia hạn**.
2. Mở phiếu mượn đang mở.
3. Với từng cuốn, bấm **Nhận trả**.

Backend xử lý:

- Frontend gọi `POST /api/loans/{loan_id}/items/{item_id}/return`.
- Backend ghi `returned_at`.
- Backend tính phạt nếu quá hạn.
- Backend đổi `book_copies.status` về `available`.
- Nếu mọi cuốn đã trả, đổi `loans.status = completed`.

Bảng ghi:

- `loan_items`
- `book_copies`
- `readers`
- `loans`

Thuộc UC báo cáo: UC003 - Nhận trả sách.

### 4.12. Tính phạt quá hạn

Tác nhân: hệ thống, do thủ thư kích hoạt khi nhận trả

Công thức:

```text
số ngày quá hạn = ngày trả thực tế - ngày hẹn trả
tiền phạt = số ngày quá hạn * fine_per_day
```

Nếu trả đúng hạn hoặc trước hạn:

```text
số ngày quá hạn = 0
tiền phạt = 0
```

Ví dụ:

```text
Hạn trả: 2026-07-09
Ngày trả: 2026-07-12
Quá hạn: 3 ngày
fine_per_day: 5000
Tiền phạt: 3 * 5000 = 15000 đồng
```

Bảng ghi:

- `loan_items.fine_amount`
- `readers.balance`

Kết quả:

- Tiền phạt được cộng vào công nợ bạn đọc.

Thuộc UC báo cáo: UC003 - Nhận trả sách.

### 4.13. Gia hạn phiếu mượn

Tác nhân: thủ thư

Mục đích: kéo dài hạn trả cho phiếu đang mượn.

Cách thực hiện:

1. Vào **Mượn, trả và gia hạn**.
2. Chọn phiếu đang mở.
3. Bấm **Gia hạn**.

Backend kiểm tra:

- Phiếu phải đang `open`.
- Phiếu chưa quá hạn.
- Chưa vượt số lần gia hạn tối đa.

Bảng ghi:

- `loans.due_at`
- `loans.renewal_count`

Kết quả:

- Hạn trả được cộng thêm `loan_days`.

Thuộc UC báo cáo: không.

### 4.14. Thu tiền phạt

Tác nhân: thủ thư

Cách thực hiện:

1. Vào **Bạn đọc và thu tiền**.
2. Chọn bạn đọc có công nợ.
3. Nhập số tiền thu.
4. Bấm **Lập phiếu thu**.

Bảng ghi:

- `payments`
- `readers.balance`

Kết quả:

- Công nợ giảm.
- Hệ thống lưu chứng từ thu tiền.

Thuộc UC báo cáo: không.

### 4.15. Xem báo cáo

Tác nhân: thủ thư

Cách thực hiện:

1. Vào **Báo cáo**.
2. Xem:
   - sách quá hạn
   - sách được mượn nhiều
   - lượt mượn theo thể loại

Bảng đọc:

- `loans`
- `loan_items`
- `book_copies`
- `book_titles`
- `categories`
- `readers`

Thuộc UC báo cáo: không.

## 5. Luồng của bạn đọc

Bạn đọc là người dùng bên ngoài sử dụng cổng bạn đọc.

### 5.1. Đăng ký tài khoản

Tác nhân: bạn đọc

Mục đích: có tài khoản để đăng nhập vào cổng bạn đọc.

Cách thực hiện:

1. Mở web.
2. Chọn **Đăng ký bạn đọc mới**.
3. Nhập:
   - họ tên
   - email
   - mật khẩu
4. Gửi đăng ký.

Backend xử lý:

- Frontend gọi `POST /api/auth/register-reader`.
- Backend tạo dòng `users` với role `reader`.

Bảng ghi:

- `users`

Kết quả:

- Bạn đọc có tài khoản đăng nhập.
- Bạn đọc chưa có thẻ đọc.
- Bạn đọc chưa được mượn sách.

Thuộc UC báo cáo: bước chuẩn bị cho UC005.

### 5.2. Gửi yêu cầu cấp thẻ đọc

Tác nhân: bạn đọc

Mục đích: xin cấp thẻ đọc online để được mượn sách.

Cách thực hiện:

1. Đăng nhập bằng tài khoản bạn đọc.
2. Nếu chưa có thẻ, cổng bạn đọc hiển thị form cấp thẻ.
3. Nhập:
   - số điện thoại
   - ngày sinh
   - địa chỉ
4. Bấm gửi yêu cầu.

Backend xử lý:

- Frontend gọi `POST /api/readers/me/card-request`.
- Backend ghi `card_requests.status = pending`.

Bảng ghi:

- `card_requests`

Kết quả:

- Bạn đọc thấy trạng thái **Chờ thủ thư duyệt**.
- Bạn đọc vẫn chưa thể mượn sách cho đến khi thẻ được duyệt.

Thuộc UC báo cáo: UC005 - Đăng ký thẻ đọc.

### 5.3. Theo dõi trạng thái thẻ

Tác nhân: bạn đọc

Cách thực hiện:

1. Đăng nhập vào cổng bạn đọc.
2. Xem khối thông tin thẻ.

Các trường hợp:

| Trạng thái | Ý nghĩa |
|---|---|
| Chưa có thẻ | Cần gửi yêu cầu cấp thẻ |
| Chờ thủ thư duyệt | Đã gửi yêu cầu, đang chờ duyệt |
| Đã duyệt | Có mã thẻ và có thể mượn sách nếu thẻ còn hạn |
| Từ chối | Cần kiểm tra lý do và gửi lại |
| Hết hạn/bị khóa | Không được lập phiếu mượn |

Bảng đọc:

- `readers`
- `card_requests`

Thuộc UC báo cáo: UC005 - Đăng ký thẻ đọc.

### 5.4. Tra cứu sách

Tác nhân: bạn đọc

Mục đích: tìm sách muốn mượn.

Cách thực hiện:

1. Vào **Cổng bạn đọc**.
2. Nhập tên sách, ISBN hoặc tác giả.
3. Bấm tìm.

Backend xử lý:

- Frontend gọi `GET /api/catalog/books?search=...`.

Bảng đọc:

- `book_titles`
- `book_copies`
- `authors`
- `categories`
- `publishers`

Kết quả:

- Bạn đọc thấy sách và số bản sao sẵn có.

Thuộc UC báo cáo: UC001 - Tìm kiếm sách.

### 5.5. Lập phiếu đăng ký mượn online

Tác nhân: bạn đọc

Điều kiện:

- Có thẻ đọc.
- Thẻ còn hạn.
- Thẻ đang hoạt động.

Cách thực hiện:

1. Vào **Cổng bạn đọc**.
2. Tích chọn các đầu sách muốn mượn.
3. Nhập ghi chú nếu cần.
4. Bấm **Gửi phiếu đăng ký mượn**.

Backend xử lý:

- Frontend gọi `POST /api/loans/tickets`.
- Backend tạo `borrow_tickets.status = pending_review`.
- Backend tạo các dòng `borrow_ticket_items`.

Bảng ghi:

- `borrow_tickets`
- `borrow_ticket_items`

Kết quả:

- Phiếu xuất hiện trong danh sách phiếu của bạn đọc.
- Thủ thư thấy phiếu ở màn **Mượn, trả và gia hạn**.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 5.6. Xem phản hồi khi thiếu sách

Tác nhân: bạn đọc

Mục đích: biết sách nào còn bản sao, sách nào hết.

Khi xảy ra:

- Thủ thư kiểm tra phiếu.
- Nếu có sách hết bản sao, phiếu chuyển `changes_requested`.

Cách thực hiện:

1. Bạn đọc mở cổng bạn đọc.
2. Xem phiếu trạng thái **Cần bạn đọc phản hồi**.
3. Xem từng dòng sách:
   - `available`: còn bản sao
   - `unavailable`: hết bản sao
   - `reserved`: đã giữ chỗ
   - `skipped`: không mượn

Bảng đọc:

- `borrow_tickets`
- `borrow_ticket_items`

Thuộc UC báo cáo: UC002 - Mượn sách.

### 5.7. Sửa phiếu và gửi lại

Tác nhân: bạn đọc

Mục đích: thay đổi danh sách sách muốn mượn sau khi thủ thư báo thiếu bản sao.

Cách thực hiện:

1. Tại phiếu `changes_requested`, bấm **Sửa phiếu**.
2. Bỏ sách hết bản sao hoặc chọn sách khác.
3. Bấm gửi lại.

Backend xử lý:

- Frontend gọi `PUT /api/loans/tickets/{id}`.
- Backend xóa danh sách item cũ.
- Backend tạo lại `borrow_ticket_items`.
- Backend đưa phiếu về `pending_review`.

Bảng ghi:

- `borrow_tickets`
- `borrow_ticket_items`

Kết quả:

- Thủ thư kiểm tra lại phiếu mới.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 5.8. Đồng ý mượn phần còn sẵn

Tác nhân: bạn đọc

Mục đích: không sửa phiếu nữa, chấp nhận mượn những sách còn bản sao.

Cách thực hiện:

1. Tại phiếu `changes_requested`, bấm **Mượn phần còn sẵn**.

Backend xử lý:

- Frontend gọi `POST /api/loans/tickets/{id}/approve-available`.
- Backend giữ chỗ sách còn bản sao.
- Sách thiếu chuyển `skipped`.
- Phiếu chuyển `approved_waiting_pickup`.

Bảng ghi:

- `borrow_tickets`
- `borrow_ticket_items`
- `book_copies`

Kết quả:

- Những sách còn bản sao được giữ chỗ.
- Bạn đọc đến thư viện lấy phần đã duyệt.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 5.9. Đến thư viện lấy sách

Tác nhân: bạn đọc và thủ thư

Mục đích: nhận sách vật lý.

Cách thực hiện ngoài đời:

1. Bạn đọc đến thư viện.
2. Bạn đọc cung cấp mã thẻ hoặc thông tin tài khoản.
3. Thủ thư mở phiếu đã duyệt.
4. Thủ thư lấy sách đã giữ chỗ.
5. Thủ thư bấm **Xác nhận đã lấy**.

Backend xử lý:

- Tạo `loans`.
- Tạo `loan_items`.
- Đổi `book_copies.status` từ `reserved` sang `on_loan`.
- Tính hạn trả từ thời điểm xác nhận lấy sách.

Thuộc UC báo cáo: UC002 - Mượn sách.

### 5.10. Xem sách đang mượn

Tác nhân: bạn đọc

Cách thực hiện:

1. Đăng nhập cổng bạn đọc.
2. Xem khối **Sách đang mượn**.

Bảng đọc:

- `loans`
- `loan_items`
- `book_copies`

Kết quả:

- Bạn đọc biết đang mượn cuốn nào và hạn trả.

Thuộc UC báo cáo: không.

### 5.11. Xem lịch sử và công nợ

Tác nhân: bạn đọc

Cách thực hiện:

1. Đăng nhập cổng bạn đọc.
2. Xem:
   - lịch sử phiếu
   - sách đang mượn
   - công nợ

Bảng đọc:

- `loans`
- `loan_items`
- `readers.balance`
- `payments`

Thuộc UC báo cáo: không.

## 6. Mapping 5 UC trong báo cáo

| UC | Tên use case | Tác nhân chính | Màn hình thực hiện | API chính | Bảng chính |
|---|---|---|---|---|---|
| UC001 | Tìm kiếm sách | Bạn đọc, thủ thư, quản trị viên | Cổng bạn đọc, Sách & kho | `GET /api/catalog/books` | `book_titles`, `book_copies`, `authors` |
| UC002 | Mượn sách | Bạn đọc, thủ thư | Cổng bạn đọc, Mượn trả và gia hạn | `POST /api/loans/tickets`, `POST /api/loans/tickets/{id}/review`, `POST /api/loans/tickets/{id}/pickup`, `POST /api/loans/checkout` | `borrow_tickets`, `borrow_ticket_items`, `book_copies`, `loans`, `loan_items` |
| UC003 | Nhận trả sách | Thủ thư | Mượn trả và gia hạn | `POST /api/loans/{loan_id}/items/{item_id}/return` | `loan_items`, `book_copies`, `readers`, `loans` |
| UC004 | Thêm sách | Thủ thư, quản trị viên | Sách & kho, Nhập sách | `POST /api/catalog/books`, `POST /api/catalog/books/{id}/copies`, `POST /api/acquisitions` | `book_titles`, `book_copies`, `authors`, `categories`, `publishers`, `acquisitions` |
| UC005 | Đăng ký thẻ đọc | Bạn đọc, thủ thư | Cổng bạn đọc, Bạn đọc và thu tiền | `POST /api/auth/register-reader`, `POST /api/readers/me/card-request`, `POST /api/readers/card-requests/{id}/approve` | `users`, `card_requests`, `readers` |

## 7. Số luồng nghiệp vụ theo tác nhân

### 7.1. Quản trị viên

Quản trị viên có 10 nhóm luồng:

| STT | Luồng | Thuộc UC |
|---|---|---|
| 1 | Đăng nhập | Không |
| 2 | Quản lý tài khoản | Không |
| 3 | Quản lý quy định hệ thống | Không |
| 4 | Tra cứu sách | UC001 |
| 5 | Thêm sách, thêm bản sao | UC004 |
| 6 | Duyệt yêu cầu cấp thẻ | UC005 |
| 7 | Xử lý mượn/trả | UC002, UC003 |
| 8 | Nhập sách | Mở rộng UC004 |
| 9 | Thu tiền phạt | Không |
| 10 | Xem báo cáo | Không |

### 7.2. Thủ thư

Thủ thư có 15 nhóm luồng:

| STT | Luồng | Thuộc UC |
|---|---|---|
| 1 | Đăng nhập | Không |
| 2 | Tra cứu sách | UC001 |
| 3 | Thêm đầu sách và bản sao | UC004 |
| 4 | Nhập sách từ nhà cung cấp | Mở rộng UC004 |
| 5 | Duyệt yêu cầu cấp thẻ online | UC005 |
| 6 | Tạo thẻ tại quầy | UC005 |
| 7 | Kiểm tra phiếu đăng ký mượn online | UC002 |
| 8 | Phản hồi khi thiếu bản sao | UC002 |
| 9 | Duyệt phần sách còn sẵn | UC002 |
| 10 | Xác nhận bạn đọc đến lấy sách | UC002 |
| 11 | Lập phiếu mượn trực tiếp tại quầy | UC002 |
| 12 | Nhận trả sách | UC003 |
| 13 | Tính phạt quá hạn | UC003 |
| 14 | Gia hạn phiếu mượn | Không |
| 15 | Thu tiền phạt và xem báo cáo | Không |

### 7.3. Bạn đọc

Bạn đọc có 11 nhóm luồng:

| STT | Luồng | Thuộc UC |
|---|---|---|
| 1 | Đăng ký tài khoản | Chuẩn bị UC005 |
| 2 | Gửi yêu cầu cấp thẻ đọc | UC005 |
| 3 | Theo dõi trạng thái thẻ | UC005 |
| 4 | Tra cứu sách | UC001 |
| 5 | Lập phiếu đăng ký mượn online | UC002 |
| 6 | Xem phản hồi khi thiếu sách | UC002 |
| 7 | Sửa phiếu và gửi lại | UC002 |
| 8 | Đồng ý mượn phần còn sẵn | UC002 |
| 9 | Đến thư viện lấy sách | UC002 |
| 10 | Xem sách đang mượn | Không |
| 11 | Xem lịch sử và công nợ | Không |

## 8. Công thức tính hạn và phạt

### 8.1. Hạn trả

Hạn trả không tính từ lúc thủ thư duyệt phiếu online.

Hạn trả tính từ lúc bạn đọc đến thư viện lấy sách và thủ thư bấm **Xác nhận đã lấy**.

```text
loaned_at = thời điểm thủ thư xác nhận đã lấy
due_at = loaned_at + loan_days
```

`loan_days` lấy từ `system_settings`.

Mặc định hiện tại:

```text
loan_days = 14
```

Ví dụ:

```text
Thủ thư duyệt online: 2026-06-25
Bạn đọc đến lấy sách: 2026-06-28
loan_days: 14
Hạn trả: 2026-07-12
```

### 8.2. Phạt quá hạn

Phạt được tính khi thủ thư bấm **Nhận trả**.

```text
số ngày quá hạn = max(0, ngày trả thực tế - ngày hẹn trả)
tiền phạt = số ngày quá hạn * fine_per_day
```

`fine_per_day` lấy từ `system_settings`.

Mặc định hiện tại:

```text
fine_per_day = 5000
```

Ví dụ:

```text
Hạn trả: 2026-07-12
Ngày trả: 2026-07-15
Quá hạn: 3 ngày
Tiền phạt/ngày: 5000
Tiền phạt: 15000 đồng
```

Khi nhận trả:

- `loan_items.returned_at` được ghi ngày trả
- `loan_items.fine_amount` được ghi tiền phạt
- `readers.balance` cộng thêm tiền phạt
- `book_copies.status` đổi về `available`
- nếu mọi cuốn trong phiếu đã trả, `loans.status` đổi thành `completed`

## 9. Kịch bản demo đề xuất

### Kịch bản 1: Đăng ký thẻ đọc online

1. Mở web.
2. Đăng ký tài khoản bạn đọc mới.
3. Đăng nhập bằng tài khoản đó.
4. Gửi yêu cầu cấp thẻ đọc.
5. Đăng nhập admin.
6. Vào **Bạn đọc và thu tiền**.
7. Duyệt yêu cầu cấp thẻ.
8. Đăng nhập lại bạn đọc.
9. Kiểm tra đã có mã thẻ `DG-xxxx`.

Liên quan UC: UC005.

### Kịch bản 2: Mượn sách online đủ bản sao

1. Bạn đọc có thẻ còn hạn đăng nhập.
2. Tìm sách.
3. Chọn nhiều đầu sách.
4. Gửi phiếu đăng ký mượn.
5. Thủ thư vào **Mượn, trả và gia hạn**.
6. Bấm **Kiểm tra**.
7. Nếu đủ bản sao, phiếu chuyển **Đã duyệt, chờ lấy**.
8. Bạn đọc đến thư viện.
9. Thủ thư bấm **Xác nhận đã lấy**.
10. Hệ thống tạo phiếu mượn thật.

Liên quan UC: UC001, UC002.

### Kịch bản 3: Mượn sách online thiếu bản sao

1. Bạn đọc gửi phiếu gồm nhiều đầu sách.
2. Một đầu sách không còn bản sao `available`.
3. Thủ thư bấm **Kiểm tra**.
4. Phiếu chuyển **Cần bạn đọc phản hồi**.
5. Bạn đọc thấy sách nào còn và sách nào hết.
6. Bạn đọc chọn một trong hai cách:
   - sửa phiếu và gửi lại
   - đồng ý mượn phần còn sẵn
7. Hệ thống giữ chỗ các sách còn bản sao.

Liên quan UC: UC002.

### Kịch bản 4: Trả sách quá hạn

1. Thủ thư mở phiếu mượn đang mở.
2. Bấm **Nhận trả**.
3. Nếu ngày trả sau `due_at`, hệ thống tính phạt.
4. Công nợ bạn đọc tăng.
5. Sách trở lại `available`.
6. Thủ thư thu tiền phạt ở màn **Bạn đọc và thu tiền**.

Liên quan UC: UC003.

### Kịch bản 5: Thêm sách và nhập kho

1. Thủ thư vào **Sách & kho**.
2. Tạo đầu sách mới.
3. Thêm bản sao vật lý với mã vạch.
4. Hoặc vào **Nhập sách**, tạo phiếu nhập từ nhà cung cấp.
5. Hệ thống tạo thêm bản sao.
6. Bạn đọc tìm thấy sách mới ở cổng bạn đọc.

Liên quan UC: UC004, UC001.
