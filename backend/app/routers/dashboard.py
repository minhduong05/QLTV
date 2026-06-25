from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import DbSession, StaffUser
from app.models import BookCopy, BookTitle, Category, CopyStatus, Loan, LoanItem, LoanStatus, Reader
from app.schemas import CategoryBorrowOut, DashboardOut, OverdueItemOut, PopularBookOut

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/overview", response_model=DashboardOut)
def overview(db: DbSession, _: StaffUser):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return DashboardOut(
        titles=db.scalar(select(func.count()).select_from(BookTitle).where(BookTitle.is_active.is_(True))) or 0,
        available_copies=db.scalar(select(func.count()).select_from(BookCopy).where(BookCopy.status == CopyStatus.AVAILABLE)) or 0,
        active_readers=db.scalar(select(func.count()).select_from(Reader).where(Reader.is_active.is_(True))) or 0,
        open_loans=db.scalar(select(func.count()).select_from(Loan).where(Loan.status == LoanStatus.OPEN)) or 0,
        overdue_items=db.scalar(
            select(func.count()).select_from(LoanItem).join(Loan).where(LoanItem.returned_at.is_(None), Loan.due_at < now)
        ) or 0,
        unpaid_fines=db.scalar(select(func.coalesce(func.sum(Reader.balance), 0))) or 0,
    )


@router.get("/overdue", response_model=list[OverdueItemOut])
def overdue_items(db: DbSession, _: StaffUser):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = db.execute(
        select(Loan, LoanItem, Reader, BookCopy, BookTitle)
        .join(LoanItem, LoanItem.loan_id == Loan.id)
        .join(Reader, Reader.id == Loan.reader_id)
        .join(BookCopy, BookCopy.id == LoanItem.book_copy_id)
        .join(BookTitle, BookTitle.id == BookCopy.book_title_id)
        .where(LoanItem.returned_at.is_(None), Loan.due_at < now)
        .order_by(Loan.due_at)
    ).all()
    return [
        OverdueItemOut(
            loan_id=loan.id,
            reader_name=reader.full_name,
            card_number=reader.card_number,
            barcode=copy.barcode,
            title=title.title,
            due_at=loan.due_at,
            overdue_days=(now.date() - loan.due_at.date()).days,
        )
        for loan, _item, reader, copy, title in rows
    ]


@router.get("/popular-books", response_model=list[PopularBookOut])
def popular_books(db: DbSession, _: StaffUser, limit: int = 10):
    rows = db.execute(
        select(BookTitle.id, BookTitle.title, func.count(LoanItem.id).label("borrow_count"))
        .join(BookCopy, BookCopy.book_title_id == BookTitle.id)
        .join(LoanItem, LoanItem.book_copy_id == BookCopy.id)
        .group_by(BookTitle.id, BookTitle.title)
        .order_by(func.count(LoanItem.id).desc(), BookTitle.title)
        .limit(max(1, min(limit, 50)))
    ).all()
    return [PopularBookOut(book_title_id=row.id, title=row.title, borrow_count=row.borrow_count) for row in rows]


@router.get("/borrow-by-category", response_model=list[CategoryBorrowOut])
def borrow_by_category(db: DbSession, _: StaffUser):
    rows = db.execute(
        select(Category.name, func.count(LoanItem.id).label("borrow_count"))
        .join(BookTitle, BookTitle.category_id == Category.id)
        .join(BookCopy, BookCopy.book_title_id == BookTitle.id)
        .join(LoanItem, LoanItem.book_copy_id == BookCopy.id)
        .group_by(Category.name)
        .order_by(func.count(LoanItem.id).desc(), Category.name)
    ).all()
    return [CategoryBorrowOut(category=row.name, borrow_count=row.borrow_count) for row in rows]
