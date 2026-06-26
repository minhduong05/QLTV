# Hệ Thống Quản Lý Thư Viện

Đây là phiên bản web của hệ thống quản lý thư viện, được xây dựng lại theo mô hình phân tầng để phục vụ các nghiệp vụ chính trong báo cáo phân tích thiết kế hệ thống thông tin và các nghiệp vụ mở rộng thường có trong thư viện thực tế.

## 1. Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|---|---|
| Backend API | FastAPI |
| ORM / Data Access | SQLAlchemy |
| Database mặc định | SQLite |
| Database có thể triển khai | PostgreSQL |
| Authentication | JWT, Argon2 password hash |
| Frontend | React |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Migration | Alembic |

Backend mặc định dùng SQLite tại:

```text
backend/library.db
```

Khi backend khởi động, hệ thống tự:

- Tạo bảng nếu chưa có.
- Bổ sung một số cột tương thích cho SQLite local cũ.
- Seed dữ liệu mẫu: tài khoản, bạn đọc, sách, bản sao, loại bạn đọc, nhà cung cấp, quy định hệ thống.

## 2. Tài Khoản Mẫu

| Vai trò | Email | Mật khẩu | Mục đích |
|---|---|---|---|
| Quản trị viên | `admin@example.com` | `admin123` | Quản lý tài khoản, quy định, xem toàn hệ thống |
| Bạn đọc đã có thẻ | `reader@example.com` | `reader123` | Test cổng bạn đọc, mượn sách, xem công nợ |

Quản trị viên có thể tạo thêm tài khoản thủ thư hoặc quản trị viên tại màn **Quản trị hệ thống**.

Bạn đọc mới tự đăng ký tài khoản tại màn đăng nhập, sau đó gửi yêu cầu cấp thẻ đọc online để thủ thư duyệt.

## 3. Cách Chạy Local

### 3.1. Chạy backend

Mở terminal 1:

```powershell
cd "D:\2025_2\Phân tích và thiết kế hệ thống thông tin\QLTV\backend"
uv run --with-requirements requirements.txt python -m uvicorn app.main:app --reload
```

Backend chạy tại:

```text
http://localhost:8000
```

Swagger API:

```text
http://localhost:8000/docs
```

### 3.2. Chạy frontend

Mở terminal 2:

```powershell
cd "D:\2025_2\Phân tích và thiết kế hệ thống thông tin\QLTV\frontend"
npm install
npm run dev
```

Frontend chạy tại:

```text
http://localhost:5173
```

### 3.3. Kiểm tra build

Backend:

```powershell
cd "D:\2025_2\Phân tích và thiết kế hệ thống thông tin\QLTV\backend"
uv run --with-requirements requirements.txt python -m compileall app
```

Frontend:

```powershell
cd "D:\2025_2\Phân tích và thiết kế hệ thống thông tin\QLTV\frontend"
npm run build
```

## 4. Cấu Trúc Thư Mục

```text
QLTV/
├─ backend/
│  ├─ app/
│  │  ├─ main.py              # Khởi tạo FastAPI, CORS, router, database startup
│  │  ├─ config.py            # Cấu hình môi trường
│  │  ├─ database.py          # Engine, SessionLocal, Base
│  │  ├─ models.py            # ORM models, mapping bảng database
│  │  ├─ schemas.py           # Pydantic DTO/request/response
│  │  ├─ security.py          # Hash mật khẩu, JWT
│  │  ├─ services.py          # Logic dịch vụ dùng chung
│  │  ├─ seed.py              # Dữ liệu mẫu
│  │  └─ routers/
│  │     ├─ auth.py           # Đăng nhập, đăng ký bạn đọc, bootstrap admin
│  │     ├─ users.py          # Quản trị tài khoản
│  │     ├─ catalog.py        # Đầu sách, bản sao, tác giả, thể loại, NXB
│  │     ├─ readers.py        # Thẻ bạn đọc, duyệt thẻ, thu phạt
│  │     ├─ loans.py          # Phiếu mượn online, mượn/trả/gia hạn
│  │     ├─ acquisitions.py   # Nhà cung cấp, nhập sách
│  │     ├─ dashboard.py      # Báo cáo tổng quan
│  │     └─ settings.py       # Quy định hệ thống
│  ├─ alembic/                # Migration database
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ App.jsx              # Điều hướng theo role
│  │  ├─ api.js               # Hàm gọi API
│  │  ├─ main.jsx
│  │  ├─ index.css
│  │  ├─ components/
│  │  │  └─ ui.jsx            # Component UI dùng chung
│  │  └─ pages/
│  │     ├─ AdminPage.jsx
│  │     ├─ CatalogPage.jsx
│  │     ├─ CirculationPage.jsx
│  │     ├─ DashboardPage.jsx
│  │     ├─ ReadersPage.jsx
│  │     ├─ ReaderPortalPage.jsx
│  │     ├─ AcquisitionsPage.jsx
│  │     └─ ReportsPage.jsx
│  ├─ package.json
│  └─ vite.config.js
├─ docs/
│  ├─ LUONG_NGHIEP_VU_CHI_TIET.md
│  ├─ TONG_HOP_LUONG_TAC_NHAN_VA_USE_CASE.md
│  ├─ KIEN_TRUC_VA_HUONG_DAN.md
│  └─ CAP_NHAT_LOGIC_NGHIEP_VU.md
└─ README.md
```

## 5. Kiến Trúc Phân Tầng

Hệ thống được tổ chức theo mô hình phân tầng. Mỗi tầng có trách nhiệm riêng, hạn chế trộn logic giao diện, nghiệp vụ và truy cập dữ liệu.

### 5.1. Tầng giao diện

Vị trí:

```text
frontend/src/pages/
frontend/src/components/
frontend/src/api.js
```

Trách nhiệm:

- Hiển thị màn hình theo vai trò: quản trị, thủ thư, bạn đọc.
- Nhận thao tác người dùng.
- Gọi API backend qua `frontend/src/api.js`.
- Không trực tiếp thao tác database.

Các màn hình chính:

| Màn hình | Tác nhân | Chức năng |
|---|---|---|
| `AdminPage.jsx` | Quản trị viên | Quản lý tài khoản, quy định |
| `CatalogPage.jsx` | Quản trị viên, thủ thư | Quản lý đầu sách, bản sao |
| `ReadersPage.jsx` | Thủ thư | Duyệt thẻ đọc, tạo thẻ tại quầy, thu phạt |
| `CirculationPage.jsx` | Thủ thư | Duyệt phiếu mượn, mượn trực tiếp, trả/gia hạn |
| `AcquisitionsPage.jsx` | Thủ thư | Nhập sách, nhà cung cấp |
| `ReaderPortalPage.jsx` | Bạn đọc | Đăng ký thẻ, tra cứu sách, gửi phiếu mượn |
| `ReportsPage.jsx` | Quản trị viên, thủ thư | Báo cáo quá hạn, sách phổ biến |

### 5.2. Tầng API / Controller

Vị trí:

```text
backend/app/routers/
```

Trách nhiệm:

- Nhận request HTTP.
- Kiểm tra quyền truy cập.
- Validate dữ liệu đầu vào qua schema.
- Điều phối xử lý nghiệp vụ.
- Trả response cho frontend.

Các router chính:

| Router | Nhóm nghiệp vụ |
|---|---|
| `auth.py` | Đăng nhập, đăng ký bạn đọc, lấy thông tin tài khoản |
| `users.py` | Quản lý tài khoản hệ thống |
| `catalog.py` | Đầu sách, tác giả, thể loại, nhà xuất bản, bản sao |
| `readers.py` | Bạn đọc, thẻ đọc, yêu cầu cấp thẻ, thu tiền phạt |
| `loans.py` | Phiếu mượn online, mượn trực tiếp, trả sách, gia hạn |
| `acquisitions.py` | Nhà cung cấp, nhập sách |
| `settings.py` | Quy định mượn/trả |
| `dashboard.py` | Báo cáo, thống kê |

### 5.3. Tầng nghiệp vụ

Vị trí:

```text
backend/app/routers/
backend/app/services.py
backend/app/seed.py
```

Trách nhiệm:

- Kiểm tra thẻ bạn đọc còn hạn hay không.
- Kiểm tra số lượng sách đang mượn/đang giữ chỗ.
- Kiểm tra bản sao vật lý còn sẵn.
- Duyệt phiếu mượn, giữ chỗ bản sao, xác nhận lấy sách.
- Tính tiền phạt khi trả quá hạn.
- Kiểm tra điều kiện xóa tài khoản.
- Seed dữ liệu mẫu.

Một số quy định nghiệp vụ đang áp dụng:

| Quy định | Mặc định |
|---|---:|
| Thời hạn thẻ đọc | 12 tháng |
| Số ngày mượn sách | 14 ngày |
| Số sách tối đa đang mượn/giữ chỗ | 5 |
| Tiền phạt quá hạn | 5.000 đ/ngày |

Các quy định này được lưu trong `system_settings` và có thể sửa tại màn **Quản trị hệ thống**.

### 5.4. Tầng schema / DTO

Vị trí:

```text
backend/app/schemas.py
```

Trách nhiệm:

- Định nghĩa request body.
- Định nghĩa response trả về frontend.
- Validate kiểu dữ liệu, độ dài, số lượng.

Ví dụ:

- `ReaderCardRegisterRequest`: thông tin bạn đọc gửi khi xin cấp thẻ.
- `BorrowTicketCreate`: phiếu đăng ký mượn online.
- `PaymentCreate`: phiếu thu tiền phạt.
- `BookTitleCreate`: tạo đầu sách.

### 5.5. Tầng truy cập dữ liệu

Vị trí:

```text
backend/app/database.py
backend/app/models.py
```

Trách nhiệm:

- Khởi tạo SQLAlchemy engine/session.
- Mapping class Python với bảng database.
- Quản lý quan hệ giữa các bảng.

Các bảng chính:

| Bảng | Ý nghĩa |
|---|---|
| `users` | Tài khoản đăng nhập |
| `readers` | Thẻ bạn đọc |
| `card_requests` | Yêu cầu cấp thẻ online |
| `book_titles` | Đầu sách |
| `book_copies` | Bản sao vật lý |
| `borrow_tickets` | Phiếu đăng ký mượn online |
| `borrow_ticket_items` | Dòng sách trong phiếu đăng ký |
| `borrow_ticket_reservations` | Bản sao được giữ chỗ cho phiếu online |
| `loans` | Phiếu mượn thật |
| `loan_items` | Từng bản sao trong phiếu mượn thật |
| `payments` | Phiếu thu tiền phạt/công nợ |
| `suppliers` | Nhà cung cấp |
| `acquisitions` | Phiếu nhập sách |
| `acquisition_items` | Dòng sách trong phiếu nhập |
| `system_settings` | Quy định hệ thống |

## 6. Vai Trò Và Quyền Hạn

### 6.1. Quản trị viên

Quản trị viên có các luồng chính:

- Đăng nhập hệ thống.
- Tạo tài khoản thủ thư/quản trị viên.
- Khóa/mở khóa tài khoản.
- Xóa tài khoản nếu tài khoản chưa phát sinh nghiệp vụ và đã qua 1 ngày.
- Quản lý quy định mượn/trả.
- Xem dashboard và báo cáo.
- Có thể thao tác các nghiệp vụ thư viện như thủ thư.

Lưu ý xóa tài khoản:

- Không được tự xóa tài khoản đang đăng nhập.
- Không được xóa admin hoạt động cuối cùng.
- Tài khoản đã phát sinh nghiệp vụ thì nên khóa để giữ lịch sử.
- Tài khoản chưa phát sinh nghiệp vụ nhưng mới tạo chưa đủ 1 ngày cũng chưa được xóa.

### 6.2. Thủ thư

Thủ thư có các luồng chính:

- Duyệt/từ chối yêu cầu cấp thẻ online.
- Tạo thẻ bạn đọc tại quầy.
- Quản lý đầu sách, bản sao.
- Nhập sách, tạo nhà cung cấp.
- Kiểm tra phiếu đăng ký mượn online.
- Duyệt giữ chỗ bản sao.
- Xác nhận bạn đọc đến lấy sách.
- Lập phiếu mượn trực tiếp tại quầy.
- Nhận trả sách, gia hạn.
- Thu tiền phạt/công nợ.
- Xem báo cáo.

### 6.3. Bạn đọc

Bạn đọc có các luồng chính:

- Đăng ký tài khoản online.
- Gửi yêu cầu cấp thẻ đọc online.
- Tra cứu sách.
- Gửi phiếu đăng ký mượn online, có chọn số lượng.
- Sửa phiếu khi thủ thư phản hồi thiếu bản sao.
- Đồng ý mượn phần còn sẵn.
- Theo dõi sách đang mượn, lịch sử mượn, công nợ.

## 7. Dữ Liệu Chính Và Trạng Thái

### 7.1. Tài khoản

Bảng:

```text
users
```

Vai trò:

| Role | Ý nghĩa |
|---|---|
| `admin` | Quản trị viên |
| `librarian` | Thủ thư |
| `reader` | Bạn đọc |

Tài khoản bạn đọc mới đăng ký chỉ có quyền đăng nhập. Muốn mượn sách phải có thẻ đọc hợp lệ trong bảng `readers`.

### 7.2. Thẻ bạn đọc

Bảng:

```text
readers
```

Một thẻ hợp lệ cần:

- `is_active = true`
- `expires_at` chưa quá hạn
- Có thông tin định danh như CCCD/CMND
- Không vượt giới hạn sách đang mượn/đang giữ chỗ

### 7.3. Bản sao vật lý

Bảng:

```text
book_copies
```

Trạng thái bản sao:

| Trạng thái | Ý nghĩa |
|---|---|
| `available` | Có thể cho mượn |
| `reserved` | Đã được giữ chỗ, chờ bạn đọc đến lấy |
| `on_loan` | Đang được mượn thật |
| `lost` | Mất |
| `damaged` | Hỏng |
| `retired` | Ngừng phục vụ |

### 7.4. Phiếu đăng ký mượn online

Bảng:

```text
borrow_tickets
borrow_ticket_items
borrow_ticket_reservations
```

Trạng thái phiếu:

| Trạng thái | Ý nghĩa |
|---|---|
| `pending_review` | Bạn đọc vừa gửi, chờ thủ thư kiểm tra |
| `reviewed` | Đã kiểm tra đủ số lượng, chờ thủ thư duyệt giữ chỗ |
| `changes_requested` | Có sách thiếu bản sao, chờ bạn đọc phản hồi hoặc thủ thư duyệt phần còn sẵn |
| `approved_waiting_pickup` | Đã giữ chỗ bản sao, chờ bạn đọc đến lấy |
| `borrowed` | Bạn đọc đã lấy sách, đã sinh phiếu mượn thật |
| `rejected` | Bị thủ thư từ chối |
| `cancelled` | Bạn đọc hủy |

### 7.5. Phiếu mượn thật

Bảng:

```text
loans
loan_items
```

Phiếu mượn thật chỉ được tạo khi:

- Bạn đọc đến thư viện lấy sách.
- Thủ thư bấm **Xác nhận đã lấy**.

Lúc đó bản sao chuyển từ `reserved` sang `on_loan`.

## 8. Năm Use Case Chính Trong Báo Cáo

Các use case dưới đây tương ứng với 5 UC chính trong báo cáo. Hệ thống web có mở rộng thêm nhiều luồng phụ, nhưng 5 UC này là lõi nghiệp vụ.

### UC001 - Tìm kiếm sách

Tác nhân:

- Bạn đọc
- Thủ thư
- Quản trị viên

Màn hình thực hiện:

- **Cổng bạn đọc**
- **Sách & kho**

Luồng thực hiện:

1. Người dùng nhập từ khóa theo tên sách, ISBN hoặc tác giả.
2. Frontend gọi:

```text
GET /api/catalog/books?search=...
```

3. Backend tìm trong:

```text
book_titles.title
book_titles.isbn
authors.name
```

4. Hệ thống trả về danh sách đầu sách, tác giả, thể loại, nhà xuất bản, số bản sao.
5. Frontend hiển thị số bản sao đang sẵn sàng, đang giữ chỗ hoặc đang mượn.

Dữ liệu đọc:

```text
book_titles
book_copies
authors
categories
publishers
```

### UC002 - Mượn sách

UC này có hai cách thực hiện: mượn online và mượn trực tiếp tại quầy.

#### A. Mượn online

Tác nhân:

- Bạn đọc
- Thủ thư

Điều kiện:

- Bạn đọc đã có thẻ đọc.
- Thẻ còn hạn.
- Thẻ đang hoạt động.
- Không vượt số sách tối đa.

Luồng thực hiện:

1. Bạn đọc đăng nhập vào **Cổng bạn đọc**.
2. Bạn đọc tra cứu sách.
3. Bạn đọc chọn đầu sách và nhập số lượng muốn mượn.
4. Frontend gọi:

```text
POST /api/loans/tickets
```

5. Backend tạo:

```text
borrow_tickets
borrow_ticket_items
```

6. Phiếu ở trạng thái `pending_review`.
7. Thủ thư mở màn **Mượn, trả và gia hạn**.
8. Thủ thư bấm **Kiểm tra chi tiết**.
9. Backend đếm số bản sao `available` theo từng đầu sách.
10. Nếu đủ số lượng, phiếu chuyển sang `reviewed`.
11. Thủ thư bấm **Duyệt giữ chỗ**.
12. Backend tạo `borrow_ticket_reservations`, chuyển bản sao sang `reserved`, phiếu sang `approved_waiting_pickup`.
13. Bạn đọc đến thư viện lấy sách.
14. Thủ thư bấm **Xác nhận đã lấy**.
15. Backend tạo:

```text
loans
loan_items
```

16. Bản sao chuyển từ `reserved` sang `on_loan`.
17. Phiếu online chuyển sang `borrowed`.

Trường hợp thiếu bản sao:

1. Nếu một số đầu sách không đủ số lượng, phiếu chuyển sang `changes_requested`.
2. Bạn đọc có thể sửa phiếu gửi lại.
3. Hoặc bạn đọc/thủ thư đồng ý duyệt phần còn sẵn.
4. Các dòng thiếu không được giữ chỗ.

#### B. Mượn trực tiếp tại quầy

Tác nhân:

- Thủ thư

Luồng thực hiện:

1. Bạn đọc đến quầy.
2. Thủ thư chọn bạn đọc.
3. Thủ thư chọn từng bản sao vật lý đang `available`.
4. Frontend gọi:

```text
POST /api/loans/checkout
```

5. Backend kiểm tra thẻ, hạn thẻ, giới hạn mượn.
6. Backend tạo `loans`, `loan_items`.
7. Bản sao chuyển sang `on_loan`.

Dữ liệu ghi:

```text
borrow_tickets
borrow_ticket_items
borrow_ticket_reservations
loans
loan_items
book_copies
```

### UC003 - Nhận trả sách

Tác nhân:

- Thủ thư

Màn hình thực hiện:

- **Mượn, trả và gia hạn**

Luồng thực hiện:

1. Thủ thư xem danh sách phiếu mượn đang mở.
2. Thủ thư bấm **Nhận trả** trên từng cuốn.
3. Frontend gọi:

```text
POST /api/loans/{loan_id}/items/{item_id}/return
```

4. Backend ghi `loan_items.returned_at`.
5. Backend kiểm tra ngày trả với `loans.due_at`.
6. Nếu trả quá hạn, backend tính:

```text
số ngày quá hạn = ngày trả thực tế - hạn trả
tiền phạt = số ngày quá hạn * system_settings.fine_per_day
```

7. Tiền phạt được ghi vào:

```text
loan_items.fine_amount
readers.balance
```

8. Bản sao chuyển từ `on_loan` về `available`.
9. Nếu tất cả sách trong phiếu đã trả, `loans.status = completed`.

Dữ liệu ghi:

```text
loan_items
loans
book_copies
readers.balance
```

### UC004 - Thêm sách

Tác nhân:

- Thủ thư
- Quản trị viên

Màn hình thực hiện:

- **Sách & kho**
- **Nhập sách**

Có hai cách thêm sách.

#### A. Thêm đầu sách và bản sao từ Sách & kho

Luồng thực hiện:

1. Thủ thư tạo thể loại, tác giả, nhà xuất bản nếu chưa có.
2. Thủ thư tạo đầu sách.
3. Frontend gọi:

```text
POST /api/catalog/books
```

4. Backend ghi:

```text
book_titles
book_title_authors
categories
authors
publishers
```

5. Thủ thư thêm bản sao vật lý cho đầu sách.
6. Backend ghi `book_copies`.

#### B. Nhập sách bằng phiếu nhập

Luồng thực hiện:

1. Thủ thư mở màn **Nhập sách**.
2. Chọn nhà cung cấp hoặc tạo nhà cung cấp mới.
3. Chọn đầu sách có sẵn hoặc tạo đầu sách mới ngay trong phiếu nhập.
4. Nhập số lượng, đơn giá, vị trí kệ.
5. Nếu nhập barcode thủ công, số barcode phải bằng số lượng.
6. Nếu không nhập barcode, hệ thống tự sinh mã.
7. Frontend gọi:

```text
POST /api/acquisitions
```

8. Backend ghi:

```text
suppliers
acquisitions
acquisition_items
book_copies
```

Vị trí kệ được hiểu là vị trí áp dụng cho toàn bộ số bản sao nhập trong dòng đó.

### UC005 - Đăng ký thẻ đọc

Tác nhân:

- Bạn đọc
- Thủ thư

Màn hình thực hiện:

- **Cổng bạn đọc**
- **Bạn đọc, cấp thẻ và thu phạt**

Luồng online:

1. Người dùng đăng ký tài khoản bạn đọc.
2. Frontend gọi:

```text
POST /api/auth/register-reader
```

3. Backend tạo tài khoản trong `users` với role `reader`.
4. Tài khoản này chưa được mượn sách vì chưa có thẻ đọc.
5. Bạn đọc đăng nhập.
6. Hệ thống báo chưa có thẻ đọc.
7. Bạn đọc gửi yêu cầu cấp thẻ, gồm:

```text
họ tên
CCCD/CMND
email
số điện thoại
ngày sinh
địa chỉ
loại bạn đọc
```

8. Frontend gọi:

```text
POST /api/readers/me/card-request
```

9. Backend ghi `card_requests` trạng thái `pending`.
10. Thủ thư mở màn **Bạn đọc, cấp thẻ và thu phạt**.
11. Thủ thư bấm **Xem chi tiết** để kiểm tra hồ sơ.
12. Nếu hợp lệ, thủ thư bấm **Duyệt cấp thẻ**.
13. Frontend gọi:

```text
POST /api/readers/card-requests/{id}/approve
```

14. Backend sinh mã thẻ `DG-xxxx`, tạo dòng trong `readers`, chuyển yêu cầu sang `approved`.
15. Bạn đọc có thẻ hợp lệ và có thể đăng ký mượn sách.

Luồng tại quầy:

1. Bạn đọc đến thư viện.
2. Thủ thư nhập thông tin tại form **Tạo thẻ bạn đọc tại quầy**.
3. Thông tin gồm họ tên, CCCD, email, SĐT, ngày sinh, địa chỉ, loại bạn đọc, hạn thẻ.
4. Frontend gọi:

```text
POST /api/readers
```

5. Backend tạo trực tiếp thẻ trong `readers`.

Dữ liệu ghi:

```text
users
card_requests
readers
```

## 9. Các Nghiệp Vụ Mở Rộng

Ngoài 5 UC chính, hệ thống còn có:

- Quản lý tài khoản quản trị/thủ thư.
- Khóa/mở tài khoản.
- Xóa tài khoản chưa phát sinh nghiệp vụ và đã qua 1 ngày.
- Quản lý quy định mượn/trả.
- Duyệt phiếu mượn theo cơ chế kiểm tra trước, duyệt giữ chỗ sau.
- Gia hạn phiếu mượn.
- Thu tiền phạt/công nợ.
- Báo cáo sách quá hạn.
- Báo cáo sách được mượn nhiều.
- Báo cáo mượn theo thể loại.
- Quản lý nhà cung cấp.
- Nhập sách và tự sinh barcode.

## 10. Tiền Phạt Và Công Nợ

Tiền phạt không tự sinh chỉ vì thời gian hiện tại đã quá hạn. Tiền phạt được chốt khi thủ thư nhận trả sách.

Luồng:

1. Phiếu mượn có `due_at`.
2. Bạn đọc trả sách sau hạn.
3. Thủ thư bấm **Nhận trả**.
4. Backend tính số ngày trễ.
5. Backend ghi tiền phạt vào `loan_items.fine_amount`.
6. Backend cộng tiền phạt vào `readers.balance`.
7. Khi bạn đọc nộp tiền, thủ thư lập phiếu thu.
8. Backend ghi `payments` và trừ `readers.balance`.

Ý nghĩa:

| Trường/Bảng | Ý nghĩa |
|---|---|
| `loan_items.fine_amount` | Tiền phạt phát sinh từ từng cuốn trả muộn |
| `readers.balance` | Tổng công nợ hiện tại của bạn đọc |
| `payments` | Lịch sử các lần bạn đọc nộp tiền |

## 11. Dữ Liệu Mẫu

Dữ liệu mẫu gồm:

- 1 admin.
- 1 bạn đọc đã có thẻ.
- Loại bạn đọc: sinh viên, giảng viên.
- Danh mục tác giả, thể loại, nhà xuất bản.
- 15 đầu sách active.
- Có đầu sách 2 bản sao, 1 bản sao và 0 bản sao để test hết sách.
- Phiếu nhập mẫu.
- Lịch sử mượn mẫu.

Một số sách mẫu:

- Phân tích và thiết kế hệ thống thông tin
- Clean Code
- Cho tôi xin một vé đi tuổi thơ
- Vũ trụ trong vỏ hạt dẻ
- 1984
- Sapiens: Lược sử loài người
- Atomic Habits
- Refactoring
- Thinking, Fast and Slow
- Đắc nhân tâm

## 12. API Docs

Khi backend đang chạy, mở:

```text
http://localhost:8000/docs
```

Swagger UI dùng để test API trực tiếp:

1. Gọi `POST /api/auth/login`.
2. Copy `access_token`.
3. Bấm **Authorize**.
4. Nhập:

```text
Bearer <access_token>
```

5. Gọi thử các API cần đăng nhập.

## 13. Tài Liệu Chi Tiết

Các file tài liệu nghiệp vụ nằm trong thư mục `docs/`:

| File | Nội dung |
|---|---|
| `docs/LUONG_NGHIEP_VU_CHI_TIET.md` | Luồng nghiệp vụ chi tiết |
| `docs/TONG_HOP_LUONG_TAC_NHAN_VA_USE_CASE.md` | Tổng hợp luồng theo tác nhân và use case |
| `docs/KIEN_TRUC_VA_HUONG_DAN.md` | Kiến trúc và hướng dẫn |
| `docs/CAP_NHAT_LOGIC_NGHIEP_VU.md` | Các cập nhật logic mới |

## 14. Ghi Chú Triển Khai

Mặc định local dùng SQLite để dễ chạy demo. Nếu muốn dùng PostgreSQL, tạo file:

```text
backend/.env
```

Ví dụ:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/qltv
SECRET_KEY=change-this-secret
CORS_ORIGINS=http://localhost:5173
```

Sau đó chạy backend như bình thường.
