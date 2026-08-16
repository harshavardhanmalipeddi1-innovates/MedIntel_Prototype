import pytest
from backend.services.model_loader import ModelLoader


@pytest.fixture(scope="module")
def loader():
    return ModelLoader()


def test_primary_model_loads(loader):
    model = loader.load_primary_model()
    assert model is not None
    assert hasattr(model, "save_model") or hasattr(model, "get_dump")


def test_supported_scope_model_loads(loader):
    model = loader.load_supported_scope_model()
    assert model is not None
    assert hasattr(model, "save_model") or hasattr(model, "get_dump")


def test_candidate_model_loads(loader):
    candidates = loader.list_candidate_models()
    assert len(candidates) > 0

    model = loader.load_candidate_model(candidates[0])

    assert model is not None
    assert hasattr(model, "save_model") or hasattr(model, "get_dump")