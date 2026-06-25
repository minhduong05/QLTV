# Web Quản lý thư viện

Ứng dụng web quản lý thư viện chạy song song với source WinForms cũ. Stack: FastAPI, SQLAlchemy, SQLite/PostgreSQL, React, Vite, Tailwind, JWT và Argon2.

## Chạy local bằng uv

Mở terminal 1 để chạy backend:

```powershell
cd "D:\2025_2\Phân tích và thiết kế hệ thống thông tin\QLTV\backend"
uv run --with-requirements requirements.txt python -m uvicorn app.main:app --reload
```

Mở terminal 2 để chạy frontend:

```powershell
cd "D:\2025_2\Phân tích và thiết kế hệ thống thông tin\QLTV\frontend"
npm install
npm run dev
```

Mở `http://localhost:5173`. Swagger API ở `http://localhost:8000/docs`.

Backend mặc định dùng SQLite tại `backend/library.db`, tự tạo bảng mới khi khởi động và tự seed dữ liệu mẫu nếu còn thiếu.

## Tài khoản mẫu

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản trị viên | `admin@example.com` | `admin123` |
| Bạn đọc đã có thẻ | `reader@example.com` | `reader123` |

Admin có thể tạo thêm tài khoản thủ thư hoặc quản trị viên ở màn **Quản trị**. Bạn đọc mới tự đăng ký tài khoản ở màn đăng nhập, sau đó gửi yêu cầu cấp thẻ đọc online để thủ thư duyệt.

## Luồng chính đã có

- Bạn đọc đăng ký tài khoản, gửi yêu cầu cấp thẻ, thủ thư duyệt online rồi hệ thống tạo mã thẻ `DG-xxxx`.
- Bạn đọc có thẻ còn hạn mới được lập phiếu đăng ký mượn online.
- Phiếu đăng ký mượn có thể gồm nhiều đầu sách.
- Thủ thư kiểm tra bản sao vật lý; nếu thiếu sách, hệ thống phản hồi rõ sách nào còn, sách nào hết.
- Bạn đọc có thể sửa phiếu gửi lại hoặc đồng ý mượn phần còn sẵn.
- Khi bạn đọc đến thư viện lấy sách, thủ thư xác nhận để tạo phiếu mượn thật và chuyển bản sao từ `reserved` sang `on_loan`.
- Trả sách cập nhật bản sao về `available`, tính phạt quá hạn và cộng công nợ.
- Có thêm catalog, nhập sách, nhà cung cấp, thu tiền phạt, báo cáo và quy định mượn/trả.

Chi tiết nghiệp vụ: [docs/LUONG_NGHIEP_VU_CHI_TIET.md](docs/LUONG_NGHIEP_VU_CHI_TIET.md).
