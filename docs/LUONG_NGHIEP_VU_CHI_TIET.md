# Luồng nghiệp vụ chi tiết

Tài liệu này mô tả cách web quản lý thư viện vận hành ngoài đời, dữ liệu ghi vào đâu và màn hình nào hiển thị kết quả.

## Tác nhân và tài khoản mẫu

| Tác nhân | Tài khoản mẫu | Luồng nghiệp vụ chính |
|---|---|---|
| Quản trị viên | `admin@example.com` / `admin123` | Quản lý tài khoản, phân quyền, quy định hệ thống, xem toàn bộ nghiệp vụ |
| Thủ thư | Do admin tạo | Duyệt thẻ, quản lý sách/kho, duyệt phiếu mượn online, lập phiếu mượn trực tiếp, nhận trả, thu phạt, nhập sách |
| Bạn đọc | `reader@example.com` / `reader123` hoặc tự đăng ký | Đăng ký tài khoản, gửi yêu cầu cấp thẻ, tra cứu sách, lập phiếu đăng ký mượn online, theo dõi mượn/trả và công nợ |

## Tổng quan luồng ngoài đời

1. Người mới tạo tài khoản bạn đọc online.
2. Bạn đọc gửi yêu cầu cấp thẻ đọc, nhập số điện thoại, ngày sinh, địa chỉ.
3. Thủ thư kiểm tra hồ sơ và duyệt online.
4. Hệ thống tạo thẻ đọc, ví dụ `DG-0005`, hạn 12 tháng theo `system_settings.card_validity_months`.
5. Khi thẻ còn hạn và đang hoạt động, bạn đọc tra cứu sách và lập một phiếu đăng ký mượn gồm nhiều đầu sách.
6. Thủ thư kiểm tra bản sao vật lý.
7. Nếu tất cả sách còn bản sao, hệ thống giữ chỗ các cuốn đó và phiếu chuyển sang `approved_waiting_pickup`.
8. Nếu một số sách hết bản sao, phiếu chuyển sang `changes_requested`; bạn đọc nhìn thấy sách nào còn, sách nào hết.
9. Bạn đọc có thể sửa phiếu gửi lại hoặc đồng ý mượn phần còn sẵn.
10. Khi bạn đọc đến thư viện lấy sách, thủ thư bấm xác nhận. Lúc này mới tạo `loans`, `loan_items` và đổi `book_copies.status` từ `reserved` sang `on_loan`.
11. Khi trả sách, thủ thư nhận trả từng cuốn, tính phạt nếu quá hạn và đưa bản sao về `available`.

## UC001 - Tìm kiếm sách

Tác nhân: quản trị viên, thủ thư, bạn đọc.

1. Người dùng nhập từ khóa tại **Sách & kho** hoặc **Cổng bạn đọc**.
2. Frontend gọi `GET /api/catalog/books?search=...`.
3. Backend tìm theo `book_titles.title`, `book_titles.isbn`, `authors.name`.
4. Kết quả hiển thị đầu sách, tác giả, thể loại, số bản sao `available`, số bản sao đang `reserved` hoặc `on_loan`.

Dữ liệu đọc: `book_titles`, `book_copies`, `authors`, `categories`, `publishers`.

Tương ứng báo cáo: UC001.

## UC002 - Mượn sách

### Lập phiếu đăng ký mượn online

Tác nhân: bạn đọc.

1. Bạn đọc phải có bản ghi `readers`, thẻ `is_active = true`, `expires_at` chưa quá hạn.
2. Bạn đọc chọn nhiều đầu sách ở **Cổng bạn đọc**.
3. Frontend gọi `POST /api/loans/tickets`.
4. Backend tạo `borrow_tickets` trạng thái `pending_review`.
5. Backend tạo các dòng `borrow_ticket_items` trạng thái `pending`.
6. Bạn đọc thấy phiếu trong khối **Phiếu đăng ký mượn**.
7. Thủ thư thấy phiếu tại **Mượn, trả và gia hạn**.

### Thủ thư kiểm tra phiếu online

Tác nhân: thủ thư.

1. Thủ thư bấm **Kiểm tra**.
2. Frontend gọi `POST /api/loans/tickets/{id}/review`.
3. Backend đếm `book_copies.status = available` cho từng đầu sách.
4. Nếu đủ tất cả, backend đổi các bản sao được chọn sang `reserved`, cập nhật `borrow_ticket_items.status = reserved`, phiếu sang `approved_waiting_pickup`.
5. Nếu thiếu một số đầu sách, backend đặt dòng đủ bản sao là `available`, dòng thiếu là `unavailable`, ghi `unavailable_reason`, phiếu sang `changes_requested`.
6. Bạn đọc thấy phản hồi: sách nào có bản sao, sách nào hết bản sao.

### Bạn đọc phản hồi khi thiếu bản sao

Tác nhân: bạn đọc.

1. Nếu muốn thay đổi, bạn đọc bấm **Sửa phiếu**, bỏ/chọn lại sách và gửi.
2. Frontend gọi `PUT /api/loans/tickets/{id}`.
3. Backend đưa phiếu về `pending_review` để thủ thư kiểm tra lại.
4. Nếu không thay đổi, bạn đọc bấm **Mượn phần còn sẵn**.
5. Frontend gọi `POST /api/loans/tickets/{id}/approve-available`.
6. Backend giữ chỗ các bản sao còn sẵn, các dòng thiếu chuyển `skipped`, phiếu sang `approved_waiting_pickup`.

### Bạn đọc đến thư viện lấy sách

Tác nhân: thủ thư.

1. Thủ thư kiểm tra bạn đọc và bấm **Xác nhận đã lấy**.
2. Frontend gọi `POST /api/loans/tickets/{id}/pickup`.
3. Backend tạo `loans`, tạo `loan_items`, đặt hạn trả theo `system_settings.loan_days`.
4. Backend đổi các `book_copies.status` từ `reserved` sang `on_loan`.
5. Phiếu online sang `borrowed`, gắn `loan_id`.
6. Bạn đọc thấy sách trong **Sách đang mượn**.

### Lập phiếu mượn trực tiếp tại quầy

Tác nhân: thủ thư.

1. Thủ thư chọn bạn đọc và các bản sao vật lý đang `available`.
2. Frontend gọi `POST /api/loans/checkout`.
3. Backend kiểm tra thẻ, hạn mượn, số sách tối đa, trạng thái bản sao.
4. Backend tạo `loans`, `loan_items`, đổi `book_copies.status` sang `on_loan`.

Dữ liệu ghi: `borrow_tickets`, `borrow_ticket_items`, `book_copies`, `loans`, `loan_items`.

Tương ứng báo cáo: UC002.

## UC003 - Nhận trả sách

Tác nhân: thủ thư.

1. Thủ thư bấm **Nhận trả** trên từng cuốn trong phiếu đang mở.
2. Frontend gọi `POST /api/loans/{loan_id}/items/{item_id}/return`.
3. Backend ghi `loan_items.returned_at`.
4. Nếu quá hạn, backend tính `overdue_days * system_settings.fine_per_day`, ghi `loan_items.fine_amount`, cộng vào `readers.balance`.
5. Backend đổi `book_copies.status` về `available`.
6. Nếu mọi cuốn trong phiếu đã trả, backend đổi `loans.status = completed`.

Dữ liệu ghi: `loan_items`, `book_copies`, `readers.balance`, `loans`.

Tương ứng báo cáo: UC003.

## UC004 - Thêm sách

Tác nhân: thủ thư, quản trị viên.

1. Thủ thư tạo thể loại, tác giả, nhà xuất bản nếu chưa có.
2. Thủ thư tạo đầu sách tại **Sách & kho**.
3. Backend ghi `categories`, `authors`, `publishers`, `book_titles`, `book_title_authors`.
4. Thủ thư thêm bản sao thủ công hoặc tạo phiếu nhập.
5. Backend ghi `book_copies`; nếu nhập sách thì ghi thêm `suppliers`, `acquisitions`, `acquisition_items`.
6. Cổng bạn đọc và màn kho cập nhật số bản sao sẵn có.

Tương ứng báo cáo: UC004.

## UC005 - Đăng ký thẻ đọc

### Đăng ký tài khoản bạn đọc

Tác nhân: bạn đọc.

1. Người dùng chọn **Đăng ký bạn đọc mới**.
2. Frontend gọi `POST /api/auth/register-reader`.
3. Backend ghi `users` với role `reader`.
4. Tài khoản lúc này mới là tài khoản đăng nhập, chưa có quyền mượn.

### Gửi yêu cầu cấp thẻ online

Tác nhân: bạn đọc.

1. Sau khi đăng nhập, nếu chưa có thẻ, cổng bạn đọc hiển thị form cấp thẻ.
2. Bạn đọc nhập số điện thoại, ngày sinh, địa chỉ.
3. Frontend gọi `POST /api/readers/me/card-request`.
4. Backend ghi `card_requests` trạng thái `pending`.
5. Bạn đọc thấy trạng thái **Chờ thủ thư duyệt**.

### Thủ thư duyệt thẻ

Tác nhân: thủ thư.

1. Thủ thư mở **Bạn đọc và thu tiền**, xem danh sách yêu cầu cấp thẻ.
2. Nếu hồ sơ hợp lệ, thủ thư bấm **Duyệt cấp thẻ**.
3. Frontend gọi `POST /api/readers/card-requests/{id}/approve`.
4. Backend sinh mã thẻ `DG-xxxx`, ghi `readers`, cập nhật `card_requests.status = approved`.
5. Nếu hồ sơ chưa hợp lệ, thủ thư bấm **Từ chối**.
6. Frontend gọi `POST /api/readers/card-requests/{id}/reject`; backend ghi lý do để bạn đọc gửi lại.

Tương ứng báo cáo: UC005.

## Luồng nghiệp vụ mở rộng

| Luồng | Tác nhân | Bảng chính | Màn hình |
|---|---|---|---|
| Quản lý tài khoản nội bộ | Quản trị viên | `users` | Quản trị |
| Quản lý quy định mượn/trả | Quản trị viên | `system_settings` | Quản trị |
| Gia hạn phiếu | Thủ thư | `loans.due_at`, `loans.renewal_count` | Mượn, trả và gia hạn |
| Thu tiền phạt | Thủ thư | `payments`, `readers.balance` | Bạn đọc và thu tiền |
| Khóa/mở thẻ bạn đọc | Thủ thư | `readers.is_active` | Bạn đọc và thu tiền |
| Quản lý nhà cung cấp, nhập sách | Thủ thư | `suppliers`, `acquisitions`, `acquisition_items`, `book_copies` | Nhập sách |
| Báo cáo quá hạn | Thủ thư, quản trị viên | Đọc `loans`, `loan_items`, `readers`, `book_copies` | Báo cáo |
| Báo cáo sách mượn nhiều | Thủ thư, quản trị viên | Đọc `loan_items`, `book_copies`, `book_titles` | Báo cáo |
| Báo cáo theo thể loại | Thủ thư, quản trị viên | Đọc `categories`, `book_titles`, `loan_items` | Báo cáo |

## Số luồng theo tác nhân

Quản trị viên có 9 luồng: đăng nhập; quản lý tài khoản; quản lý quy định; quản lý danh mục/sách; quản lý bạn đọc; theo dõi mượn/trả; nhập sách; thu phạt; xem báo cáo.

Thủ thư có 11 luồng: đăng nhập; duyệt/từ chối thẻ; tạo thẻ tại quầy; quản lý bạn đọc; thêm sách/bản sao; nhập sách; kiểm tra phiếu online; duyệt phiếu/chờ lấy; xác nhận lấy sách; nhận trả/gia hạn; thu phạt và xem báo cáo.

Bạn đọc có 8 luồng: đăng ký tài khoản; gửi yêu cầu cấp thẻ; tra cứu sách; lập phiếu đăng ký mượn; sửa phiếu khi thiếu bản sao; đồng ý mượn phần còn sẵn; theo dõi sách đang mượn/lịch sử; xem công nợ.

## Dữ liệu mẫu

Backend tự seed nếu thiếu dữ liệu:

- Admin: `admin@example.com` / `admin123`
- Bạn đọc: `reader@example.com` / `reader123`
- Sách mẫu, bản sao, loại bạn đọc, nhà cung cấp, phiếu nhập và lịch sử mượn.
