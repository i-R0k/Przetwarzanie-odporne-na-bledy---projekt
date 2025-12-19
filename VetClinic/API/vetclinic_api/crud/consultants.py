# vetclinic_api/crud/consultants.py

from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets

from vetclinic_api.models.users import Consultant
from vetclinic_api.schemas.users import ConsultantCreate, UserUpdate
from vetclinic_api.services.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
        password = pw_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def create_consultant(
    db: Session,
    cons_in: ConsultantCreate
) -> Consultant:
    """
    Tworzy nowego konsultanta:
     - Generuje losowe hasło,
     - Buduje unikalny email (jeśli nie podano),
     - Ustawia must_change_password=True,
     - Wysyła tymczasowe hasło na backup_email.
    """
    raw_password = secrets.token_urlsafe(16)
    hashed       = get_password_hash(raw_password)

    # jeśli nie podano emaila, budujemy domyślny
    if not cons_in.email:
        base = f"{cons_in.first_name[0].lower()}.{cons_in.last_name.lower()}"
        email = f"{base}@consultant.vetclinic.com"
        i = 1
        while db.query(Consultant).filter_by(email=email).first():
            email = f"{base}{i}@consultant.vetclinic.com"
            i += 1
    else:
        email = cons_in.email

    consultant = Consultant(
        first_name           = cons_in.first_name,
        last_name            = cons_in.last_name,
        email                = email,
        password_hash        = hashed,
        facility_id          = cons_in.facility_id,
        backup_email         = cons_in.backup_email,
        must_change_password = True,
    )
    db.add(consultant)
    db.commit()
    db.refresh(consultant)

    # wyślij maila z tymczasowym hasłem
    EmailService.send_temporary_password(consultant.backup_email, raw_password)
    return consultant


def list_consultants(db: Session, skip: int = 0, limit: int = 100) -> list[Consultant]:
    return (
        db.query(Consultant)
          .order_by(Consultant.id)
          .offset(skip)
          .limit(limit)
          .all()
    )

def get_consultant(
    db: Session,
    cons_id: int
) -> Consultant | None:
    """
    Pobiera konsultanta po ID.
    """
    return db.get(Consultant, cons_id)


def update_consultant(
    db: Session,
    cons_id: int,
    data_in: UserUpdate
) -> Consultant | None:
    """
    Aktualizuje dane konsultanta.
    Jeżeli zmieniono hasło, hashuje je i
    ustawia must_change_password=False.
    """
    consultant = get_consultant(db, cons_id)
    if not consultant:
        return None

    data = data_in.model_dump(exclude_unset=True)
    if "password" in data:
        # zaktualizowano hasło
        consultant.password_hash        = get_password_hash(data.pop("password"))
        consultant.must_change_password = False

    for field, value in data.items():
        setattr(consultant, field, value)

    db.commit()
    db.refresh(consultant)
    return consultant


def delete_consultant(
    db: Session,
    cons_id: int
) -> bool:
    """
    Usuwa konsultanta, jeśli istnieje.
    """
    consultant = get_consultant(db, cons_id)
    if not consultant:
        return False
    db.delete(consultant)
    db.commit()
    return True
