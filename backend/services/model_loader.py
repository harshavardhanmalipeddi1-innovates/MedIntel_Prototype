import logging
from pathlib import Path
from typing import Any, Dict, List

import xgboost as xgb

logger = logging.getLogger(__name__)

class ModelLoader:
    """Lazy loader for XGBoost Booster models used by MedIntel.

    Models are stored as native XGBoost JSON dumps under
    ``backend/models/respiratory/model/``. This class loads them on first request,
    caches the Booster instances, and returns cached objects on subsequent calls.
    """

    def __init__(self) -> None:
        # Base directory where the model JSON files live
        self._model_dir = Path(__file__).resolve().parents[1] / "models" / "respiratory" / "model"
        if not self._model_dir.is_dir():
            raise RuntimeError(f"Model directory not found: {self._model_dir}")
        self._cache: Dict[str, Any] = {}
        logger.info("ModelLoader initialized – model root: %s", self._model_dir)

    def _load_booster(self, name: str, path: Path) -> xgb.Booster:
        """Load a Booster from *path* and cache it under *name*.
        Raises RuntimeError if the file cannot be loaded.
        """
        if name in self._cache:
            logger.debug("Cache hit for model %s", name)
            return self._cache[name]
        if not path.is_file():
            raise RuntimeError(f"Model file missing: {path}")
        try:
            booster = xgb.Booster()
            booster.load_model(str(path))
            self._cache[name] = booster
            logger.info("Loaded XGBoost model %s from %s", name, path)
            return booster
        except Exception as exc:
            logger.error("Failed to load XGBoost model %s: %s", name, exc)
            raise RuntimeError(f"Could not load XGBoost model {name}") from exc

    def load_primary_model(self) -> xgb.Booster:
        """Load the primary pathology XGBoost model.
        Returns a cached ``xgboost.Booster`` instance.
        """
        model_path = self._model_dir / "primary_pathology_xgboost.json"
        return self._load_booster("primary", model_path)

    def load_supported_scope_model(self) -> xgb.Booster:
        """Load the supported‑scope XGBoost model.
        Returns a cached ``xgboost.Booster`` instance.
        """
        model_path = self._model_dir / "supported_scope_xgboost.json"
        return self._load_booster("supported_scope", model_path)

    def list_candidate_models(self) -> List[str]:
        """Return the list of candidate model filenames (without extension)."""
        cand_dir = self._model_dir / "candidate_inclusion_models"
        if not cand_dir.is_dir():
            logger.warning("Candidate inclusion models directory missing: %s", cand_dir)
            return []
        return [p.stem for p in sorted(cand_dir.glob("*.json"))]

    def load_candidate_model(self, model_name: str) -> xgb.Booster:
        """Load a specific candidate inclusion model by *model_name*.

        ``model_name`` should be the stem of the JSON file (e.g. ``"Bronchospasm_acute_asthma_exacerbation"``).
        """
        cand_dir = self._model_dir / "candidate_inclusion_models"
        model_path = cand_dir / f"{model_name}.json"
        return self._load_booster(f"candidate_{model_name}", model_path)
