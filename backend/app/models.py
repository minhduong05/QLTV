import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    READER = "reader"


class CopyStatus(str, enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ON_LOAN = "on_loan"
    LOST = "lost"
    DAMAGED = "damaged"
    RETIRED = "retired"


class LoanStatus(str, enum.Enum):
    OPEN = "open"
    COMPLETED = "completed"


class BorrowRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class CardRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class BorrowTicketStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED_WAITING_PICKUP = "approved_waiting_pickup"
    BORROWED = "borrowed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class BorrowTicketItemStatus(str, enum.Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RESERVED = "reserved"
    SKIPPED = "skipped"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.LIBRARIAN)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    titles: Mapped[list["BookTitle"]] = relationship(back_populates="category")


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    titles: Mapped[list["BookTitle"]] = relationship(secondary="book_title_authors", back_populates="authors")


class Publisher(Base):
    __tablename__ = "publishers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    titles: Mapped[list["BookTitle"]] = relationship(back_populates="publisher")


class BookTitleAuthor(Base):
    __tablename__ = "book_title_authors"
    book_title_id: Mapped[int] = mapped_column(ForeignKey("book_titles.id", ondelete="CASCADE"), primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)


class BookTitle(Base):
    __tablename__ = "book_titles"
    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    edition: Mapped[str | None] = mapped_column(String(80), nullable=True)
    language: Mapped[str | None] = mapped_column(String(60), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    publisher_id: Mapped[int | None] = mapped_column(ForeignKey("publishers.id"), nullable=True)
    category: Mapped[Category] = relationship(back_populates="titles")
    publisher: Mapped[Publisher | None] = relationship(back_populates="titles")
    authors: Mapped[list[Author]] = relationship(secondary="book_title_authors", back_populates="titles")
    copies: Mapped[list["BookCopy"]] = relationship(back_populates="book_title", cascade="all, delete-orphan")
    borrow_requests: Mapped[list["BorrowRequest"]] = relationship(back_populates="book_title")
    borrow_ticket_items: Mapped[list["BorrowTicketItem"]] = relationship(back_populates="book_title")


class BookCopy(Base):
    __tablename__ = "book_copies"
    id: Mapped[int] = mapped_column(primary_key=True)
    barcode: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    book_title_id: Mapped[int] = mapped_column(ForeignKey("book_titles.id"), index=True)
    shelf_location: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[CopyStatus] = mapped_column(Enum(CopyStatus), default=CopyStatus.AVAILABLE)
    acquired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    condition_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    book_title: Mapped[BookTitle] = relationship(back_populates="copies")
    loan_items: Mapped[list["LoanItem"]] = relationship(back_populates="book_copy")
    ticket_reservations: Mapped[list["BorrowTicketReservation"]] = relationship(back_populates="book_copy")


class ReaderType(Base):
    __tablename__ = "reader_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    readers: Mapped[list["Reader"]] = relationship(back_populates="reader_type")


class Reader(Base):
    __tablename__ = "readers"
    id: Mapped[int] = mapped_column(primary_key=True)
    card_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    cccd: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[date] = mapped_column(Date)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reader_type_id: Mapped[int | None] = mapped_column(ForeignKey("reader_types.id"), nullable=True)
    reader_type: Mapped[ReaderType | None] = relationship(back_populates="readers")
    loans: Mapped[list["Loan"]] = relationship(back_populates="reader")
    payments: Mapped[list["Payment"]] = relationship(back_populates="reader")
    borrow_requests: Mapped[list["BorrowRequest"]] = relationship(back_populates="reader")
    borrow_tickets: Mapped[list["BorrowTicket"]] = relationship(back_populates="reader")


class CardRequest(Base):
    __tablename__ = "card_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    cccd: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(300))
    date_of_birth: Mapped[date] = mapped_column(Date)
    reader_type_id: Mapped[int | None] = mapped_column(ForeignKey("reader_types.id"), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[CardRequestStatus] = mapped_column(Enum(CardRequestStatus), default=CardRequestStatus.PENDING)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reader_id: Mapped[int | None] = mapped_column(ForeignKey("readers.id"), nullable=True)
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reader_type: Mapped[ReaderType | None] = relationship()
    reader: Mapped[Reader | None] = relationship()


class Loan(Base):
    __tablename__ = "loans"
    id: Mapped[int] = mapped_column(primary_key=True)
    reader_id: Mapped[int] = mapped_column(ForeignKey("readers.id"), index=True)
    loaned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    loaned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    due_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.OPEN)
    renewal_count: Mapped[int] = mapped_column(Integer, default=0)
    reader: Mapped[Reader] = relationship(back_populates="loans")
    items: Mapped[list["LoanItem"]] = relationship(back_populates="loan", cascade="all, delete-orphan")


class LoanItem(Base):
    __tablename__ = "loan_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), index=True)
    # A physical copy can appear in many historical loans; circulation checks
    # ensure it only has one *open* loan at a time.
    book_copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id"), index=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fine_amount: Mapped[int] = mapped_column(Integer, default=0)
    loan: Mapped[Loan] = relationship(back_populates="items")
    book_copy: Mapped[BookCopy] = relationship(back_populates="loan_items")


class BorrowRequest(Base):
    __tablename__ = "borrow_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    reader_id: Mapped[int] = mapped_column(ForeignKey("readers.id"), index=True)
    book_title_id: Mapped[int] = mapped_column(ForeignKey("book_titles.id"), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[BorrowRequestStatus] = mapped_column(Enum(BorrowRequestStatus), default=BorrowRequestStatus.PENDING)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id"), nullable=True)
    reader: Mapped[Reader] = relationship(back_populates="borrow_requests")
    book_title: Mapped[BookTitle] = relationship(back_populates="borrow_requests")
    loan: Mapped[Loan | None] = relationship()


class BorrowTicket(Base):
    __tablename__ = "borrow_tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    reader_id: Mapped[int] = mapped_column(ForeignKey("readers.id"), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[BorrowTicketStatus] = mapped_column(Enum(BorrowTicketStatus), default=BorrowTicketStatus.PENDING_REVIEW)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    staff_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id"), nullable=True)
    reader: Mapped[Reader] = relationship(back_populates="borrow_tickets")
    items: Mapped[list["BorrowTicketItem"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    loan: Mapped[Loan | None] = relationship()


class BorrowTicketItem(Base):
    __tablename__ = "borrow_ticket_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("borrow_tickets.id", ondelete="CASCADE"), index=True)
    book_title_id: Mapped[int] = mapped_column(ForeignKey("book_titles.id"), index=True)
    requested_quantity: Mapped[int] = mapped_column(Integer, default=1)
    approved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[BorrowTicketItemStatus] = mapped_column(Enum(BorrowTicketItemStatus), default=BorrowTicketItemStatus.PENDING)
    unavailable_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    reserved_copy_id: Mapped[int | None] = mapped_column(ForeignKey("book_copies.id"), nullable=True)
    ticket: Mapped[BorrowTicket] = relationship(back_populates="items")
    book_title: Mapped[BookTitle] = relationship(back_populates="borrow_ticket_items")
    reserved_copy: Mapped[BookCopy | None] = relationship()
    reservations: Mapped[list["BorrowTicketReservation"]] = relationship(back_populates="item", cascade="all, delete-orphan")


class BorrowTicketReservation(Base):
    __tablename__ = "borrow_ticket_reservations"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_item_id: Mapped[int] = mapped_column(ForeignKey("borrow_ticket_items.id", ondelete="CASCADE"), index=True)
    book_copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id"), index=True)
    item: Mapped[BorrowTicketItem] = relationship(back_populates="reservations")
    book_copy: Mapped[BookCopy] = relationship(back_populates="ticket_reservations")


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    acquisitions: Mapped[list["Acquisition"]] = relationship(back_populates="supplier")


class Acquisition(Base):
    __tablename__ = "acquisitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    received_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    total_amount: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    supplier: Mapped[Supplier] = relationship(back_populates="acquisitions")
    items: Mapped[list["AcquisitionItem"]] = relationship(back_populates="acquisition", cascade="all, delete-orphan")


class AcquisitionItem(Base):
    __tablename__ = "acquisition_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    acquisition_id: Mapped[int] = mapped_column(ForeignKey("acquisitions.id", ondelete="CASCADE"), index=True)
    book_title_id: Mapped[int] = mapped_column(ForeignKey("book_titles.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer)
    acquisition: Mapped[Acquisition] = relationship(back_populates="items")
    book_title: Mapped[BookTitle] = relationship()


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    reader_id: Mapped[int] = mapped_column(ForeignKey("readers.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    received_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reader: Mapped[Reader] = relationship(back_populates="payments")


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
