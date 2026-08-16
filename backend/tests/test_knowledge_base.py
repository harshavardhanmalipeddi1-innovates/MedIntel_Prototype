import pytest
from backend.services.knowledge_base import KnowledgeBaseService

@pytest.fixture(scope='module')
def kb_service():
    return KnowledgeBaseService()

def test_service_initialization(kb_service):
    assert kb_service.enabled is True
    assert isinstance(kb_service.list_supported_diseases(), list)

def test_list_supported_diseases(kb_service):
    diseases = kb_service.list_supported_diseases()
    assert 'Pneumonia' in diseases
    assert 'Tuberculosis' in diseases
    assert 'Pulmonary Embolism' in diseases

@pytest.mark.parametrize('name,expected_id', [
    ('Pneumonia', 'pneumonia'),
    ('Tuberculosis', 'tuberculosis'),
    ('Pulmonary Embolism', 'pulmonary_embolism'),
])
def test_get_disease_by_name(kb_service, name, expected_id):
    disease = kb_service.get_disease(name)
    assert disease is not None
    assert disease.disease_id == expected_id

def test_case_insensitive_and_whitespace(kb_service):
    disease = kb_service.get_disease('  pNeUmOnIa  ')
    assert disease is not None
    assert disease.name == 'Pneumonia'

def test_alias_lookup(kb_service):
    disease = kb_service.get_disease('PE')
    assert disease is not None
    assert disease.name == 'Pulmonary Embolism'

def test_get_disease_by_id(kb_service):
    disease = kb_service.get_disease_by_id('tuberculosis')
    assert disease is not None
    assert disease.name == 'Tuberculosis'

def test_get_multiple_diseases(kb_service):
    result = kb_service.get_multiple_diseases(['pneumonia', 'TB', 'Pulmonary Embolism'])
    assert len(result) == 3
    names = [d.name for d in result if d]
    assert set(names) == {'Pneumonia', 'Tuberculosis', 'Pulmonary Embolism'}

def test_unknown_disease(kb_service):
    assert kb_service.get_disease('unknown disease') is None
    assert kb_service.get_disease_by_id('nonexistent') is None

def test_required_fields(kb_service):
    disease = kb_service.get_disease('Pneumonia')
    for field in ['disease_id', 'name', 'description', 'body_system', 'common_symptoms']:
        assert getattr(disease, field, None) is not None

def test_knowledge_version(kb_service):
    disease = kb_service.get_disease('Pneumonia')
    assert hasattr(disease, 'knowledge_version')
