from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession, StaffUser
from app.models import Acquisition, AcquisitionItem, BookCopy, BookTitle, Supplier
from app.schemas import AcquisitionCreate, AcquisitionOut, SupplierCreate, SupplierOut

router = APIRouter(prefix="/acquisitions", tags=["Acquisitions"])


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: DbSession):
    return db.scalars(select(Supplier).order_by(Supplier.name)).all()


@router.post("/suppliers", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: DbSession, _: StaffUser):
    if db.scalar(select(Supplier).where(Supplier.name == payload.name.strip())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nhà cung cấp đã tồn tại")
    supplier_data = payload.model_dump(exclude_none=True)
    supplier_data["name"] = payload.name.strip()
    supplier = Supplier(**supplier_data)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierCreate, db: DbSession, _: StaffUser):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp")
    for key, value in payload.model_dump().items():
        setattr(supplier, key, value.strip() if key == "name" else value)
    db.commit()
    db.refresh(supplier)
    return supplier


def _acquisition_query():
    return select(Acquisition).options(selectinload(Acquisition.items))


@router.get("", response_model=list[AcquisitionOut])
def list_acquisitions(db: DbSession):
    return db.scalars(_acquisition_query().order_by(Acquisition.received_at.desc())).all()


@router.post("", response_model=AcquisitionOut, status_code=status.HTTP_201_CREATED)
def create_acquisition(payload: AcquisitionCreate, db: DbSession, user: StaffUser):
    if not db.get(Supplier, payload.supplier_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp")
    book_ids = [item.book_title_id for item in payload.items]
    if len(book_ids) != len(set(book_ids)):
        raise HTTPException(status_code=422, detail="Mỗi đầu sách chỉ nên xuất hiện một lần trong phiếu nhập")
    books = {book.id: book for book in db.scalars(select(BookTitle).where(BookTitle.id.in_(book_ids))).all()}
    if len(books) != len(book_ids):
        raise HTTPException(status_code=404, detail="Có đầu sách không tồn tại")
    barcodes = [code.strip() for item in payload.items for code in item.barcodes]
    if len(barcodes) != len(set(barcodes)):
        raise HTTPException(status_code=409, detail="Mã vạch bị trùng trong phiếu nhập")
    if barcodes and db.scalar(select(BookCopy).where(BookCopy.barcode.in_(barcodes))):
        raise HTTPException(status_code=409, detail="Có mã vạch đã tồn tại")
    for item in payload.items:
        if item.barcodes and len(item.barcodes) != item.quantity:
            raise HTTPException(status_code=422, detail="Số mã vạch phải bằng số lượng nhập")
    received_at = (payload.received_at or datetime.now(timezone.utc)).replace(tzinfo=None)
    acquisition = Acquisition(supplier_id=payload.supplier_id, received_at=received_at, note=payload.note, created_by_id=user.id)
    db.add(acquisition)
    db.flush()
    total = 0
    for line_index, item in enumerate(payload.items, start=1):
        db.add(AcquisitionItem(acquisition=acquisition, book_title=books[item.book_title_id], quantity=item.quantity, unit_price=item.unit_price))
        total += item.quantity * item.unit_price
        codes = item.barcodes or [f"ACQ-{acquisition.id:06}-{line_index:02}-{number:03}" for number in range(1, item.quantity + 1)]
        for barcode in codes:
            db.add(BookCopy(book_title=books[item.book_title_id], barcode=barcode.strip(), shelf_location=item.shelf_location, acquired_at=received_at.date()))
    acquisition.total_amount = total
    db.commit()
    return db.scalar(_acquisition_query().where(Acquisition.id == acquisition.id))
