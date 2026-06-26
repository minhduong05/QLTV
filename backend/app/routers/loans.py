from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession, StaffUser
from app.models import (
    BookCopy,
    BookTitle,
    BorrowTicket,
    BorrowTicketItem,
    BorrowTicketItemStatus,
    BorrowTicketReservation,
    BorrowTicketStatus,
    CopyStatus,
    Loan,
    LoanItem,
    LoanStatus,
    Reader,
    UserRole,
)
from app.schemas import BorrowTicketCreate, BorrowTicketDecision, BorrowTicketOut, BorrowTicketUpdate, CheckoutRequest, LoanOut, ReturnRequest
from app.services import ensure_default_settings, get_int_setting

router = APIRouter(prefix="/loans", tags=["Circulation"])
settings = get_settings()


def _loan_query():
    return select(Loan).options(
        selectinload(Loan.reader),
        selectinload(Loan.items).selectinload(LoanItem.book_copy),
    )


def _ticket_query():
    return select(BorrowTicket).options(
        selectinload(BorrowTicket.reader),
        selectinload(BorrowTicket.items).selectinload(BorrowTicketItem.book_title),
        selectinload(BorrowTicket.items).selectinload(BorrowTicketItem.reserved_copy),
        selectinload(BorrowTicket.items).selectinload(BorrowTicketItem.reservations).selectinload(BorrowTicketReservation.book_copy),
    )


def _active_item_count(db: DbSession, reader_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(LoanItem).join(Loan).where(Loan.reader_id == reader_id, LoanItem.returned_at.is_(None))
    ) or 0


def _reserved_item_count(db: DbSession, reader_id: int, exclude_ticket_id: int | None = None) -> int:
    statement = (
        select(func.coalesce(func.sum(BorrowTicketItem.approved_quantity), 0))
        .select_from(BorrowTicket)
        .join(BorrowTicketItem)
        .where(BorrowTicket.reader_id == reader_id, BorrowTicket.status == BorrowTicketStatus.APPROVED_WAITING_PICKUP)
    )
    if exclude_ticket_id:
        statement = statement.where(BorrowTicket.id != exclude_ticket_id)
    return db.scalar(statement) or 0


def _available_count(db: DbSession, book_title_id: int) -> int:
    return db.scalar(select(func.count()).select_from(BookCopy).where(BookCopy.book_title_id == book_title_id, BookCopy.status == CopyStatus.AVAILABLE)) or 0


def _reader_for_user(db: DbSession, user: CurrentUser) -> Reader:
    reader = db.scalar(select(Reader).where(Reader.email == user.email))
    if not reader:
        raise HTTPException(status_code=404, detail="Tài khoản này chưa có thẻ bạn đọc")
    return reader


def _ensure_reader_can_borrow(db: DbSession, reader: Reader, requested_count: int, exclude_ticket_id: int | None = None) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not reader.is_active:
        raise HTTPException(status_code=409, detail="Thẻ bạn đọc đang bị khóa")
    if reader.expires_at < now.date():
        raise HTTPException(status_code=409, detail="Thẻ bạn đọc đã hết hạn")
    maximum = get_int_setting(db, "max_active_loans", settings.max_active_loans)
    active = _active_item_count(db, reader.id)
    reserved = _reserved_item_count(db, reader.id, exclude_ticket_id)
    if active + reserved + requested_count > maximum:
        raise HTTPException(status_code=409, detail=f"Bạn đọc chỉ được mượn tối đa {maximum} cuốn")


def _release_reservations(ticket: BorrowTicket) -> None:
    for item in ticket.items:
        for reservation in item.reservations:
            if reservation.book_copy.status == CopyStatus.RESERVED:
                reservation.book_copy.status = CopyStatus.AVAILABLE
        item.reservations.clear()
        if item.reserved_copy and item.reserved_copy.status == CopyStatus.RESERVED:
            item.reserved_copy.status = CopyStatus.AVAILABLE
        item.reserved_copy = None
        item.reserved_copy_id = None
        if item.status == BorrowTicketItemStatus.RESERVED:
            item.status = BorrowTicketItemStatus.AVAILABLE
        item.approved_quantity = 0


def _ticket_out(ticket: BorrowTicket, db: DbSession) -> BorrowTicketOut:
    return BorrowTicketOut(
        id=ticket.id,
        reader_id=ticket.reader_id,
        reader_name=ticket.reader.full_name,
        card_number=ticket.reader.card_number,
        requested_at=ticket.requested_at,
        status=ticket.status,
        note=ticket.note,
        staff_note=ticket.staff_note,
        decided_at=ticket.decided_at,
        loan_id=ticket.loan_id,
        items=[
            {
                "id": item.id,
                "book_title_id": item.book_title_id,
                "title": item.book_title.title,
                "requested_quantity": item.requested_quantity,
                "approved_quantity": item.approved_quantity,
                "available_copies": _available_count(db, item.book_title_id),
                "status": item.status,
                "unavailable_reason": item.unavailable_reason,
                "reserved_copy_id": item.reserved_copy_id,
                "reserved_barcode": item.reserved_copy.barcode if item.reserved_copy else None,
                "reserved_barcodes": [reservation.book_copy.barcode for reservation in item.reservations],
            }
            for item in ticket.items
        ],
    )


def _reload_ticket(db: DbSession, ticket_id: int) -> BorrowTicket:
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    return ticket


def _set_items_from_payload(db: DbSession, ticket: BorrowTicket, payload: BorrowTicketCreate) -> None:
    title_ids = [item.book_title_id for item in payload.items]
    if len(title_ids) != len(set(title_ids)):
        raise HTTPException(status_code=422, detail="Một đầu sách không được xuất hiện hai lần trong cùng phiếu")
    titles = db.scalars(select(BookTitle).where(BookTitle.id.in_(title_ids), BookTitle.is_active.is_(True))).all()
    if len(titles) != len(title_ids):
        raise HTTPException(status_code=404, detail="Có đầu sách không tồn tại hoặc đã ngừng phục vụ")
    ticket.items.clear()
    for item in payload.items:
        ticket.items.append(BorrowTicketItem(book_title_id=item.book_title_id, requested_quantity=item.quantity))


def _review_availability(ticket: BorrowTicket, db: DbSession) -> bool:
    all_available = True
    for item in ticket.items:
        available = _available_count(db, item.book_title_id)
        item.approved_quantity = 0
        item.reserved_copy = None
        item.reserved_copy_id = None
        if available >= item.requested_quantity:
            item.status = BorrowTicketItemStatus.AVAILABLE
            item.unavailable_reason = None
        else:
            item.status = BorrowTicketItemStatus.UNAVAILABLE
            item.unavailable_reason = f"Chỉ còn {available}/{item.requested_quantity} bản sao vật lý sẵn sàng"
            all_available = False
    return all_available


def _reserve_available_items(ticket: BorrowTicket, db: DbSession, *, allow_partial: bool) -> int:
    reserved_count = 0
    for item in ticket.items:
        copies = db.scalars(
            select(BookCopy)
            .where(BookCopy.book_title_id == item.book_title_id, BookCopy.status == CopyStatus.AVAILABLE)
            .order_by(BookCopy.id)
            .limit(item.requested_quantity)
            .with_for_update()
        ).all()
        if len(copies) < item.requested_quantity and not allow_partial:
            item.status = BorrowTicketItemStatus.UNAVAILABLE
            item.approved_quantity = 0
            item.unavailable_reason = f"Chỉ còn {len(copies)}/{item.requested_quantity} bản sao sẵn sàng"
            raise HTTPException(status_code=409, detail=f"Đầu sách '{item.book_title.title}' không đủ số lượng yêu cầu")
        if not copies:
            item.status = BorrowTicketItemStatus.SKIPPED if allow_partial else BorrowTicketItemStatus.UNAVAILABLE
            item.approved_quantity = 0
            item.unavailable_reason = "Không còn bản sao vật lý sẵn sàng cho mượn"
            if not allow_partial:
                raise HTTPException(status_code=409, detail=f"Đầu sách '{item.book_title.title}' hiện không còn bản sao sẵn sàng")
            continue
        for copy in copies:
            copy.status = CopyStatus.RESERVED
            item.reservations.append(BorrowTicketReservation(book_copy=copy))
        item.reserved_copy = copies[0]
        item.reserved_copy_id = copies[0].id
        item.approved_quantity = len(copies)
        item.status = BorrowTicketItemStatus.RESERVED
        item.unavailable_reason = None if len(copies) == item.requested_quantity else f"Chỉ duyệt {len(copies)}/{item.requested_quantity} bản sao còn sẵn"
        reserved_count += len(copies)
    return reserved_count


@router.get("", response_model=list[LoanOut])
def list_loans(db: DbSession, only_open: bool = False, reader_id: int | None = None):
    statement = _loan_query().order_by(Loan.loaned_at.desc())
    if only_open:
        statement = statement.where(Loan.status == LoanStatus.OPEN)
    if reader_id:
        statement = statement.where(Loan.reader_id == reader_id)
    return db.scalars(statement).all()


@router.post("/checkout", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
def checkout(payload: CheckoutRequest, db: DbSession, user: StaffUser):
    if len(payload.book_copy_ids) != len(set(payload.book_copy_ids)):
        raise HTTPException(status_code=422, detail="Một cuốn không thể xuất hiện hai lần trong phiếu")
    ensure_default_settings(db)
    reader = db.get(Reader, payload.reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn đọc")
    _ensure_reader_can_borrow(db, reader, len(payload.book_copy_ids))
    copies = db.scalars(select(BookCopy).where(BookCopy.id.in_(payload.book_copy_ids)).with_for_update()).all()
    if len(copies) != len(payload.book_copy_ids):
        raise HTTPException(status_code=404, detail="Có cuốn sách không tồn tại")
    unavailable = [copy.barcode for copy in copies if copy.status != CopyStatus.AVAILABLE]
    if unavailable:
        raise HTTPException(status_code=409, detail=f"Sách chưa sẵn sàng cho mượn: {', '.join(unavailable)}")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    loan_days = get_int_setting(db, "loan_days", settings.default_loan_days)
    loan = Loan(reader=reader, loaned_by_id=user.id, due_at=now + timedelta(days=loan_days))
    db.add(loan)
    db.flush()
    for copy in copies:
        copy.status = CopyStatus.ON_LOAN
        db.add(LoanItem(loan=loan, book_copy=copy))
    db.commit()
    return db.scalar(_loan_query().where(Loan.id == loan.id))


@router.get("/tickets", response_model=list[BorrowTicketOut])
def list_borrow_tickets(db: DbSession, _: StaffUser, ticket_status: BorrowTicketStatus | None = None):
    statement = _ticket_query().order_by(BorrowTicket.requested_at.desc())
    if ticket_status:
        statement = statement.where(BorrowTicket.status == ticket_status)
    return [_ticket_out(ticket, db) for ticket in db.scalars(statement).all()]


@router.get("/tickets/me", response_model=list[BorrowTicketOut])
def my_borrow_tickets(db: DbSession, user: CurrentUser):
    reader = _reader_for_user(db, user)
    rows = db.scalars(_ticket_query().where(BorrowTicket.reader_id == reader.id).order_by(BorrowTicket.requested_at.desc())).all()
    return [_ticket_out(ticket, db) for ticket in rows]


@router.post("/tickets", response_model=BorrowTicketOut, status_code=status.HTTP_201_CREATED)
def create_borrow_ticket(payload: BorrowTicketCreate, db: DbSession, user: CurrentUser):
    ensure_default_settings(db)
    reader = _reader_for_user(db, user)
    requested_count = sum(item.quantity for item in payload.items)
    _ensure_reader_can_borrow(db, reader, requested_count)
    ticket = BorrowTicket(reader=reader, note=payload.note, status=BorrowTicketStatus.PENDING_REVIEW)
    db.add(ticket)
    _set_items_from_payload(db, ticket, payload)
    db.commit()
    return _ticket_out(_reload_ticket(db, ticket.id), db)


@router.put("/tickets/{ticket_id}", response_model=BorrowTicketOut)
def update_borrow_ticket(ticket_id: int, payload: BorrowTicketUpdate, db: DbSession, user: CurrentUser):
    reader = _reader_for_user(db, user)
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id, BorrowTicket.reader_id == reader.id).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    if ticket.status != BorrowTicketStatus.CHANGES_REQUESTED:
        raise HTTPException(status_code=409, detail="Chỉ có thể sửa phiếu khi thủ thư yêu cầu điều chỉnh")
    _release_reservations(ticket)
    _ensure_reader_can_borrow(db, reader, sum(item.quantity for item in payload.items), exclude_ticket_id=ticket.id)
    ticket.note = payload.note
    ticket.staff_note = None
    ticket.status = BorrowTicketStatus.PENDING_REVIEW
    ticket.decided_at = None
    ticket.decided_by_id = None
    _set_items_from_payload(db, ticket, payload)
    db.commit()
    return _ticket_out(_reload_ticket(db, ticket.id), db)


@router.post("/tickets/{ticket_id}/review", response_model=BorrowTicketOut)
def review_borrow_ticket(ticket_id: int, payload: BorrowTicketDecision, db: DbSession, user: StaffUser):
    ensure_default_settings(db)
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    if ticket.status not in {BorrowTicketStatus.PENDING_REVIEW, BorrowTicketStatus.REVIEWED, BorrowTicketStatus.CHANGES_REQUESTED}:
        raise HTTPException(status_code=409, detail="Phiếu này không còn ở trạng thái chờ kiểm tra")
    _release_reservations(ticket)
    _ensure_reader_can_borrow(db, ticket.reader, sum(item.requested_quantity for item in ticket.items), exclude_ticket_id=ticket.id)
    all_available = _review_availability(ticket, db)
    ticket.staff_note = payload.note
    ticket.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    ticket.decided_by_id = user.id
    if all_available:
        ticket.status = BorrowTicketStatus.REVIEWED
        ticket.staff_note = payload.note or "Tất cả đầu sách đủ số lượng. Thủ thư có thể xem chi tiết rồi bấm duyệt để giữ chỗ."
    else:
        ticket.status = BorrowTicketStatus.CHANGES_REQUESTED
        ticket.staff_note = payload.note or "Một số đầu sách không còn bản sao. Bạn đọc có thể sửa phiếu hoặc đồng ý mượn phần còn sẵn."
    db.commit()
    return _ticket_out(_reload_ticket(db, ticket.id), db)


@router.post("/tickets/{ticket_id}/approve-available", response_model=BorrowTicketOut)
def approve_available_items(ticket_id: int, payload: BorrowTicketDecision, db: DbSession, user: CurrentUser):
    ensure_default_settings(db)
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    if user.role == UserRole.READER and ticket.reader.email != user.email:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xử lý phiếu này")
    if user.role == UserRole.READER and ticket.status != BorrowTicketStatus.CHANGES_REQUESTED:
        raise HTTPException(status_code=409, detail="Chỉ có thể xác nhận mượn phần còn sẵn sau khi thủ thư phản hồi")
    if user.role != UserRole.READER and ticket.status not in {BorrowTicketStatus.REVIEWED, BorrowTicketStatus.CHANGES_REQUESTED}:
        raise HTTPException(status_code=409, detail="Cần kiểm tra/xem chi tiết phiếu trước khi duyệt")
    _release_reservations(ticket)
    reserved_count = _reserve_available_items(ticket, db, allow_partial=True)
    if reserved_count == 0:
        raise HTTPException(status_code=409, detail="Không còn đầu sách nào có bản sao sẵn sàng để duyệt")
    _ensure_reader_can_borrow(db, ticket.reader, reserved_count, exclude_ticket_id=ticket.id)
    ticket.status = BorrowTicketStatus.APPROVED_WAITING_PICKUP
    ticket.staff_note = payload.note or "Đã duyệt các đầu sách còn bản sao, chờ bạn đọc đến thư viện nhận sách."
    ticket.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    ticket.decided_by_id = user.id
    db.commit()
    return _ticket_out(_reload_ticket(db, ticket.id), db)


@router.post("/tickets/{ticket_id}/reject", response_model=BorrowTicketOut)
def reject_borrow_ticket(ticket_id: int, payload: BorrowTicketDecision, db: DbSession, user: StaffUser):
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    if ticket.status in {BorrowTicketStatus.BORROWED, BorrowTicketStatus.CANCELLED, BorrowTicketStatus.REJECTED}:
        raise HTTPException(status_code=409, detail="Phiếu này đã kết thúc")
    _release_reservations(ticket)
    ticket.status = BorrowTicketStatus.REJECTED
    ticket.staff_note = payload.note
    ticket.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    ticket.decided_by_id = user.id
    db.commit()
    return _ticket_out(_reload_ticket(db, ticket.id), db)


@router.post("/tickets/{ticket_id}/cancel", response_model=BorrowTicketOut)
def cancel_my_borrow_ticket(ticket_id: int, db: DbSession, user: CurrentUser):
    reader = _reader_for_user(db, user)
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id, BorrowTicket.reader_id == reader.id).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    if ticket.status == BorrowTicketStatus.BORROWED:
        raise HTTPException(status_code=409, detail="Phiếu đã chuyển thành đang mượn nên không thể hủy online")
    if ticket.status in {BorrowTicketStatus.CANCELLED, BorrowTicketStatus.REJECTED}:
        raise HTTPException(status_code=409, detail="Phiếu này đã kết thúc")
    _release_reservations(ticket)
    ticket.status = BorrowTicketStatus.CANCELLED
    ticket.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return _ticket_out(_reload_ticket(db, ticket.id), db)


@router.post("/tickets/{ticket_id}/pickup", response_model=LoanOut)
def confirm_ticket_pickup(ticket_id: int, db: DbSession, user: StaffUser):
    ensure_default_settings(db)
    ticket = db.scalar(_ticket_query().where(BorrowTicket.id == ticket_id).with_for_update())
    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký mượn")
    if ticket.status != BorrowTicketStatus.APPROVED_WAITING_PICKUP:
        raise HTTPException(status_code=409, detail="Chỉ xác nhận lấy sách với phiếu đã duyệt")
    reservations = [reservation for item in ticket.items for reservation in item.reservations if item.status == BorrowTicketItemStatus.RESERVED]
    if not reservations:
        raise HTTPException(status_code=409, detail="Phiếu chưa có cuốn sách nào được giữ chỗ")
    _ensure_reader_can_borrow(db, ticket.reader, 0, exclude_ticket_id=ticket.id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    loan_days = get_int_setting(db, "loan_days", settings.default_loan_days)
    loan = Loan(reader=ticket.reader, loaned_by_id=user.id, due_at=now + timedelta(days=loan_days))
    db.add(loan)
    db.flush()
    for reservation in reservations:
        if reservation.book_copy.status != CopyStatus.RESERVED:
            raise HTTPException(status_code=409, detail=f"Cuốn {reservation.book_copy.barcode} không còn ở trạng thái giữ chỗ")
        reservation.book_copy.status = CopyStatus.ON_LOAN
        db.add(LoanItem(loan=loan, book_copy=reservation.book_copy))
    ticket.status = BorrowTicketStatus.BORROWED
    ticket.loan_id = loan.id
    ticket.decided_at = now
    ticket.decided_by_id = user.id
    db.commit()
    return db.scalar(_loan_query().where(Loan.id == loan.id))


@router.post("/{loan_id}/items/{item_id}/return", response_model=LoanOut)
def return_item(loan_id: int, item_id: int, payload: ReturnRequest, db: DbSession, _: StaffUser):
    item = db.scalar(select(LoanItem).where(LoanItem.id == item_id, LoanItem.loan_id == loan_id).with_for_update())
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy chi tiết mượn")
    if item.returned_at:
        raise HTTPException(status_code=409, detail="Cuốn này đã được trả")
    returned_at = (payload.returned_at or datetime.now(timezone.utc)).replace(tzinfo=None)
    if returned_at < item.loan.loaned_at:
        raise HTTPException(status_code=422, detail="Ngày trả không thể trước ngày mượn")
    ensure_default_settings(db)
    overdue_days = max(0, (returned_at.date() - item.loan.due_at.date()).days)
    item.returned_at = returned_at
    item.fine_amount = overdue_days * get_int_setting(db, "fine_per_day", settings.fine_per_day)
    item.book_copy.status = CopyStatus.AVAILABLE
    if payload.condition_note is not None:
        item.book_copy.condition_note = payload.condition_note
    item.loan.reader.balance += item.fine_amount
    if not any(other.id != item.id and other.returned_at is None for other in item.loan.items):
        item.loan.status = LoanStatus.COMPLETED
    db.commit()
    return db.scalar(_loan_query().where(Loan.id == loan_id))


@router.post("/{loan_id}/renew", response_model=LoanOut)
def renew_loan(loan_id: int, db: DbSession, _: StaffUser):
    ensure_default_settings(db)
    loan = db.scalar(_loan_query().where(Loan.id == loan_id).with_for_update())
    if not loan:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu mượn")
    if loan.status != LoanStatus.OPEN:
        raise HTTPException(status_code=409, detail="Chỉ có thể gia hạn phiếu đang mượn")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if loan.due_at < now:
        raise HTTPException(status_code=409, detail="Không thể gia hạn phiếu đã quá hạn")
    maximum = get_int_setting(db, "max_renewals", 1)
    if loan.renewal_count >= maximum:
        raise HTTPException(status_code=409, detail=f"Phiếu chỉ được gia hạn tối đa {maximum} lần")
    loan.due_at += timedelta(days=get_int_setting(db, "loan_days", settings.default_loan_days))
    loan.renewal_count += 1
    db.commit()
    return db.scalar(_loan_query().where(Loan.id == loan_id))
