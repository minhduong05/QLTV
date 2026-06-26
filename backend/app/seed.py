from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Acquisition,
    AcquisitionItem,
    Author,
    BookCopy,
    BookTitle,
    Category,
    CopyStatus,
    Loan,
    LoanItem,
    LoanStatus,
    Publisher,
    Reader,
    ReaderType,
    Supplier,
    User,
    UserRole,
)
from app.security import hash_password

DEMO_ACCOUNTS = {
    "admin": {"email": "admin@example.com", "password": "admin123"},
    "reader": {"email": "reader@example.com", "password": "reader123"},
}


def _get_or_create_lookup(db: Session, model, name: str):
    item = db.scalar(select(model).where(model.name == name))
    if item:
        return item
    item = model(name=name)
    db.add(item)
    db.flush()
    return item


def _ensure_user(db: Session, full_name: str, email: str, password: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.full_name = full_name
        user.role = role
        return user
    user = User(full_name=full_name, email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    return user


def _ensure_copy(db: Session, book: BookTitle, barcode: str, shelf: str, status: CopyStatus = CopyStatus.AVAILABLE) -> BookCopy:
    copy = db.scalar(select(BookCopy).where(BookCopy.barcode == barcode))
    if copy:
        copy.book_title = book
        copy.shelf_location = shelf
        return copy
    copy = BookCopy(
        book_title=book,
        barcode=barcode,
        shelf_location=shelf,
        acquired_at=date.today() - timedelta(days=45),
        status=status,
        condition_note="Tốt",
    )
    db.add(copy)
    db.flush()
    return copy


def ensure_demo_data(db: Session) -> None:
    admin = _ensure_user(db, "Quản trị viên", DEMO_ACCOUNTS["admin"]["email"], DEMO_ACCOUNTS["admin"]["password"], UserRole.ADMIN)
    _ensure_user(db, "Nguyễn Bạn Đọc", DEMO_ACCOUNTS["reader"]["email"], DEMO_ACCOUNTS["reader"]["password"], UserRole.READER)

    student_type = _get_or_create_lookup(db, ReaderType, "Sinh viên")
    _get_or_create_lookup(db, ReaderType, "Giảng viên")

    reader = db.scalar(select(Reader).where(Reader.email == DEMO_ACCOUNTS["reader"]["email"]))
    if not reader:
        reader = Reader(
            card_number="DG-0001",
            full_name="Nguyễn Bạn Đọc",
            cccd="001205000001",
            email=DEMO_ACCOUNTS["reader"]["email"],
            phone="0901234567",
            address="Số 1 Đại Cồ Việt, Hà Nội",
            date_of_birth=date(2005, 9, 15),
            expires_at=date.today() + timedelta(days=365),
            reader_type=student_type,
        )
        db.add(reader)
        db.flush()
    else:
        reader.cccd = reader.cccd or "001205000001"

    categories = {
        "technology": _get_or_create_lookup(db, Category, "Công nghệ thông tin"),
        "literature": _get_or_create_lookup(db, Category, "Văn học"),
        "science": _get_or_create_lookup(db, Category, "Khoa học"),
        "business": _get_or_create_lookup(db, Category, "Kinh tế"),
        "history": _get_or_create_lookup(db, Category, "Lịch sử"),
        "skills": _get_or_create_lookup(db, Category, "Kỹ năng"),
    }
    authors = {
        "system": _get_or_create_lookup(db, Author, "Nguyễn Văn Phân Tích"),
        "clean": _get_or_create_lookup(db, Author, "Robert C. Martin"),
        "lit": _get_or_create_lookup(db, Author, "Nguyễn Nhật Ánh"),
        "orwell": _get_or_create_lookup(db, Author, "George Orwell"),
        "harari": _get_or_create_lookup(db, Author, "Yuval Noah Harari"),
        "clear": _get_or_create_lookup(db, Author, "James Clear"),
        "martin": _get_or_create_lookup(db, Author, "Martin Fowler"),
        "kahneman": _get_or_create_lookup(db, Author, "Daniel Kahneman"),
        "hawking": _get_or_create_lookup(db, Author, "Stephen Hawking"),
        "carnegie": _get_or_create_lookup(db, Author, "Dale Carnegie"),
    }
    publishers = {
        "edu": _get_or_create_lookup(db, Publisher, "NXB Giáo dục"),
        "young": _get_or_create_lookup(db, Publisher, "NXB Trẻ"),
        "world": _get_or_create_lookup(db, Publisher, "NXB Thế Giới"),
        "knowledge": _get_or_create_lookup(db, Publisher, "NXB Tri Thức"),
        "general": _get_or_create_lookup(db, Publisher, "NXB Tổng hợp"),
    }

    books = [
        {
            "isbn": "978604000101",
            "title": "Phân tích và thiết kế hệ thống thông tin",
            "description": "Giáo trình nhập môn về khảo sát, phân tích yêu cầu và thiết kế hệ thống.",
            "publication_year": 2026,
            "category": categories["technology"],
            "publisher": publishers["edu"],
            "authors": [authors["system"]],
            "copies": [("IT-0001", "A1-01"), ("IT-0002", "A1-02"), ("IT-0003", "A1-03")],
        },
        {
            "isbn": "9780132350884",
            "title": "Clean Code",
            "description": "Các nguyên tắc viết mã nguồn dễ đọc, dễ kiểm thử và dễ bảo trì.",
            "publication_year": 2008,
            "category": categories["technology"],
            "publisher": publishers["edu"],
            "authors": [authors["clean"]],
            "copies": [("IT-0101", "A2-01"), ("IT-0102", "A2-02")],
        },
        {
            "isbn": "978604100201",
            "title": "Cho tôi xin một vé đi tuổi thơ",
            "description": "Tác phẩm văn học Việt Nam quen thuộc với bạn đọc trẻ.",
            "publication_year": 2008,
            "category": categories["literature"],
            "publisher": publishers["young"],
            "authors": [authors["lit"]],
            "copies": [("VH-0001", "B1-01"), ("VH-0002", "B1-02")],
        },
        {
            "isbn": "978604200301",
            "title": "Vũ trụ trong vỏ hạt dẻ",
            "description": "Sách phổ thông về khoa học và vũ trụ học.",
            "publication_year": 2001,
            "category": categories["science"],
            "publisher": publishers["edu"],
            "authors": [authors["hawking"]],
            "copies": [("KH-0001", "C1-01")],
        },
        # 5 đầu sách có 2 bản sao
        {
            "isbn": "9780451524935",
            "title": "1984",
            "description": "Tiểu thuyết phản địa đàng kinh điển về quyền lực và tự do.",
            "publication_year": 1949,
            "category": categories["literature"],
            "publisher": publishers["world"],
            "authors": [authors["orwell"]],
            "copies": [("VH-0101", "B2-01"), ("VH-0102", "B2-02")],
        },
        {
            "isbn": "9780062316097",
            "title": "Sapiens: Lược sử loài người",
            "description": "Tổng quan lịch sử phát triển của nhân loại.",
            "publication_year": 2011,
            "category": categories["history"],
            "publisher": publishers["knowledge"],
            "authors": [authors["harari"]],
            "copies": [("LS-0101", "D1-01"), ("LS-0102", "D1-02")],
        },
        {
            "isbn": "9780735211292",
            "title": "Atomic Habits",
            "description": "Phương pháp xây dựng thói quen nhỏ để tạo thay đổi lớn.",
            "publication_year": 2018,
            "category": categories["skills"],
            "publisher": publishers["general"],
            "authors": [authors["clear"]],
            "copies": [("KN-0101", "E1-01"), ("KN-0102", "E1-02")],
        },
        {
            "isbn": "9780201485677",
            "title": "Refactoring",
            "description": "Cải tiến thiết kế mã nguồn hiện có một cách có hệ thống.",
            "publication_year": 1999,
            "category": categories["technology"],
            "publisher": publishers["knowledge"],
            "authors": [authors["martin"]],
            "copies": [("IT-0201", "A3-01"), ("IT-0202", "A3-02")],
        },
        {
            "isbn": "9780374533557",
            "title": "Thinking, Fast and Slow",
            "description": "Những cơ chế tư duy nhanh, chậm và các thiên kiến nhận thức.",
            "publication_year": 2011,
            "category": categories["science"],
            "publisher": publishers["world"],
            "authors": [authors["kahneman"]],
            "copies": [("KH-0201", "C2-01"), ("KH-0202", "C2-02")],
        },
        # 5 đầu sách có 1 bản sao
        {
            "isbn": "9780553380163",
            "title": "A Brief History of Time",
            "description": "Lược sử thời gian và những câu hỏi lớn của vũ trụ học.",
            "publication_year": 1988,
            "category": categories["science"],
            "publisher": publishers["world"],
            "authors": [authors["hawking"]],
            "copies": [("KH-0301", "C3-01")],
        },
        {
            "isbn": "9780671027032",
            "title": "Đắc nhân tâm",
            "description": "Sách kinh điển về giao tiếp và ứng xử.",
            "publication_year": 1936,
            "category": categories["skills"],
            "publisher": publishers["general"],
            "authors": [authors["carnegie"]],
            "copies": [("KN-0201", "E2-01")],
        },
        {
            "isbn": "9786041122333",
            "title": "Mắt biếc",
            "description": "Một trong những tác phẩm nổi bật của Nguyễn Nhật Ánh.",
            "publication_year": 1990,
            "category": categories["literature"],
            "publisher": publishers["young"],
            "authors": [authors["lit"]],
            "copies": [("VH-0201", "B3-01")],
        },
        {
            "isbn": "9786043440008",
            "title": "Dế Mèn phiêu lưu ký",
            "description": "Tác phẩm thiếu nhi kinh điển của văn học Việt Nam.",
            "publication_year": 1941,
            "category": categories["literature"],
            "publisher": publishers["edu"],
            "authors": [_get_or_create_lookup(db, Author, "Tô Hoài")],
            "copies": [("VH-0301", "B3-02")],
        },
        {
            "isbn": "9780131103627",
            "title": "The C Programming Language",
            "description": "Tài liệu kinh điển về ngôn ngữ lập trình C.",
            "publication_year": 1988,
            "category": categories["technology"],
            "publisher": publishers["knowledge"],
            "authors": [_get_or_create_lookup(db, Author, "Brian W. Kernighan"), _get_or_create_lookup(db, Author, "Dennis M. Ritchie")],
            "copies": [("IT-0301", "A3-03")],
        },
        # 1 đầu sách không có bản sao
        {
            "isbn": "9780000000000",
            "title": "Sách đang chờ bổ sung bản sao",
            "description": "Đầu sách có trong danh mục nhưng chưa có bản sao vật lý để kiểm thử trường hợp hết sách.",
            "publication_year": 2026,
            "category": categories["business"],
            "publisher": publishers["general"],
            "authors": [authors["system"]],
            "copies": [],
        },
    ]

    seeded_books: list[BookTitle] = []
    for entry in books:
        book = db.scalar(select(BookTitle).where(BookTitle.isbn == entry["isbn"]))
        if not book:
            book = BookTitle(
                isbn=entry["isbn"],
                title=entry["title"],
                description=entry["description"],
                publication_year=entry["publication_year"],
                category=entry["category"],
                publisher=entry["publisher"],
                authors=entry["authors"],
                is_active=True,
            )
            db.add(book)
            db.flush()
        book.title = entry["title"]
        book.description = entry["description"]
        book.publication_year = entry["publication_year"]
        book.language = "Tiếng Anh" if entry["title"] in {"Clean Code", "1984", "Atomic Habits", "Refactoring", "Thinking, Fast and Slow", "A Brief History of Time", "The C Programming Language"} else "Tiếng Việt"
        book.category = entry["category"]
        book.publisher = entry["publisher"]
        book.authors = entry["authors"]
        book.is_active = True
        seeded_books.append(book)
        for barcode, shelf in entry["copies"]:
            _ensure_copy(db, book, barcode, shelf)

    supplier = db.scalar(select(Supplier).where(Supplier.name == "Công ty Sách Demo"))
    if not supplier:
        supplier = Supplier(name="Công ty Sách Demo", phone="02439990000", email="demo@example.com", address="Hà Nội")
        db.add(supplier)
        db.flush()

    if not db.scalar(select(Acquisition).where(Acquisition.note == "Phiếu nhập dữ liệu mẫu")):
        acquisition = Acquisition(
            supplier=supplier,
            received_at=datetime.now() - timedelta(days=30),
            total_amount=450000,
            note="Phiếu nhập dữ liệu mẫu",
            created_by_id=admin.id,
        )
        db.add(acquisition)
        db.flush()
        db.add_all(
            [
                AcquisitionItem(acquisition=acquisition, book_title=seeded_books[0], quantity=3, unit_price=90000),
                AcquisitionItem(acquisition=acquisition, book_title=seeded_books[1], quantity=2, unit_price=90000),
            ]
        )

    if reader and not db.scalar(select(Loan).where(Loan.reader_id == reader.id)):
        copy = db.scalar(select(BookCopy).where(BookCopy.barcode == "VH-0001"))
        if copy:
            loaned_at = datetime.now() - timedelta(days=20)
            loan = Loan(
                reader=reader,
                loaned_by_id=admin.id,
                loaned_at=loaned_at,
                due_at=loaned_at + timedelta(days=14),
                status=LoanStatus.COMPLETED,
            )
            db.add(loan)
            db.flush()
            db.add(LoanItem(loan=loan, book_copy=copy, returned_at=loaned_at + timedelta(days=10), fine_amount=0))

    db.commit()
