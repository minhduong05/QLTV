# Web Quản lý thư viện — kiến trúc và hướng dẫn tổ chức

Tài liệu này mô tả ứng dụng web mới trong repository. Source C# WinForms cũ (`GUI`, `BUS`, `DAL`, `DTO`) được giữ lại làm tài liệu tham khảo; hệ thống đang phát triển nằm ở `backend/` và `frontend/`.

## 1. Mục tiêu và phạm vi

Hệ thống phục vụ thủ thư và quản trị viên của một thư viện. Thiết kế bám năm use case tiêu biểu trong báo cáo, nhưng triển khai thêm các nghiệp vụ quản trị cần thiết để vận hành như một ứng dụng thư viện hoàn chỉnh.

| Use case trong báo cáo | Triển khai trong web |
|---|---|
| UC001 — Tìm kiếm sách | Tìm theo tên, ISBN hoặc tác giả; hiển thị tồn kho từng cuốn/mã vạch |
| UC002 — Mượn sách | Phiếu mượn nhiều cuốn, kiểm tra thẻ, tồn kho, giới hạn mượn và hạn trả |
| UC003 — Nhận trả sách | Nhận trả từng cuốn, cập nhật kho, tính phạt quá hạn và công nợ |
| UC004 — Thêm sách | Tạo đầu sách, tác giả, thể loại, NXB; thêm cuốn thủ công hoặc từ phiếu nhập |
| UC005 — Đăng ký thẻ đọc | Tạo bạn đọc, loại bạn đọc, hạn thẻ và theo dõi công nợ |

Phần mở rộng tương đương repo WinForms gồm: người dùng/role, danh mục, kho từng cuốn, nhập sách–nhà cung cấp, thu phạt, quy định thư viện và các báo cáo.

## 2. Kiến trúc

```mermaid
flowchart LR
    UI[React + Vite + Tailwind] -->|REST JSON + JWT| API[FastAPI routers]
    API --> Service[Business rules / services]
    Service --> ORM[SQLAlchemy ORM]
    ORM --> DB[(SQLite / PostgreSQL)]
    Migration[Alembic migrations] --> DB
```

- **React** chịu trách nhiệm hiển thị màn hình và gọi API. JWT được lưu ở `localStorage` trong môi trường demo local.
- **FastAPI routers** chia API theo miền nghiệp vụ, không để mọi endpoint trong một file.
- **Services** chứa quy định dùng chung (mặc định số ngày mượn, phạt, giới hạn sách).
- **SQLAlchemy** biểu diễn bảng và quan hệ bằng class Python. Mặc định bản demo dùng SQLite để chạy ngay; khi triển khai nhóm có thể chuyển sang PostgreSQL bằng `DATABASE_URL`.
- **Alembic** lưu lịch sử thay đổi cấu trúc PostgreSQL để tất cả thành viên dùng cùng schema.

## 3. Cấu trúc thư mục

```text
QLTV/
├── backend/
│   ├── app/
│   │   ├── routers/             # HTTP API theo module nghiệp vụ
│   │   │   ├── auth.py          # bootstrap admin, login, tài khoản hiện tại
│   │   │   ├── users.py         # quản trị người dùng / role
│   │   │   ├── catalog.py       # sách, tác giả, thể loại, NXB, bản sao
│   │   │   ├── readers.py       # thẻ bạn đọc, phiếu thu
│   │   │   ├── loans.py         # mượn, trả, gia hạn
│   │   │   ├── acquisitions.py  # nhà cung cấp, phiếu nhập
│   │   │   ├── settings.py      # quy định thư viện
│   │   │   └── dashboard.py     # báo cáo/thống kê
│   │   ├── models.py            # SQLAlchemy entities
│   │   ├── schemas.py           # Pydantic request/response validation
│   │   ├── services.py          # quy định và nghiệp vụ dùng chung
│   │   ├── security.py          # hash mật khẩu + JWT
│   │   ├── dependencies.py      # DB session và kiểm tra quyền
│   │   └── main.py              # tạo FastAPI app, CORS, đăng ký routers
│   └── alembic/                 # migration database
├── frontend/
│   └── src/
│       ├── pages/               # một module nghiệp vụ một trang React
│       ├── components/          # UI dùng chung
│       ├── api.js               # fetch wrapper, JWT, xử lý lỗi kết nối
│       └── App.jsx              # đăng nhập và khung điều hướng
├── docs/
│   └── KIEN_TRUC_VA_HUONG_DAN.md
└── README-WEB.md                # hướng dẫn chạy nhanh
```

## 4. Mô hình dữ liệu

```mermaid
erDiagram
    USER ||--o{ LOAN : creates
    READER ||--o{ LOAN : has
    LOAN ||--|{ LOAN_ITEM : includes
    BOOK_TITLE ||--o{ BOOK_COPY : owns
    BOOK_COPY ||--o{ LOAN_ITEM : appears_in
    CATEGORY ||--o{ BOOK_TITLE : classifies
    PUBLISHER ||--o{ BOOK_TITLE : publishes
    BOOK_TITLE }o--o{ AUTHOR : authored_by
    READER ||--o{ PAYMENT : pays
    SUPPLIER ||--o{ ACQUISITION : supplies
    ACQUISITION ||--|{ ACQUISITION_ITEM : includes
    BOOK_TITLE ||--o{ ACQUISITION_ITEM : received
```

Điểm thiết kế quan trọng:

- `book_titles` là **đầu sách**; `book_copies` là **từng cuốn vật lý** với mã vạch và vị trí kệ. Không ghi một con số tồn kho dễ sai.
- `loans` là **phiếu mượn**; `loan_items` là từng cuốn trên phiếu. Một bạn đọc có thể mượn nhiều cuốn trong cùng một giao dịch.
- Phạt được ghi trên `loan_items`, tổng nợ hiện tại nằm trên `readers.balance`; `payments` là chứng từ thu tiền.
- `system_settings` giúp thay đổi hạn mượn, mức phạt, số sách tối đa mà không sửa mã nguồn.
- Báo cáo được tính từ giao dịch, không tạo bảng báo cáo dư thừa.

## 5. Quy tắc nghiệp vụ đã áp dụng

1. Chỉ `admin` và `librarian` được dùng nghiệp vụ thư viện; chỉ `admin` quản lý tài khoản và quy định.
2. Mật khẩu được hash bằng Argon2 qua `pwdlib`; database không bao giờ lưu mật khẩu gốc.
3. Mượn sách yêu cầu: thẻ hoạt động, chưa hết hạn, số cuốn mượn chưa vượt quy định và mọi bản sao phải `available`.
4. Một bản sao đổi sang `on_loan` ngay khi lập phiếu; trả xong sẽ đổi về `available`.
5. Trả trễ tính `số ngày trễ × fine_per_day` và cộng vào công nợ bạn đọc.
6. Không gia hạn phiếu đã quá hạn; số lần gia hạn bị giới hạn bởi `max_renewals`.
7. Phiếu nhập tạo bản sao kho tương ứng; nếu không cấp mã vạch, hệ thống tự sinh mã theo số phiếu nhập.
8. Không thể khóa hoặc hạ quyền admin đang hoạt động cuối cùng.

## 6. Các màn hình web

| Màn hình | Công việc chính |
|---|---|
| Tổng quan | đầu sách, tồn kho, bạn đọc, phiếu mở, quá hạn, công nợ |
| Sách & kho | tìm kiếm; tạo danh mục, đầu sách và từng cuốn/mã vạch |
| Bạn đọc & thu tiền | tạo thẻ, theo dõi hạn thẻ/công nợ, lập phiếu thu |
| Mượn / trả | lập phiếu nhiều cuốn, nhận trả từng cuốn, gia hạn |
| Nhập sách | nhà cung cấp, phiếu nhập, tạo cuốn tự động |
| Báo cáo | quá hạn, sách được mượn nhiều, lượt mượn theo thể loại |
| Quản trị | tài khoản nội bộ và quy định mượn/trả |

## 7. API theo module

Swagger tự sinh ở `http://localhost:8000/docs` sau khi backend chạy.

| Prefix | Mục đích |
|---|---|
| `/api/auth` | tạo admin đầu tiên, đăng nhập, tài khoản hiện tại |
| `/api/users` | CRUD người dùng nội bộ |
| `/api/catalog` | danh mục, đầu sách, cuốn sách, kho |
| `/api/readers` | bạn đọc, loại bạn đọc, phiếu thu, lịch sử mượn |
| `/api/loans` | checkout, return, renew, danh sách phiếu |
| `/api/acquisitions` | nhà cung cấp và phiếu nhập |
| `/api/settings` | quy định thư viện |
| `/api/reports` | dashboard, trả trễ, phổ biến, theo thể loại |

## 8. Chạy local

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Sau đó kiểm tra `http://localhost:8000/docs` hoặc `http://localhost:8000/health`. Nếu chưa có cấu hình riêng, hệ thống tự dùng SQLite tại `backend/library.db` và tự tạo bảng khi khởi động.

Nếu muốn dùng PostgreSQL, tạo `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://library_user:library_password@localhost:5432/library_db
SECRET_KEY=doi-khoa-bi-mat-khi-trien-khai
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Mở `http://localhost:5173`. Lần đầu bấm **Chưa có tài khoản? Tạo admin đầu tiên**. Endpoint này bị khóa ngay khi hệ thống đã có người dùng.

## 9. Cách làm migration đúng

Sau khi sửa `models.py`:

```powershell
cd backend
alembic revision --autogenerate -m "mo ta thay doi"
alembic upgrade head
```

Không sửa database bằng tay trên từng máy. Commit file trong `backend/alembic/versions/` cùng source; thành viên khác chỉ cần pull code rồi chạy `alembic upgrade head`.

## 10. Kịch bản test/demo nên trình bày

1. Tạo admin, đăng nhập, tạo thủ thư.
2. Tạo thể loại/tác giả/đầu sách, nhập thêm 3 cuốn và kiểm tra mã vạch.
3. Tạo bạn đọc còn hạn; lập phiếu mượn 2 cuốn.
4. Thử mượn lại cuốn đã `on_loan` để chứng minh hệ thống từ chối.
5. Gia hạn một phiếu hợp lệ; thử gia hạn quá số lần cho phép.
6. Trả một cuốn trễ với ngày trả tùy chọn để kiểm tra tiền phạt/công nợ.
7. Lập phiếu thu và kiểm tra công nợ giảm.
8. Mở báo cáo quá hạn, sách phổ biến và thống kê theo thể loại.

## 11. Phân công nhóm gợi ý

- **Thành viên 1:** ERD, Alembic, auth/users/settings.
- **Thành viên 2:** catalog, kho, nhập sách và nhà cung cấp.
- **Thành viên 3:** bạn đọc, mượn/trả/gia hạn/phạt/thu tiền.
- **Thành viên 4:** React layout, dashboard/báo cáo, kiểm thử tích hợp, tài liệu/slide.

Mỗi feature chỉ hoàn thành khi có migration, API validation, quyền truy cập, màn hình dùng được, dữ liệu demo và test ít nhất một trường hợp thành công + một trường hợp bị từ chối.
