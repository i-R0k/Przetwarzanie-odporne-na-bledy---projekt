"""
Główny punkt wejścia aplikacji FastAPI.
Importuje wszystkie moduły, rejestruje routery, konfiguruje bazę danych.
"""

from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()
import uvicorn

from vetclinic_api.routers import (
    users,
    doctors,
    appointments,
    animals,
    weight_logs,
    medical_records,
    invoices,
    consultants,
    facilities,
    blockchain,
    payments,
)
from vetclinic_api.core.database import engine, Base

app = FastAPI(
    title="System Zarządzania Kliniką Weterynaryjną",
    description="Aplikacja wykorzystująca FastAPI, SQLAlchemy oraz defensywne programowanie.",
    version="1.0.0",
)

# Rejestracja routerów
app.include_router(users.router)
app.include_router(doctors.router)
app.include_router(consultants.router)
app.include_router(facilities.router)
app.include_router(appointments.router)
app.include_router(animals.router)
app.include_router(medical_records.router)
app.include_router(invoices.router)
app.include_router(weight_logs.router)
app.include_router(blockchain.router)
app.include_router(payments.router)
 

# Tworzenie tabel w bazie danych (jeśli nie istnieją)
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("vetclinic_api.main:app", host="127.0.0.1", port=8000, reload=True)
