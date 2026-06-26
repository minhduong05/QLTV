# Cập Nhật Logic Nghiệp Vụ

Tài liệu này mô tả các logic đã chỉnh để web chạy đúng hơn với quy trình thư viện thực tế.

## 1. Cấp thẻ bạn đọc online và tại quầy

Thông tin bạn đọc điền khi gửi yêu cầu cấp thẻ online đã được đồng bộ với thông tin thủ thư nhập khi tạo thẻ tại quầy:

| Trường | Online bạn đọc gửi | Tại quầy thủ thư nhập |
|---|---|---|
| Họ và tên | Có | Có |
| Email | Lấy từ tài khoản đăng nhập | Có |
| Số điện thoại | Có | Có |
| Ngày sinh | Có | Có |
| Địa chỉ | Có | Có |
| Loại bạn đọc | Có | Có |
| Mã thẻ | Hệ thống sinh khi duyệt | Thủ thư nhập hoặc hệ thống gợi ý |
| Hạn thẻ | Hệ thống tính theo quy định | Thủ thư nhập |

Luồng online:

1. Bạn đọc đăng ký tài khoản đăng nhập.
2. Tài khoản này chưa được mượn sách vì chưa có dòng trong bảng `readers`.
3. Bạn đọc gửi yêu cầu cấp thẻ, backend ghi `card_requests` trạng thái `pending`.
4. Thủ thư mở màn **Bạn đọc, cấp thẻ và thu phạt**, xem yêu cầu.
5. Nếu hợp lệ, thủ thư bấm duyệt. Backend sinh mã `DG-xxxx`, tạo dòng `readers`, đổi `card_requests.status = approved`.
6. Nếu không hợp lệ, thủ thư từ chối và ghi lý do. Bạn đọc sửa/gửi lại sau.

Điều kiện để mượn sách:

- Có tài khoản `users.role = reader`.
- Có thẻ trong `readers`.
- `readers.is_active = true`.
- `readers.expires_at` chưa quá hạn.
- Chưa vượt số sách đang mượn/đang được giữ chỗ tối đa.

## 2. Thu tiền phạt / công nợ

Thu tiền phạt đã được tách khỏi duyệt thẻ đọc.

Logic đúng là:

1. Tiền phạt không tự xuất hiện ở màn thu tiền.
2. Tiền phạt phát sinh khi thủ thư nhận trả sách quá hạn.
3. Khi trả quá hạn, backend tính:

```text
số ngày quá hạn = ngày trả thực tế - hạn trả
tiền phạt = số ngày quá hạn * system_settings.fine_per_day
```

4. Backend ghi tiền phạt vào `loan_items.fine_amount`.
5. Backend cộng số tiền đó vào `readers.balance`.
6. Màn **Thu tiền phạt / công nợ** chỉ hiển thị bạn đọc có `balance > 0`.
7. Khi thủ thư thu tiền, backend ghi `payments` và trừ vào `readers.balance`.

Ví dụ:

- Bạn đọc trả sách trễ 3 ngày.
- Quy định phạt là 5.000 đ/ngày.
- Hệ thống cộng công nợ 15.000 đ.
- Thủ thư thu 10.000 đ thì `readers.balance` còn 5.000 đ.
- Thủ thư thu toàn bộ 15.000 đ thì `readers.balance = 0`.

## 3. Phiếu đăng ký mượn online có số lượng

Mỗi dòng trong phiếu mượn giờ có số lượng:

```text
borrow_ticket_items.requested_quantity
borrow_ticket_items.approved_quantity
```

Bạn đọc có thể chọn cùng một đầu sách và nhập số lượng cần mượn, ví dụ:

| Đầu sách | Số lượng yêu cầu |
|---|---:|
| Clean Code | 2 |
| Atomic Habits | 1 |

Backend kiểm tra giới hạn mượn theo tổng số lượng, không chỉ theo số dòng đầu sách.

## 4. Kiểm tra phiếu khác với duyệt phiếu

Trước đây nút kiểm tra và duyệt gần như giống nhau. Logic mới tách rõ:

### Bước 1: Kiểm tra chi tiết

Thủ thư bấm **Kiểm tra chi tiết**.

Backend:

- Đếm số bản sao `available` cho từng đầu sách.
- So sánh với `requested_quantity`.
- Chưa giữ chỗ bản sao nào.
- Nếu đủ toàn bộ, phiếu sang `reviewed`.
- Nếu thiếu một phần, phiếu sang `changes_requested`.

Ý nghĩa:

- `reviewed`: đã kiểm tra, đủ số lượng, đang chờ thủ thư bấm duyệt giữ chỗ.
- `changes_requested`: có đầu sách thiếu bản sao, bạn đọc có thể sửa phiếu hoặc đồng ý mượn phần còn sẵn.

### Bước 2: Duyệt giữ chỗ

Thủ thư bấm **Duyệt giữ chỗ** hoặc **Duyệt phần còn sẵn**.

Backend:

- Chọn đúng số bản sao vật lý còn `available`.
- Ghi từng bản sao được giữ vào `borrow_ticket_reservations`.
- Đổi các `book_copies.status` từ `available` sang `reserved`.
- Cập nhật `approved_quantity`.
- Đổi phiếu sang `approved_waiting_pickup`.

### Bước 3: Bạn đọc đến lấy sách

Thủ thư bấm **Xác nhận đã lấy**.

Backend:

- Tạo `loans`.
- Tạo nhiều dòng `loan_items` tương ứng với từng bản sao đã giữ.
- Đổi `book_copies.status` từ `reserved` sang `on_loan`.
- Đổi phiếu online sang `borrowed`.

## 5. Nhập sách và vị trí kệ

Màn nhập sách hỗ trợ hai cách:

1. Chọn đầu sách đã có.
2. Tạo đầu sách mới ngay trong phiếu nhập.

Khi tạo đầu sách mới, thủ thư nhập:

- Tên sách.
- ISBN.
- Thể loại.
- Nhà xuất bản.
- Tác giả.
- Năm xuất bản.
- Mô tả.

Trong phiếu nhập, trường **vị trí kệ** được hiểu là vị trí áp dụng cho toàn bộ số bản sao nhập trong dòng đó.

Ví dụ:

```text
Đầu sách: Clean Code
Số lượng nhập: 3
Vị trí kệ: A2-01
```

Backend sẽ tạo 3 dòng `book_copies`, tất cả có `shelf_location = A2-01`.

Nếu thủ thư nhập barcode thủ công, số barcode phải bằng đúng số lượng nhập. Nếu để trống, hệ thống tự sinh barcode dạng:

```text
ACQ-000001-01-001
ACQ-000001-01-002
...
```

## 6. Dữ liệu mẫu hiện tại

Database local đã được dọn để chỉ hiển thị các đầu sách đang phục vụ. Có 15 đầu sách active:

- 4 đầu sách demo ban đầu.
- 5 đầu sách mới có 2 bản sao.
- 5 đầu sách mới có 1 bản sao.
- 1 đầu sách mới có 0 bản sao để test tình huống hết sách.

Các sách test linh tinh nếu đã có lịch sử nghiệp vụ thì không xóa cứng, mà chuyển `is_active = false` để không hiện trong catalog đang phục vụ.
