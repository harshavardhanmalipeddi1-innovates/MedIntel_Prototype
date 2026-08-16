from datetime import datetime
from typing import Optional, Dict, Any
from backend.services.firestore_service import FirestoreService
from backend.app.schemas.encounter_schema import EncounterCreate, EncounterResponse

class EncounterService:
    COLLECTION = "encounters"

    def __init__(self, db: FirestoreService):
        self.db = db

    def create_encounter(self, data: EncounterCreate) -> str:
        doc_data = data.model_dump()
        doc_data["created_at"] = datetime.utcnow().isoformat()
        doc_data["updated_at"] = doc_data["created_at"]
        return self.db.add_document(self.COLLECTION, doc_data)

    def get_encounter(self, encounter_id: str) -> Optional[EncounterResponse]:
        data = self.db.get_document(self.COLLECTION, encounter_id)
        if not data:
            return None
        data["id"] = encounter_id
        return EncounterResponse(**data)

    def _update_encounter_field(self, encounter_id: str, field_name: str, field_data: Dict[str, Any]) -> bool:
        if not self.get_encounter(encounter_id):
            return False
            
        update_data = {
            field_name: field_data,
            "updated_at": datetime.utcnow().isoformat()
        }
        self.db.update_document(self.COLLECTION, encounter_id, update_data)
        return True

    def attach_prediction_results(self, encounter_id: str, results: Dict[str, Any]) -> bool:
        return self._update_encounter_field(encounter_id, "ai_prediction_results", results)

    def attach_reasoning_results(self, encounter_id: str, results: Dict[str, Any]) -> bool:
        return self._update_encounter_field(encounter_id, "ai_reasoning_results", results)

    def attach_verification_results(self, encounter_id: str, results: Dict[str, Any]) -> bool:
        return self._update_encounter_field(encounter_id, "ai_verification_results", results)

    def attach_treatment_draft(self, encounter_id: str, results: Dict[str, Any]) -> bool:
        return self._update_encounter_field(encounter_id, "ai_treatment_draft", results)

    def attach_doctor_outcome(self, encounter_id: str, results: Dict[str, Any]) -> bool:
        return self._update_encounter_field(encounter_id, "doctor_confirmed_outcome", results)
