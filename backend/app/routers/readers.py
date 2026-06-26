from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession, StaffUser
from app.models import CardRequest, CardRequestStatus, Loan, LoanItem, Payment, Reader, ReaderType, UserRole
from app.schemas import (
    CardRequestCreate,
    CardRequestDecision,
    CardRequestOut,
    LoanOut,
    LookupCreate,
    LookupOut,
    PaymentCreate,
    PaymentOut,
    ReaderCreate,
    ReaderOut,
    ReaderUpdate,
)
from app.services import ensure_default_settings, get_int_setting

router = APIRouter(prefix="/readers", tags=["Readers & payments"])


def _reader_for_user(db: DbSession, user: CurrentUser) -> Reader:
    reader = db.scalar(select(Reader).where(Reader.email == user.email))
    if not reader:
        raise HTTPException(status_code=404, detail="Tài khoản này chưa gắn với thẻ bạn đọc")
    return reader


def _loan_history_statement(reader_id: int):
    return (
        select(Loan)
        .options(selectinload(Loan.reader), selectinload(Loan.items).selectinload(LoanItem.book_copy))
        .where(Loan.reader_id == reader_id)
        .order_by(Loan.loaned_at.desc())
    )


def _next_card_number(db: DbSession) -> str:
    next_number = (db.scalar(select(func.count()).select_from(Reader)) or 0) + 1
    card_number = f"DG-{next_number:04}"
    while db.scalar(select(Reader).where(Reader.card_number == card_number)):
        next_number += 1
        card_number = f"DG-{next_number:04}"
    return card_number


@router.get("/me", response_model=ReaderOut)
def my_reader_profile(db: DbSession, user: CurrentUser):
    return _reader_for_user(db, user)


@router.get("/me/loans", response_model=list[LoanOut])
def my_loan_history(db: DbSession, user: CurrentUser):
    reader = _reader_for_user(db, user)
    return db.scalars(_loan_history_statement(reader.id)).all()


@router.get("/me/payments", response_model=list[PaymentOut])
def my_payments(db: DbSession, user: CurrentUser):
    reader = _reader_for_user(db, user)
    return db.scalars(select(Payment).where(Payment.reader_id == reader.id).order_by(Payment.paid_at.desc())).all()


@router.get("/me/card-request", response_model=CardRequestOut | None)
def my_card_request(db: DbSession, user: CurrentUser):
    return db.scalar(select(CardRequest).where(CardRequest.user_id == user.id).order_by(CardRequest.requested_at.desc()))


@router.post("/me/card-request", response_model=CardRequestOut, status_code=status.HTTP_201_CREATED)
def request_my_reader_card(payload: CardRequestCreate, db: DbSession, user: CurrentUser):
    if user.role != UserRole.READER:
        raise HTTPException(status_code=403, detail="Chỉ tài khoản bạn đọc được đăng ký thẻ đọc")
    if db.scalar(select(Reader).where(Reader.email == user.email)):
        raise HTTPException(status_code=409, detail="Tài khoản này đã có thẻ đọc")
    pending = db.scalar(select(CardRequest).where(CardRequest.user_id == user.id, CardRequest.status == CardRequestStatus.PENDING))
    if pending:
        raise HTTPException(status_code=409, detail="Bạn đã có yêu cầu cấp thẻ đang chờ thủ thư duyệt")
    if payload.reader_type_id and not db.get(ReaderType, payload.reader_type_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy loại bạn đọc")

    request_item = CardRequest(
        user_id=user.id,
        full_name=payload.full_name.strip(),
        email=user.email,
        phone=payload.phone.strip(),
        address=payload.address.strip(),
        date_of_birth=payload.date_of_birth,
        reader_type_id=payload.reader_type_id,
    )
    db.add(request_item)
    db.commit()
    db.refresh(request_item)
    return request_item


@router.post("/me/card", response_model=CardRequestOut, status_code=status.HTTP_201_CREATED)
def register_my_reader_card(payload: CardRequestCreate, db: DbSession, user: CurrentUser):
    return request_my_reader_card(payload, db, user)


@router.get("/types", response_model=list[LookupOut])
def list_reader_types(db: DbSession):
    return db.scalars(select(ReaderType).order_by(ReaderType.name)).all()


@router.post("/types", response_model=LookupOut, status_code=status.HTTP_201_CREATED)
def create_reader_type(payload: LookupCreate, db: DbSession, _: StaffUser):
    name = payload.name.strip()
    if db.scalar(select(ReaderType).where(ReaderType.name == name)):
        raise HTTPException(status_code=409, detail="Loại bạn đọc đã tồn tại")
    item = ReaderType(name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/types/{type_id}", response_model=LookupOut)
def update_reader_type(type_id: int, payload: LookupCreate, db: DbSession, _: StaffUser):
    item = db.get(ReaderType, type_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại bạn đọc")
    item.name = payload.name.strip()
    db.commit()
    db.refresh(item)
    return item


@router.get("/card-requests", response_model=list[CardRequestOut])
def list_card_requests(db: DbSession, _: StaffUser, request_status: CardRequestStatus | None = None):
    statement = select(CardRequest).order_by(CardRequest.requested_at.desc())
    if request_status:
        statement = statement.where(CardRequest.status == request_status)
    return db.scalars(statement).all()


@router.post("/card-requests/{request_id}/approve", response_model=ReaderOut)
def approve_card_request(request_id: int, payload: CardRequestDecision, db: DbSession, user: StaffUser):
    request_item = db.get(CardRequest, request_id)
    if not request_item:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu cấp thẻ")
    if request_item.status != CardRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Yêu cầu này đã được xử lý")
    if db.scalar(select(Reader).where(Reader.email == request_item.email)):
        raise HTTPException(status_code=409, detail="Email này đã có thẻ bạn đọc")

    ensure_default_settings(db)
    validity_months = get_int_setting(db, "card_validity_months", 12)
    reader = Reader(
        card_number=_next_card_number(db),
        full_name=request_item.full_name,
        email=request_item.email,
        phone=request_item.phone,
        address=request_item.address,
        date_of_birth=request_item.date_of_birth,
        expires_at=date.today() + timedelta(days=validity_months * 30),
        reader_type_id=request_item.reader_type_id,
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(reader)
    db.flush()
    request_item.status = CardRequestStatus.APPROVED
    request_item.note = payload.note
    request_item.decided_at = now
    request_item.decided_by_id = user.id
    request_item.reader_id = reader.id
    db.commit()
    db.refresh(reader)
    return reader


@router.post("/card-requests/{request_id}/reject", response_model=CardRequestOut)
def reject_card_request(request_id: int, payload: CardRequestDecision, db: DbSession, user: StaffUser):
    request_item = db.get(CardRequest, request_id)
    if not request_item:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu cấp thẻ")
    if request_item.status != CardRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Yêu cầu này đã được xử lý")
    request_item.status = CardRequestStatus.REJECTED
    request_item.note = payload.note
    request_item.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    request_item.decided_by_id = user.id
    db.commit()
    db.refresh(request_item)
    return request_item


@router.get("", response_model=list[ReaderOut])
def list_readers(db: DbSession, search: str | None = Query(default=None, max_length=100)):
    statement = select(Reader).order_by(Reader.full_name)
    if search:
        needle = f"%{search.strip()}%"
        statement = statement.where(or_(Reader.full_name.ilike(needle), Reader.card_number.ilike(needle), Reader.email.ilike(needle)))
    return db.scalars(statement).all()


@router.get("/{reader_id}", response_model=ReaderOut)
def get_reader(reader_id: int, db: DbSession):
    reader = db.get(Reader, reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn đọc")
    return reader


@router.post("", response_model=ReaderOut, status_code=status.HTTP_201_CREATED)
def create_reader(payload: ReaderCreate, db: DbSession, _: StaffUser):
    if payload.expires_at < date.today():
        raise HTTPException(status_code=422, detail="Hạn thẻ phải ở hiện tại hoặc tương lai")
    card_number = payload.card_number.strip()
    if db.scalar(select(Reader).where(Reader.card_number == card_number)):
        raise HTTPException(status_code=409, detail="Mã thẻ đã tồn tại")
    if payload.reader_type_id and not db.get(ReaderType, payload.reader_type_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy loại bạn đọc")
    reader_data = payload.model_dump(exclude_none=True)
    reader_data["card_number"] = card_number
    reader_data["full_name"] = payload.full_name.strip()
    reader = Reader(**reader_data)
    db.add(reader)
    db.commit()
    db.refresh(reader)
    return reader


@router.put("/{reader_id}", response_model=ReaderOut)
def update_reader(reader_id: int, payload: ReaderUpdate, db: DbSession, _: StaffUser):
    reader = db.get(Reader, reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn đọc")
    if payload.reader_type_id and not db.get(ReaderType, payload.reader_type_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy loại bạn đọc")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(reader, key, value.strip() if key == "full_name" and value else value)
    db.commit()
    db.refresh(reader)
    return reader


@router.get("/{reader_id}/payments", response_model=list[PaymentOut])
def reader_payments(reader_id: int, db: DbSession, _: StaffUser):
    if not db.get(Reader, reader_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn đọc")
    return db.scalars(select(Payment).where(Payment.reader_id == reader_id).order_by(Payment.paid_at.desc())).all()


@router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: DbSession, user: StaffUser):
    reader = db.get(Reader, payload.reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn đọc")
    if payload.amount > reader.balance:
        raise HTTPException(status_code=422, detail="Số tiền thu không được vượt công nợ hiện tại")
    reader.balance -= payload.amount
    payment = Payment(**payload.model_dump(), received_by_id=user.id)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/{reader_id}/loans", response_model=list[LoanOut])
def reader_loan_history(reader_id: int, db: DbSession, _: StaffUser):
    if not db.get(Reader, reader_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn đọc")
    return db.scalars(_loan_history_statement(reader_id)).all()
