from datetime import datetime
from typing import Optional
from backend.services.firestore_service import FirestoreService
from backend.app.schemas.patient_schema import PatientCreate, PatientUpdate, PatientResponse

class PatientService:
    COLLECTION = "patients"

    def __init__(self, db: FirestoreService):
        self.db = db

    def create_patient(self, data: PatientCreate) -> str:
        doc_data = data.model_dump()
        doc_data["created_at"] = datetime.utcnow().isoformat()
        doc_data["updated_at"] = doc_data["created_at"]
        return self.db.add_document(self.COLLECTION, doc_data)

    def get_patient(self, patient_id: str) -> Optional[PatientResponse]:
        data = self.db.get_document(self.COLLECTION, patient_id)
        if not data:
            return None
        data["id"] = patient_id
        return PatientResponse(**data)

    def update_patient(self, patient_id: str, update_data: PatientUpdate) -> bool:
        if not self.get_patient(patient_id):
            return False
            
        doc_data = update_data.model_dump(exclude_unset=True)
        doc_data["updated_at"] = datetime.utcnow().isoformat()
        self.db.update_document(self.COLLECTION, patient_id, doc_data)
        return True
