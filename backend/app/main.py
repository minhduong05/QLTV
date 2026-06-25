from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_default_settings(db)
        ensure_demo_data(db)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.app_name}
