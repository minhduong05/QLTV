from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.dependencies import DbSession, StaffUser
from app.models import Author, BookCopy, BookTitle, Category, CopyStatus, Publisher
from app.schemas import BookCopyCreate, BookTitleCreate, BookTitleOut, BookTitleUpdate, LookupCreate, LookupOut

router = APIRouter(prefix="/catalog", tags=["Catalog & inventory"])


def _create_lookup(model, payload: LookupCreate, db: DbSession):
    name = payload.name.strip()
    if db.scalar(select(model).where(model.name == name)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên này đã tồn tại")
    item = model(name=name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _update_lookup(model, item_id: int, payload: LookupCreate, db: DbSession):
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu")
    name = payload.name.strip()
    duplicate = db.scalar(select(model).where(model.name == name, model.id != item_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Tên này đã tồn tại")
    item.name = name
    db.commit()
    db.refresh(item)
    return item


def _list_lookup(model, db: DbSession):
    return db.scalars(select(model).order_by(model.name)).all()


def _register_lookup_routes(prefix: str, model):
    @router.get(f"/{prefix}", response_model=list[LookupOut], name=f"list_{prefix}")
    def list_items(db: DbSession):
        return _list_lookup(model, db)

    @router.post(f"/{prefix}", response_model=LookupOut, status_code=status.HTTP_201_CREATED, name=f"create_{prefix}")
    def create_item(payload: LookupCreate, db: DbSession, _: StaffUser):
        return _create_lookup(model, payload, db)

    @router.patch(f"/{prefix}/{{item_id}}", response_model=LookupOut, name=f"update_{prefix}")
    def update_item(item_id: int, payload: LookupCreate, db: DbSession, _: StaffUser):
        return _update_lookup(model, item_id, payload, db)


_register_lookup_routes("categories", Category)
_register_lookup_routes("authors", Author)
_register_lookup_routes("publishers", Publisher)


def _title_query():
    return select(BookTitle).options(
        selectinload(BookTitle.category),
        selectinload(BookTitle.publisher),
        selectinload(BookTitle.authors),
        selectinload(BookTitle.copies),
    )


def _validate_book_payload(payload: BookTitleCreate, db: DbSession, ignore_id: int | None = None):
    category = db.get(Category, payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy thể loại")
    if payload.isbn:
        statement = select(BookTitle).where(BookTitle.isbn == payload.isbn.strip())
        if ignore_id:
            statement = statement.where(BookTitle.id != ignore_id)
        if db.scalar(statement):
            raise HTTPException(status_code=409, detail="ISBN đã tồn tại")
    publisher = db.get(Publisher, payload.publisher_id) if payload.publisher_id else None
    if payload.publisher_id and not publisher:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà xuất bản")
    authors = db.scalars(select(Author).where(Author.id.in_(payload.author_ids))).all() if payload.author_ids else []
    if len(authors) != len(set(payload.author_ids)):
        raise HTTPException(status_code=404, detail="Có tác giả không tồn tại")
    return category, publisher, list(authors)


@router.get("/books", response_model=list[BookTitleOut])
def list_books(
    db: DbSession,
    search: str | None = Query(default=None, max_length=100),
    include_inactive: bool = False,
):
    statement = _title_query().order_by(BookTitle.title)
    if not include_inactive:
        statement = statement.where(BookTitle.is_active.is_(True))
    if search:
        needle = f"%{search.strip()}%"
        statement = statement.outerjoin(BookTitle.authors).where(
            or_(BookTitle.title.ilike(needle), BookTitle.isbn.ilike(needle), Author.name.ilike(needle))
        ).distinct()
    return db.scalars(statement).all()


@router.get("/books/{book_id}", response_model=BookTitleOut)
def get_book(book_id: int, db: DbSession):
    book = db.scalar(_title_query().where(BookTitle.id == book_id))
    if not book:
        raise HTTPException(status_code=404, detail="Không tìm thấy đầu sách")
    return book


@router.post("/books", response_model=BookTitleOut, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookTitleCreate, db: DbSession, _: StaffUser):
    category, publisher, authors = _validate_book_payload(payload, db)
    book = BookTitle(
        isbn=payload.isbn.strip() if payload.isbn else None,
        title=payload.title.strip(),
        description=payload.description,
        publication_year=payload.publication_year,
        edition=payload.edition,
        language=payload.language,
        image_url=payload.image_url,
        category=category,
        publisher=publisher,
        authors=authors,
    )
    db.add(book)
    db.commit()
    return db.scalar(_title_query().where(BookTitle.id == book.id))


@router.put("/books/{book_id}", response_model=BookTitleOut)
def update_book(book_id: int, payload: BookTitleUpdate, db: DbSession, _: StaffUser):
    book = db.get(BookTitle, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Không tìm thấy đầu sách")
    category, publisher, authors = _validate_book_payload(payload, db, ignore_id=book_id)
    book.isbn = payload.isbn.strip() if payload.isbn else None
    book.title = payload.title.strip()
    book.description = payload.description
    book.publication_year = payload.publication_year
    book.edition = payload.edition
    book.language = payload.language
    book.image_url = payload.image_url
    book.is_active = payload.is_active
    book.category = category
    book.publisher = publisher
    book.authors = authors
    db.commit()
    return db.scalar(_title_query().where(BookTitle.id == book_id))


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_book(book_id: int, db: DbSession, _: StaffUser):
    book = db.get(BookTitle, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Không tìm thấy đầu sách")
    if db.scalar(select(func.count()).select_from(BookCopy).where(BookCopy.book_title_id == book_id, BookCopy.status == CopyStatus.ON_LOAN)):
        raise HTTPException(status_code=409, detail="Không thể ẩn đầu sách đang có cuốn được mượn")
    book.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/books/{book_id}/copies", response_model=BookTitleOut, status_code=status.HTTP_201_CREATED)
def add_copy(book_id: int, payload: BookCopyCreate, db: DbSession, _: StaffUser):
    book = db.get(BookTitle, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Không tìm thấy đầu sách")
    barcode = payload.barcode.strip()
    if db.scalar(select(BookCopy).where(BookCopy.barcode == barcode)):
        raise HTTPException(status_code=409, detail="Mã vạch đã tồn tại")
    db.add(BookCopy(book_title=book, barcode=barcode, shelf_location=payload.shelf_location, acquired_at=payload.acquired_at, condition_note=payload.condition_note))
    db.commit()
    return db.scalar(_title_query().where(BookTitle.id == book_id))


@router.patch("/copies/{copy_id}/status", response_model=BookTitleOut)
def change_copy_status(copy_id: int, copy_status: CopyStatus, db: DbSession, _: StaffUser):
    copy = db.get(BookCopy, copy_id)
    if not copy:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuốn sách")
    if copy.status == CopyStatus.ON_LOAN:
        raise HTTPException(status_code=409, detail="Không thể đổi trạng thái khi sách đang được mượn")
    copy.status = copy_status
    db.commit()
    return db.scalar(_title_query().where(BookTitle.id == copy.book_title_id))
