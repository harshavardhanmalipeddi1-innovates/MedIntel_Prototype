import numpy as np
import pytest

from backend.services.prediction_service import PredictionService


def test_prediction_service_initialization():
    service = PredictionService()
    assert service is not None
    assert hasattr(service, "_loader")


def test_primary_prediction_real_model_shape():
    service = PredictionService()

    # Authoritative primary pathology feature dimension.
    features = np.zeros(246, dtype=np.float32)

    result = service.predict_primary_disease(features)

    assert result["status"] == "success"
    assert result["model"] == "xgboost"

    predictions = result["predictions"]

    assert len(predictions) == 13

    diseases = [item["condition"] for item in predictions]

    assert len(set(diseases)) == 13
    assert "Bronchiectasis" in diseases
    assert "Pneumonia" in diseases
    assert "Pulmonary embolism" in diseases


def test_formatter_uses_authoritative_disease_order():
    service = PredictionService()

    probabilities = np.array(
        [0.20, 0.10, 0.70],
        dtype=np.float32,
    )

    predictions = service._format_predictions(probabilities)

    assert predictions[0]["condition"] == "Bronchiectasis"
    assert predictions[1]["condition"] == (
        "Acute COPD exacerbation / infection"
    )
    assert predictions[2]["condition"] == "Acute laryngitis"


def test_scope_model_cannot_be_formatted_as_disease_predictions():
    service = PredictionService()

    # The former API was unsafe because the actual scope model is
    # binary and uses a different 8198-feature representation.
    with pytest.raises(RuntimeError):
        service.predict_supported_conditions(
            np.zeros(8198, dtype=np.float32)
        )


def test_differential_helper_uses_primary_model_only():
    service = PredictionService()

    result = service.rank_differential_diagnosis(
        np.zeros(246, dtype=np.float32)
    )

    assert result["status"] == "success"
    assert result["model"] == "xgboost"
    assert len(result["predictions"]) == 13
