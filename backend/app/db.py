import os
from typing import List, Dict, Optional
from sqlmodel import SQLModel, Session, create_engine, select
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from app.models import User, Scan, ScanItem
from datetime import datetime

# Default DB path (file in backend folder)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/app -> backend
DB_FILE = os.environ.get("SA_DB_PATH", os.path.join(BASE_DIR, "sa_data.db"))
DATABASE_URL = f"sqlite:///{DB_FILE}"

# SQLModel engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Password hasher
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def init_db() -> None:
    """
    Create DB file and all tables. Call once at startup.
    """
    # Ensure directory exists
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    SQLModel.metadata.create_all(engine)


# ---------- User helpers ----------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_user(email: str, password: str) -> User:
    hashed = hash_password(password)
    user = User(email=email, hashed_password=hashed)
    with Session(engine) as session:
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            raise ValueError("A user with that email already exists")


def get_user_by_email(email: str) -> Optional[User]:
    with Session(engine) as session:
        stmt = select(User).where(User.email == email)
        return session.exec(stmt).first()


def get_user_by_id(user_id: int) -> Optional[User]:
    with Session(engine) as session:
        return session.get(User, user_id)


# ---------- Scan helpers ----------

def save_scan_for_user(user_id: int, raw_scan: List[Dict], name: Optional[str] = None) -> Scan:
    """
    Save a whole scan snapshot (raw JSON) for a user.
    Also creates simple ScanItem rows (optional).
    """
    summary = f"{len(raw_scan)} items"
    if len(raw_scan) > 0:
        # try to find best by rssi, if present in dict
        try:
            best = sorted(
                raw_scan,
                key=lambda x: int((str(x.get("Signal (dBm)") or x.get("rssi") or "-999")).strip().split()[0]),
                reverse=True
            )[0]
            summary = f"{len(raw_scan)} items — best: {best.get('Name') or best.get('ssid') or 'Unknown'}"
        except Exception:
            pass

    scan = Scan(user_id=user_id, name=name or "Scan", timestamp=datetime.utcnow(), raw_json={"items": raw_scan}, summary=summary)
    with Session(engine) as session:
        session.add(scan)
        session.commit()
        session.refresh(scan)
        # Optionally add ScanItem rows for faster queries (lightweight)
        for it in raw_scan:
            try:
                bssid = it.get("BSSID") or it.get("bssid") or None
                ssid = it.get("Name") or it.get("ssid") or it.get("SSID") or None
                rssi_val = None
                sig = it.get("Signal (dBm)") or it.get("rssi")
                if sig is not None:
                    # extract integer
                    import re
                    m = re.search(r"-?\d+", str(sig))
                    if m:
                        rssi_val = int(m.group(0))
                item = ScanItem(scan_id=scan.id, bssid=bssid, ssid=ssid, rssi=rssi_val, extra=it)
                session.add(item)
            except Exception:
                continue
        session.commit()
    return scan


def list_scans_for_user(user_id: int) -> List[Scan]:
    with Session(engine) as session:
        stmt = select(Scan).where(Scan.user_id == user_id).order_by(Scan.timestamp.desc())
        return list(session.exec(stmt).all())


def get_scan_items(scan_id: int) -> List[ScanItem]:
    with Session(engine) as session:
        stmt = select(ScanItem).where(ScanItem.scan_id == scan_id)
        return list(session.exec(stmt).all())
