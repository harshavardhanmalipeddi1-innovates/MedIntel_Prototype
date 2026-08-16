import json
import joblib
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ArtifactManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        # Locate the respiratory model directory relative to this file
        self._base_path = (
            Path(__file__).resolve().parents[2]
            / "models"
            / "respiratory"
        )

        if not self._base_path.is_dir():
            raise RuntimeError(
                f"Missing artifact directory: {self._base_path}"
            )

        self._cache: Dict[str, Any] = {}
        self._initialized = True

        logger.info(
            "Artifact base path discovered: %s",
            self._base_path,
        )

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self._base_path / filename

        if not path.is_file():
            raise RuntimeError(f"Missing artifact: {filename}")

        if filename in self._cache:
            logger.debug(
                "Cache hit for JSON artifact: %s",
                filename,
            )
            return self._cache[filename]

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self._cache[filename] = data

        logger.info(
            "Loaded JSON artifact: %s",
            filename,
        )

        return data

    def _load_joblib(self, filename: str) -> Any:
        path = self._base_path / filename

        if not path.is_file():
            raise RuntimeError(f"Missing artifact: {filename}")

        if filename in self._cache:
            logger.debug(
                "Cache hit for joblib artifact: %s",
                filename,
            )
            return self._cache[filename]

        obj = joblib.load(path)

        self._cache[filename] = obj

        logger.info(
            "Loaded joblib artifact: %s",
            filename,
        )

        return obj

    def _load_directory(self, dirname: str) -> List[Path]:
        dir_path = self._base_path / dirname

        if not dir_path.is_dir():
            raise RuntimeError(
                f"Missing artifact directory: {dirname}"
            )

        if dirname in self._cache:
            logger.debug(
                "Cache hit for directory: %s",
                dirname,
            )
            return self._cache[dirname]

        files = sorted(
            p for p in dir_path.iterdir() if p.is_file()
        )

        self._cache[dirname] = files

        logger.info(
            "Discovered %d files in %s",
            len(files),
            dirname,
        )

        return files

    # Public getters

    def get_primary_model(self) -> Dict[str, Any]:
        return self._load_json(
                        "model/primary_pathology_xgboost.json"
        )

    def get_supported_scope_model(self) -> Dict[str, Any]:
        return self._load_json(
                        "model/supported_scope_xgboost.json"
        )

    def get_preprocessing_bundle(self) -> Any:
        return self._load_joblib(
            "preprocessing/preprocessing_bundle.joblib"
        )

    def get_metadata(self) -> Dict[str, Any]:
        return self._load_json(
                        "metadata/portable_metadata.json"
        )

    def get_candidate_inclusion_models(self) -> List[Path]:
        return self._load_directory(
                        "model/candidate_inclusion_models"
        )

    def get_critical_pathology_models(self) -> List[Path]:
        return self._load_directory(
            "critical_pathology_models"
        )

    def get_ddx_probability_models(self) -> List[Path]:
        return self._load_directory(
            "ddx_probability_models"
        )