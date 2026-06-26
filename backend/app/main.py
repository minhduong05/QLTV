from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import acquisitions, auth, catalog, dashboard, loans, readers, settings as settings_router, users
from app.seed import ensure_demo_data
from app.services import ensure_default_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="API quản lý thư viện: danh mục, bạn đọc, mượn trả và báo cáo.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, users.router, catalog.router, readers.router, loans.router, acquisitions.router, settings_router.router, dashboard.router):
    app.include_router(router, prefix=settings.api_prefix)


def ensure_sqlite_schema_compatibility() -> None:
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    with engine.begin() as connection:
        reader_columns = {column["name"] for column in inspector.get_columns("readers")}
        if "cccd" not in reader_columns:
            connection.execute(text("ALTER TABLE readers ADD COLUMN cccd VARCHAR(20)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_readers_cccd ON readers (cccd)"))

        request_columns = {column["name"] for column in inspector.get_columns("card_requests")}
        if "cccd" not in request_columns:
            connection.execute(text("ALTER TABLE card_requests ADD COLUMN cccd VARCHAR(20)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_card_requests_cccd ON card_requests (cccd)"))


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema_compatibility()
    with SessionLocal() as db:
        ensure_default_settings(db)
        ensure_demo_data(db)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.app_name}
