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
        return user
    user = User(full_name=full_name, email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    return user


def _ensure_copy(db: Session, book: BookTitle, barcode: str, shelf: str, status: CopyStatus = CopyStatus.AVAILABLE) -> BookCopy:
    copy = db.scalar(select(BookCopy).where(BookCopy.barcode == barcode))
    if copy:
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
            email=DEMO_ACCOUNTS["reader"]["email"],
            phone="0901234567",
            address="Số 1 Đại Cồ Việt, Hà Nội",
            date_of_birth=date(2005, 9, 15),
            expires_at=date.today() + timedelta(days=365),
            reader_type=student_type,
        )
        db.add(reader)
        db.flush()

    technology = _get_or_create_lookup(db, Category, "Công nghệ thông tin")
    literature = _get_or_create_lookup(db, Category, "Văn học")
    science = _get_or_create_lookup(db, Category, "Khoa học")
    author_system = _get_or_create_lookup(db, Author, "Nguyễn Văn Phân Tích")
    author_clean = _get_or_create_lookup(db, Author, "Robert C. Martin")
    author_lit = _get_or_create_lookup(db, Author, "Nguyễn Nhật Ánh")
    publisher_edu = _get_or_create_lookup(db, Publisher, "NXB Giáo dục")
    publisher_young = _get_or_create_lookup(db, Publisher, "NXB Trẻ")

    books = [
        {
            "isbn": "978604000101",
            "title": "Phân tích và thiết kế hệ thống thông tin",
            "description": "Giáo trình nhập môn về khảo sát, phân tích yêu cầu và thiết kế hệ thống.",
            "publication_year": 2026,
            "category": technology,
            "publisher": publisher_edu,
            "authors": [author_system],
            "copies": [("IT-0001", "A1-01"), ("IT-0002", "A1-02"), ("IT-0003", "A1-03")],
        },
        {
            "isbn": "9780132350884",
            "title": "Clean Code",
            "description": "Các nguyên tắc viết mã nguồn dễ đọc, dễ kiểm thử và dễ bảo trì.",
            "publication_year": 2008,
            "category": technology,
            "publisher": publisher_edu,
            "authors": [author_clean],
            "copies": [("IT-0101", "A2-01"), ("IT-0102", "A2-02")],
        },
        {
            "isbn": "978604100201",
            "title": "Cho tôi xin một vé đi tuổi thơ",
            "description": "Tác phẩm văn học Việt Nam quen thuộc với bạn đọc trẻ.",
            "publication_year": 2008,
            "category": literature,
            "publisher": publisher_young,
            "authors": [author_lit],
            "copies": [("VH-0001", "B1-01"), ("VH-0002", "B1-02")],
        },
        {
            "isbn": "978604200301",
            "title": "Vũ trụ trong vỏ hạt dẻ",
            "description": "Sách phổ thông về khoa học và vũ trụ học.",
            "publication_year": 2001,
            "category": science,
            "publisher": publisher_edu,
            "authors": [author_system],
            "copies": [("KH-0001", "C1-01")],
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
                language="Tiếng Việt" if entry["title"] != "Clean Code" else "Tiếng Anh",
                category=entry["category"],
                publisher=entry["publisher"],
                authors=entry["authors"],
            )
            db.add(book)
            db.flush()
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
