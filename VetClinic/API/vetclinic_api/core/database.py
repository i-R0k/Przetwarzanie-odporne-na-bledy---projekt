from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from vetclinic_api.core.config import DATABASE_URL

engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

# Importujemy modele, by metadata zawierało ich definicje
import vetclinic_api.models.animals
import vetclinic_api.models.appointments
import vetclinic_api.models.medical_records
import vetclinic_api.models.users
import vetclinic_api.models.facility
import vetclinic_api.models_blockchain

# Tworzymy wszystkie tabele w produkcyjnej bazie
Base.metadata.create_all(bind=engine)

def get_db():
    """Funkcja zależności, która tworzy sesję bazy danych i ją zamyka po wykorzystaniu."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
