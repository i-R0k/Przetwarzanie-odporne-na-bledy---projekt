from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets

from vetclinic_api.models.users import Client
from vetclinic_api.models.animals import Animal
from vetclinic_api.models.appointments import Appointment
from vetclinic_api.schemas.users import ClientCreate, UserUpdate
from vetclinic_api.services.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
        password = pw_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)

def create_client(db: Session, cli_in: ClientCreate) -> Client:
    raw_password = secrets.token_urlsafe(16)
    hashed       = get_password_hash(raw_password)

    client = Client(
        first_name           = cli_in.first_name,
        last_name            = cli_in.last_name,
        email                = cli_in.email,
        password_hash        = hashed,
        phone_number         = cli_in.phone_number,
        address              = cli_in.address,
        postal_code          = cli_in.postal_code,
        must_change_password = True,
        wallet_address       = cli_in.wallet_address,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    EmailService.send_temporary_password(client.email, raw_password)
    return client

def list_clients(db: Session) -> list[Client]:
    return db.query(Client).all()

def get_client(db: Session, client_id: int) -> Client | None:
    return db.get(Client, client_id)

def update_client(db: Session, client_id: int, data_in: UserUpdate) -> Client | None:
    client = get_client(db, client_id)
    if not client:
        return None

    data = data_in.model_dump(exclude_unset=True)
    if "password" in data:
        client.password_hash = get_password_hash(data.pop("password"))
        client.must_change_password = True

    for attr in ("first_name","last_name","email","phone_number","address","postal_code"):
        if attr in data:
            setattr(client, attr, data[attr])

    db.commit()
    db.refresh(client)
    return client

def delete_client(db: Session, client_id: int) -> bool:
    client = get_client(db, client_id)
    if not client:
        return False
    db.query(Appointment).filter(Appointment.owner_id == client_id).delete(synchronize_session=False)
    db.query(Animal).filter(Animal.owner_id == client_id).delete(synchronize_session=False)
    db.delete(client)
    db.commit()
    return True
