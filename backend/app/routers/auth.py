from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DbSession
from app.models import Reader, User, UserRole
from app.schemas import BootstrapRequest, LoginRequest, ReaderRegisterRequest, SetupStatus, Token, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/setup-status", response_model=SetupStatus)
def setup_status(db: DbSession) -> SetupStatus:
    """Lets the web client decide whether it should offer first-admin setup."""
    has_admin = bool(db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)))
    return SetupStatus(has_admin=has_admin)


@router.post("/bootstrap", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def bootstrap_first_admin(payload: BootstrapRequest, db: DbSession) -> User:
    """Create the very first administrator. This endpoint locks after the first account exists."""
    if db.scalar(select(func.count()).select_from(User)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hệ thống đã có tài khoản; hãy dùng chức năng quản trị")
    user = User(
        full_name=payload.full_name,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register-reader", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_reader(payload: ReaderRegisterRequest, db: DbSession) -> User:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được sử dụng")
    if db.scalar(select(Reader).where(Reader.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã có thẻ bạn đọc")
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.READER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: DbSession) -> Token:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng")
    return Token(access_token=create_access_token(user.id, user.role.value))


@router.get("/me", response_model=UserOut)
def current_account(user: CurrentUser) -> User:
    return user
