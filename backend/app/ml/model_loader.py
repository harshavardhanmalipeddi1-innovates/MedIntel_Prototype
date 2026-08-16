import logging
from typing import Any
from backend.app.ml.artifact_manager import ArtifactManager

logger = logging.getLogger(__name__)

class ModelLoader:
    """Provides lazy access to AI model artifacts via ArtifactManager.
    All loading is delegated to ArtifactManager; this class adds caching
    and higher‑level error translation.
    """

    def __init__(self):
        self._artifact_manager = ArtifactManager()
        self._cache: dict[str, Any] = {}
        logger.info("ModelLoader instantiated with ArtifactManager")

    def _load(self, name: str, loader_callable):
        """Internal helper to perform lazy loading with caching.
        Args:
            name: Cache key / descriptive name.
            loader_callable: Callable that returns the artifact.
        Returns:
            The loaded artifact.
        Raises:
            RuntimeError: If ArtifactManager raises an error, re‑raise with
            a clearer context.
        """
        if name in self._cache:
            logger.debug("Cache hit for %s", name)
            return self._cache[name]
        try:
            artifact = loader_callable()
            self._cache[name] = artifact
            logger.info("Loaded and cached %s", name)
            return artifact
        except RuntimeError as e:
            logger.error("Failed to load %s: %s", name, e)
            raise RuntimeError(f"ModelLoader failed to load {name}: {e}") from e

    def load_primary_model(self) -> Any:
        return self._load("primary_model", self._artifact_manager.get_primary_model)

    def load_supported_scope_model(self) -> Any:
        return self._load("supported_scope_model", self._artifact_manager.get_supported_scope_model)

    def load_preprocessing_bundle(self) -> Any:
        return self._load("preprocessing_bundle", self._artifact_manager.get_preprocessing_bundle)

    def load_metadata(self) -> Any:
        return self._load("metadata", self._artifact_manager.get_metadata)

    def load_candidate_models(self) -> Any:
        return self._load("candidate_inclusion_models", self._artifact_manager.get_candidate_inclusion_models)

    def load_critical_models(self) -> Any:
        return self._load("critical_pathology_models", self._artifact_manager.get_critical_pathology_models)

    def load_ddx_models(self) -> Any:
        return self._load("ddx_probability_models", self._artifact_manager.get_ddx_probability_models)
