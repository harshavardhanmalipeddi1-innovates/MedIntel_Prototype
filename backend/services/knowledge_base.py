import os
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from backend.app.config.settings import settings
from backend.app.schemas.knowledge_schema import DiseaseKnowledge
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Service to load and query medical knowledge records."""

    def __init__(self):
        self._diseases_by_id: Dict[str, DiseaseKnowledge] = {}
        self._diseases_by_name: Dict[str, DiseaseKnowledge] = {}
        
        self.enabled = getattr(settings, "KNOWLEDGE_BASE_ENABLED", True)
        if self.enabled:
            self.kb_path = Path(getattr(settings, "KNOWLEDGE_BASE_PATH", "backend/knowledge/diseases"))
            self._load_knowledge_base()
        else:
            logger.info("Knowledge Base is disabled via settings.")

    def _normalize(self, text: str) -> str:
        """Normalize disease names for lookup (lowercase, strip whitespace)."""
        if not text:
            return ""
        return text.strip().lower()

    def _load_knowledge_base(self):
        """Load all JSON records from the knowledge base directory."""
        if not self.kb_path.exists() or not self.kb_path.is_dir():
            logger.warning(f"Knowledge Base path does not exist: {self.kb_path}")
            return

        loaded_count = 0
        for file_path in self.kb_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Validate with Pydantic
                disease_kb = DiseaseKnowledge(**data)
                
                # Register by ID
                self._diseases_by_id[disease_kb.disease_id] = disease_kb
                
                # Register by normalized primary name
                norm_name = self._normalize(disease_kb.name)
                self._diseases_by_name[norm_name] = disease_kb
                
                # Register by normalized aliases
                for alias in disease_kb.aliases:
                    norm_alias = self._normalize(alias)
                    # Don't overwrite primary name mappings with an alias mapping
                    if norm_alias not in self._diseases_by_name:
                        self._diseases_by_name[norm_alias] = disease_kb

                loaded_count += 1
            except ValidationError as e:
                logger.error(f"Validation error in knowledge record '{file_path}': {e}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in knowledge record '{file_path}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading knowledge record '{file_path}': {e}")
        
        logger.info(f"Loaded {loaded_count} knowledge base records from {self.kb_path}")

    def get_disease(self, disease_name: str) -> Optional[DiseaseKnowledge]:
        """Look up a disease by name or alias."""
        if not self.enabled:
            return None
        norm_name = self._normalize(disease_name)
        return self._diseases_by_name.get(norm_name)

    def get_disease_by_id(self, disease_id: str) -> Optional[DiseaseKnowledge]:
        """Look up a disease by exact ID."""
        if not self.enabled:
            return None
        return self._diseases_by_id.get(disease_id)

    def get_multiple_diseases(self, disease_names: List[str]) -> List[Optional[DiseaseKnowledge]]:
        """Look up multiple diseases by name."""
        return [self.get_disease(name) for name in disease_names]

    def search_disease(self, query: str) -> List[DiseaseKnowledge]:
        """Search for diseases where the query appears in the name or aliases."""
        if not self.enabled or not query:
            return []
        
        norm_query = self._normalize(query)
        results = []
        # Use a set to avoid duplicates since _diseases_by_name maps aliases to the same object
        seen_ids = set()
        
        for name, kb in self._diseases_by_name.items():
            if norm_query in name:
                if kb.disease_id not in seen_ids:
                    results.append(kb)
                    seen_ids.add(kb.disease_id)
        
        return results

    def list_supported_diseases(self) -> List[str]:
        """Return a list of all primary disease names in the knowledge base."""
        if not self.enabled:
            return []
        return [kb.name for kb in self._diseases_by_id.values()]
