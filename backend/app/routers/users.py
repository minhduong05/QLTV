from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import AdminUser, DbSession
from app.models import Acquisition, BorrowRequest, BorrowTicket, CardRequest, Loan, Payment, User, UserRole
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["Administration"])


@router.get("", response_model=list[UserOut])
def list_users(db: DbSession, _: AdminUser):
    return db.scalars(select(User).order_by(User.full_name)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, _: AdminUser):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được sử dụng")
    if payload.role == UserRole.READER:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tài khoản bạn đọc cần tạo bằng form đăng ký người dùng")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: DbSession, _: AdminUser):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")
    if payload.role and user.role == UserRole.ADMIN and payload.role != UserRole.ADMIN:
        admins = db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN, User.is_active.is_(True))) or 0
        if admins <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hệ thống phải có ít nhất một admin đang hoạt động")
    if payload.is_active is False and user.role == UserRole.ADMIN:
        admins = db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN, User.is_active.is_(True))) or 0
        if admins <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Không thể khóa admin cuối cùng")
    for key, value in payload.model_dump(exclude_unset=True, exclude={"password"}).items():
        setattr(user, key, value.strip() if key == "full_name" and value else value)
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, current_admin: AdminUser):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Không thể tự xóa tài khoản đang đăng nhập")
    if user.role == UserRole.ADMIN and user.is_active:
        admins = db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN, User.is_active.is_(True))) or 0
        if admins <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Không thể xóa admin đang hoạt động cuối cùng")

    reference_checks = [
        ("yêu cầu cấp thẻ", select(func.count()).select_from(CardRequest).where(CardRequest.user_id == user.id)),
        ("quyết định cấp thẻ", select(func.count()).select_from(CardRequest).where(CardRequest.decided_by_id == user.id)),
        ("phiếu mượn", select(func.count()).select_from(Loan).where(Loan.loaned_by_id == user.id)),
        ("quyết định phiếu mượn online", select(func.count()).select_from(BorrowTicket).where(BorrowTicket.decided_by_id == user.id)),
        ("yêu cầu mượn cũ", select(func.count()).select_from(BorrowRequest).where(BorrowRequest.decided_by_id == user.id)),
        ("phiếu nhập", select(func.count()).select_from(Acquisition).where(Acquisition.created_by_id == user.id)),
        ("phiếu thu", select(func.count()).select_from(Payment).where(Payment.received_by_id == user.id)),
    ]
    used_in = [label for label, statement in reference_checks if (db.scalar(statement) or 0) > 0]
    if used_in:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tài khoản đã phát sinh nghiệp vụ ({', '.join(used_in)}). Hãy khóa tài khoản thay vì xóa để giữ lịch sử.",
        )

    created_at = user.created_at or datetime.now(timezone.utc).replace(tzinfo=None)
    one_day_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    if created_at > one_day_ago:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tài khoản chưa đủ 1 ngày không phát sinh nghiệp vụ. Hãy khóa tài khoản nếu cần ngưng sử dụng ngay.",
        )

    db.delete(user)
    db.commit()
