from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import BorrowRequestStatus, BorrowTicketItemStatus, BorrowTicketStatus, CardRequestStatus, CopyStatus, LoanStatus, UserRole


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(APIModel):
    access_token: str
    token_type: str = "bearer"


class SetupStatus(BaseModel):
    has_admin: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class BootstrapRequest(LoginRequest):
    full_name: str = Field(min_length=2, max_length=120)


class UserCreate(BootstrapRequest):
    role: UserRole = UserRole.LIBRARIAN


class ReaderRegisterRequest(BootstrapRequest):
    pass


class ReaderCardRegisterRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=30)
    address: str = Field(min_length=5, max_length=300)
    date_of_birth: date
    reader_type_id: int | None = None


class CardRequestCreate(ReaderCardRegisterRequest):
    pass


class CardRequestDecision(BaseModel):
    note: str | None = Field(default=None, max_length=300)


class CardRequestOut(APIModel):
    id: int
    user_id: int
    full_name: str
    email: EmailStr
    phone: str
    address: str
    date_of_birth: date
    reader_type_id: int | None
    requested_at: datetime
    status: CardRequestStatus
    note: str | None
    decided_at: datetime | None
    reader_id: int | None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(APIModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class LookupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class LookupUpdate(LookupCreate):
    pass


class LookupOut(APIModel):
    id: int
    name: str


class BookTitleCreate(BaseModel):
    isbn: str | None = Field(default=None, max_length=20)
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    publication_year: int | None = Field(default=None, ge=1000, le=2100)
    edition: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, max_length=60)
    image_url: str | None = Field(default=None, max_length=500)
    category_id: int
    publisher_id: int | None = None
    author_ids: list[int] = Field(default_factory=list)


class BookTitleUpdate(BookTitleCreate):
    is_active: bool = True


class BookCopyCreate(BaseModel):
    barcode: str = Field(min_length=1, max_length=50)
    shelf_location: str | None = Field(default=None, max_length=80)
    acquired_at: date | None = None
    condition_note: str | None = Field(default=None, max_length=300)


class BookCopyOut(APIModel):
    id: int
    barcode: str
    shelf_location: str | None
    status: CopyStatus
    acquired_at: date | None
    condition_note: str | None


class BookTitleOut(APIModel):
    id: int
    isbn: str | None
    title: str
    description: str | None
    publication_year: int | None
    edition: str | None
    language: str | None
    image_url: str | None
    is_active: bool
    category: LookupOut
    publisher: LookupOut | None
    authors: list[LookupOut]
    copies: list[BookCopyOut]


class ReaderCreate(BaseModel):
    card_number: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=300)
    date_of_birth: date | None = None
    expires_at: date
    reader_type_id: int | None = None


class ReaderUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=300)
    date_of_birth: date | None = None
    expires_at: date | None = None
    reader_type_id: int | None = None
    is_active: bool | None = None


class ReaderOut(APIModel):
    id: int
    card_number: str
    full_name: str
    email: EmailStr | None
    phone: str | None
    address: str | None
    date_of_birth: date | None
    registered_at: datetime
    expires_at: date
    balance: int
    is_active: bool


class CheckoutRequest(BaseModel):
    reader_id: int
    book_copy_ids: list[int] = Field(min_length=1, max_length=10)


class ReaderBorrowRequest(BaseModel):
    book_title_id: int
    note: str | None = Field(default=None, max_length=300)


class BorrowRequestDecision(BaseModel):
    note: str | None = Field(default=None, max_length=300)


class BorrowRequestOut(BaseModel):
    id: int
    reader_id: int
    reader_name: str
    card_number: str
    book_title_id: int
    title: str
    available_copies: int
    requested_at: datetime
    status: BorrowRequestStatus
    note: str | None
    decided_at: datetime | None
    loan_id: int | None


class BorrowTicketItemCreate(BaseModel):
    book_title_id: int
    quantity: int = Field(default=1, ge=1, le=1)


class BorrowTicketCreate(BaseModel):
    items: list[BorrowTicketItemCreate] = Field(min_length=1, max_length=10)
    note: str | None = Field(default=None, max_length=500)


class BorrowTicketUpdate(BorrowTicketCreate):
    pass


class BorrowTicketDecision(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class BorrowTicketItemOut(APIModel):
    id: int
    book_title_id: int
    title: str
    requested_quantity: int
    approved_quantity: int
    available_copies: int
    status: BorrowTicketItemStatus
    unavailable_reason: str | None
    reserved_copy_id: int | None
    reserved_barcode: str | None


class BorrowTicketOut(APIModel):
    id: int
    reader_id: int
    reader_name: str
    card_number: str
    requested_at: datetime
    status: BorrowTicketStatus
    note: str | None
    staff_note: str | None
    decided_at: datetime | None
    loan_id: int | None
    items: list[BorrowTicketItemOut]


class ReturnRequest(BaseModel):
    returned_at: datetime | None = None
    condition_note: str | None = Field(default=None, max_length=300)


class LoanItemOut(APIModel):
    id: int
    returned_at: datetime | None
    fine_amount: int
    book_copy: BookCopyOut


class LoanOut(APIModel):
    id: int
    loaned_at: datetime
    due_at: datetime
    status: LoanStatus
    renewal_count: int
    reader: ReaderOut
    items: list[LoanItemOut]


class PaymentCreate(BaseModel):
    reader_id: int
    amount: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=300)


class PaymentOut(APIModel):
    id: int
    reader_id: int
    amount: int
    paid_at: datetime
    note: str | None


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=300)


class SupplierOut(APIModel):
    id: int
    name: str
    phone: str | None
    email: EmailStr | None
    address: str | None


class AcquisitionItemCreate(BaseModel):
    book_title_id: int
    quantity: int = Field(ge=1, le=500)
    unit_price: int = Field(ge=0)
    shelf_location: str | None = Field(default=None, max_length=80)
    barcodes: list[str] = Field(default_factory=list)


class AcquisitionCreate(BaseModel):
    supplier_id: int
    received_at: datetime | None = None
    note: str | None = Field(default=None, max_length=300)
    items: list[AcquisitionItemCreate] = Field(min_length=1)


class AcquisitionItemOut(APIModel):
    id: int
    book_title_id: int
    quantity: int
    unit_price: int


class AcquisitionOut(APIModel):
    id: int
    supplier_id: int
    received_at: datetime
    total_amount: int
    note: str | None
    items: list[AcquisitionItemOut]


class SettingUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=300)


class SettingOut(APIModel):
    key: str
    value: str
    description: str | None


class DashboardOut(BaseModel):
    titles: int
    available_copies: int
    active_readers: int
    open_loans: int
    overdue_items: int
    unpaid_fines: int


class PopularBookOut(BaseModel):
    book_title_id: int
    title: str
    borrow_count: int


class CategoryBorrowOut(BaseModel):
    category: str
    borrow_count: int


class OverdueItemOut(BaseModel):
    loan_id: int
    reader_name: str
    card_number: str
    barcode: str
    title: str
    due_at: datetime
    overdue_days: int
