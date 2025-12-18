from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

# Minimal HTTP client; keeps GUI independent from the API/ORM layer.
DEFAULT_API_BASE = os.environ.get("VETCLINIC_API_URL", "http://127.0.0.1:8000")


class MedicalRecordsService:
    """
    Prosty klient HTTP do zarządzania historią medyczną zwierząt.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or DEFAULT_API_BASE).rstrip("/")

    # --- instancje -----------------------------------------------------
    def list_records(self, animal_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if animal_id is not None:
            params["animal_id"] = animal_id
        resp = requests.get(
            f"{self.base_url}/medical_records/", params=params, timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def list_by_appointment(self, appointment_id: int) -> List[Dict[str, Any]]:
        params = {"appointment_id": appointment_id}
        resp = requests.get(
            f"{self.base_url}/medical_records/", params=params, timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def get(self, record_id: int) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/medical_records/{record_id}", timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/medical_records/", json=payload, timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def update(self, record_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.put(
            f"{self.base_url}/medical_records/{record_id}", json=payload, timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def delete(self, record_id: int) -> None:
        resp = requests.delete(
            f"{self.base_url}/medical_records/{record_id}", timeout=5
        )
        resp.raise_for_status()

    # --- klasowe proxy dla zgodności -----------------------------------
    @classmethod
    def _client(cls) -> "MedicalRecordsService":
        return cls()

    @classmethod
    def list(cls, animal_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return cls._client().list_records(animal_id)

    @classmethod
    def list_by_appointment(cls, appointment_id: int) -> List[Dict[str, Any]]:
        return cls._client().list_by_appointment(appointment_id)

    @classmethod
    def get_record(cls, record_id: int) -> Dict[str, Any]:
        return cls._client().get(record_id)

    @classmethod
    def create_record(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        return cls._client().create(payload)

    @classmethod
    def update_record(cls, record_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return cls._client().update(record_id, payload)

    @classmethod
    def delete_record(cls, record_id: int) -> None:
        return cls._client().delete(record_id)


# Alias for import compatibility
MedicalRecordService = MedicalRecordsService
