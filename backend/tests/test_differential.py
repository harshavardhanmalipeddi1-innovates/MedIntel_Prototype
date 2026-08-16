import pytest
from backend.services.ranking_engine import RankingEngine
from backend.services.threshold_engine import ThresholdEngine
from backend.services.confidence_engine import ConfidenceEngine
from backend.services.differential_manager import DifferentialDiagnosisManager

def test_ranking():
    engine = RankingEngine(top_k=5)
    predictions = {"Pneumonia": 0.91, "COVID": 0.82, "Bronchitis": 0.71}
    ranked = engine.rank(predictions)
    assert len(ranked) == 3
    assert ranked[0]["disease"] == "Pneumonia"
    assert ranked[0]["rank"] == 1
    assert ranked[1]["disease"] == "COVID"
    assert ranked[2]["disease"] == "Bronchitis"

def test_top_k():
    engine = RankingEngine(top_k=2)
    predictions = {"Pneumonia": 0.91, "COVID": 0.82, "Bronchitis": 0.71}
    ranked = engine.rank(predictions)
    assert len(ranked) == 2
    assert ranked[-1]["disease"] == "COVID"

def test_threshold_filtering():
    engine = ThresholdEngine(min_probability=0.20)
    predictions = {"A": 0.9, "B": 0.15, "C": 0.05, "D": 0.20}
    filtered = engine.filter(predictions)
    assert len(filtered) == 2
    assert "A" in filtered
    assert "D" in filtered
    assert "B" not in filtered

def test_confidence_mapping():
    engine = ConfidenceEngine(high_threshold=0.85, medium_threshold=0.60)
    assert engine.evaluate(0.90) == "High"
    assert engine.evaluate(0.85) == "High"
    assert engine.evaluate(0.80) == "Medium"
    assert engine.evaluate(0.60) == "Medium"
    assert engine.evaluate(0.59) == "Low"
    assert engine.evaluate(0.10) == "Low"

def test_empty_predictions():
    manager = DifferentialDiagnosisManager()
    result = manager.generate_differential({})
    assert result["success"] is True
    assert len(result["predictions"]) == 0

def test_single_prediction():
    manager = DifferentialDiagnosisManager()
    result = manager.generate_differential({"OnlyOne": 0.99})
    assert len(result["predictions"]) == 1
    assert result["predictions"][0]["disease"] == "OnlyOne"
    assert result["predictions"][0]["confidence"] == "High"

def test_equal_probabilities():
    engine = RankingEngine(top_k=5)
    # Python's stable sort or dict order handles ties, we just want to ensure it doesn't crash
    predictions = {"A": 0.5, "B": 0.5, "C": 0.5}
    ranked = engine.rank(predictions)
    assert len(ranked) == 3
    for idx, item in enumerate(ranked):
        assert item["probability"] == 0.5
        assert item["rank"] == idx + 1

def test_invalid_input_handling():
    engine = RankingEngine(top_k=5)
    with pytest.raises(AttributeError):
        # A list instead of a dict will throw AttributeError for .items()
        engine.rank(["A", "B"])

def test_manager_integration():
    manager = DifferentialDiagnosisManager()
    # Override settings explicitly for testing to avoid global config dependence
    manager.ranking_engine.top_k = 2
    manager.threshold_engine.min_probability = 0.10
    manager.confidence_engine.high_threshold = 0.85
    manager.confidence_engine.medium_threshold = 0.60
    
    raw = {
        "Disease1": 0.95,
        "Disease2": 0.80,
        "Disease3": 0.70,
        "Disease4": 0.05
    }
    result = manager.generate_differential(raw)
    
    assert result["success"] is True
    preds = result["predictions"]
    # Only Top 2 due to top_k override
    assert len(preds) == 2
    
    # Check top 1
    assert preds[0]["disease"] == "Disease1"
    assert preds[0]["probability"] == 0.95
    assert preds[0]["confidence"] == "High"
    
    # Check top 2
    assert preds[1]["disease"] == "Disease2"
    assert preds[1]["probability"] == 0.80
    assert preds[1]["confidence"] == "Medium"
