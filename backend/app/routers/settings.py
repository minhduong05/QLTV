from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import AdminUser, DbSession
from app.models import SystemSetting
from app.schemas import SettingOut, SettingUpdate
from app.services import DEFAULT_SETTINGS, ensure_default_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=list[SettingOut])
def list_settings(db: DbSession, _: AdminUser):
    ensure_default_settings(db)
    return db.scalars(select(SystemSetting).order_by(SystemSetting.key)).all()


@router.put("/{key}", response_model=SettingOut)
def update_setting(key: str, payload: SettingUpdate, db: DbSession, _: AdminUser):
    if key not in DEFAULT_SETTINGS:
        raise HTTPException(status_code=404, detail="Không tìm thấy quy định hệ thống")
    ensure_default_settings(db)
    item = db.get(SystemSetting, key)
    item.value = payload.value
    if payload.description is not None:
        item.description = payload.description
    db.commit()
    db.refresh(item)
    return item
