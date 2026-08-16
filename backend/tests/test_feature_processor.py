import numpy as np

from backend.services.feature_processor import FeatureProcessor


def test_feature_processor_creation():
    processor = FeatureProcessor()

    assert processor is not None


def test_feature_processing():
    processor = FeatureProcessor()

    sample = {
        "age": 45,
        "fever": 1,
        "cough": 1
    }

    result = processor.process(sample)

    assert result is not None
    assert isinstance(result, np.ndarray)


def test_feature_schema():
    processor = FeatureProcessor()

    schema = processor.get_feature_schema()

    assert isinstance(schema, list)
    assert len(schema) > 0