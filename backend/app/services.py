from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import SystemSetting

DEFAULT_SETTINGS = {
    "loan_days": ("14", "Số ngày được mượn mỗi lần"),
    "max_active_loans": ("5", "Số cuốn tối đa một bạn đọc được mượn"),
    "fine_per_day": ("5000", "Tiền phạt quá hạn mỗi cuốn mỗi ngày (VND)"),
    "max_renewals": ("1", "Số lần được gia hạn mỗi phiếu mượn"),
    "card_validity_months": ("12", "Thời hạn thẻ bạn đọc (tháng)"),
}


def ensure_default_settings(db: Session) -> None:
    changed = False
    for key, (value, description) in DEFAULT_SETTINGS.items():
        if not db.get(SystemSetting, key):
            db.add(SystemSetting(key=key, value=value, description=description))
            changed = True
    if changed:
        db.commit()


def get_int_setting(db: Session, key: str, fallback: int) -> int:
    setting = db.get(SystemSetting, key)
    if not setting:
        return fallback
    try:
        return int(setting.value)
    except ValueError:
        return fallback
