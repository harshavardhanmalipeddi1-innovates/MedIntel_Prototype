import logging
from typing import Any, Dict, List

import numpy as np
from scipy import sparse

from backend.app.ml.artifact_manager import ArtifactManager
from backend.app.ml.model_loader import ModelLoader


logger = logging.getLogger(__name__)


class FeatureBuilder:
    """Construct runtime feature vectors for Respiratory XGBoost models.

    The preprocessing bundle is stored as a dictionary in
    preprocessing_bundle.joblib.
    """

    def __init__(
        self,
        artifact_manager: ArtifactManager | None = None,
        model_loader: ModelLoader | None = None,
    ) -> None:
        self._artifact_manager = artifact_manager or ArtifactManager()
        self._model_loader = model_loader or ModelLoader()
        self._bundle = None
        self._logger = logger

    # ------------------------------------------------------------------
    # Lazy preprocessing bundle
    # ------------------------------------------------------------------

    @property
    def preprocessing_bundle(self) -> Dict[str, Any]:
        """Load and cache the preprocessing bundle."""

        if self._bundle is None:
            self._bundle = self._artifact_manager.get_preprocessing_bundle()
            self._logger.debug("Preprocessing bundle loaded lazily")

        return self._bundle

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_feature_names(self) -> List[str]:
        """Return the exact feature order stored in the bundle."""

        bundle = self.preprocessing_bundle

        if isinstance(bundle, dict):
            return list(bundle["feature_names"])

        return list(bundle.feature_names)

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate required runtime input."""

        missing = []

        if "evidence_tokens" not in data:
            missing.append("evidence_tokens")

        if missing:
            msg = f"Input data missing required fields: {', '.join(missing)}"
            self._logger.error(msg)
            raise RuntimeError(msg)

        if not isinstance(data["evidence_tokens"], list):
            raise RuntimeError("evidence_tokens must be a list of strings")

        if not all(isinstance(x, str) for x in data["evidence_tokens"]):
            raise RuntimeError("All evidence_tokens must be strings")

        self._logger.debug("Input validation passed")

    def build_dense_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Build the six dense features using the predefined order.

        The preprocessing bundle does not contain a dedicated dense_feature_names list.
        We explicitly use the first six feature names defined by the specification.
        """
        # Retrieve the preprocessing bundle
        bundle = self.preprocessing_bundle
        # Explicit dense feature names as per specification
        dense_feature_names = [
            "AGE",
            "SEX_MALE_CODE",
            "NONINITIAL_EVIDENCE_COUNT",
            "QUESTIONNAIRE_COMPLETION_FRACTION",
            "INITIAL_EVIDENCE_ONLY",
            "CONSULTATION_STAGE_CODE",
        ]
        values = []
        for name in dense_feature_names:
            val = data.get(name, np.nan)
            if isinstance(val, (bool, int, float)):
                val = float(val)
            values.append(val)
        dense_array = np.array(values, dtype=float).reshape(1, -1)
        self._logger.debug("Dense feature array shape: %s", dense_array.shape)
        return dense_array

    def encode_evidence(self, tokens: List[str]) -> sparse.csr_matrix:
        """Encode evidence tokens using the bundled MultiLabelBinarizer."""

        if not isinstance(tokens, list):
            raise RuntimeError("evidence_tokens must be a list of strings")

        if not all(isinstance(token, str) for token in tokens):
            raise RuntimeError("All evidence_tokens must be strings")

        bundle = self.preprocessing_bundle

        if isinstance(bundle, dict):
            encoder = bundle["evidence_encoder"]
        else:
            encoder = bundle.evidence_encoder

        # IMPORTANT:
        # evidence_encoder is MultiLabelBinarizer.
        # It expects a list of labels per sample.
        encoded = encoder.transform([tokens])

        if not sparse.issparse(encoded):
            encoded = sparse.csr_matrix(encoded)
        else:
            encoded = encoded.tocsr()

        self._logger.debug(
            "Evidence encoding shape: %s",
            encoded.shape,
        )

        return encoded

    def build_feature_vector(
        self,
        data: Dict[str, Any],
    ) -> sparse.csr_matrix:
        """Build the final model feature vector."""

        self.validate_input(data)

        dense = self.build_dense_features(data)
        evidence = self.encode_evidence(data["evidence_tokens"])

        dense_csr = sparse.csr_matrix(dense)

        if dense_csr.shape[1] == 0:
            combined = evidence
        else:
            combined = sparse.hstack(
                [dense_csr, evidence],
                format="csr",
            )

        expected_len = len(self.get_feature_names())

        if combined.shape[1] != expected_len:
            msg = (
                f"Feature vector column count {combined.shape[1]} "
                f"does not match expected {expected_len}."
            )

            self._logger.error(msg)

            raise RuntimeError(msg)

        if combined.data.size > 0 and np.isnan(combined.data).any():
            self._logger.error("NaN values detected in feature matrix")
            raise RuntimeError("Feature matrix contains NaN values")

        self._logger.debug(
            "Final feature matrix shape: %s",
            combined.shape,
        )

        return combined