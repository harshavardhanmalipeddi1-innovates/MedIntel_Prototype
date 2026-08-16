from backend.services.clinical_rules import ClinicalRules


def test_clinical_rules_initialization():

    rules = ClinicalRules()

    assert rules is not None


def test_rule_evaluation():

    rules = ClinicalRules()

    symptoms = {
        "fever": True,
        "cough": True
    }

    result = rules.evaluate(symptoms)

    assert result is not None
    assert isinstance(result, dict)