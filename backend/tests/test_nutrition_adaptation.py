import pytest

from app import create_app
from app.models import ModelAdaptation
from app.services.adaptation import AdaptationFailure, AdaptationService, adaptation_service
from app.services.nutrition import nutrition_reference
from scripts.build_recipe1m_index import _validated_recipe_totals


class StubClient:
    model = "gemma-test"

    def __init__(self, proposal: dict):
        self.proposal = proposal

    def structured(self, _system, _user, schema_model, timeout):
        assert timeout == 30
        return schema_model.model_validate(self.proposal)


def source_recipe():
    return {
        "slug": "tofu-bowl",
        "name": "Tofu bowl",
        "servings": 2,
        "ingredients": [{"id": "tofu", "name": "Firm tofu"}, {"id": "rice", "name": "Rice"}],
        "steps": [{"text": "Cook the tofu and rice."}],
        "source": {"attribution": "Test source"},
    }


def proposal(**change):
    return {
        "title": "Protein-forward tofu bowl",
        "changes": [{
            "action": "increase", "ingredient_id": "tofu", "quantity_g": 100,
            "reason": "Use more of the tofu already in the pantry", **change,
        }],
        "instruction_notes": ["Brown the additional tofu in the same pan."],
    }


def test_nutrient_delta_is_server_calculated_from_usda_record():
    service = AdaptationService(StubClient(proposal()))
    result = service.adapt(
        source_recipe(), "tofu, rice", 30, [], 2,
        {"protein": 18, "calories": 420, "fat": 12, "carbs": 55},
    )
    assert result["nutrition_delta"] == {"protein": 4.5, "calories": 39.0, "fat": 2.1}
    assert result["adapted_nutrition"]["protein"] == 22.5
    assert result["changes"][0]["fdc_id"] == 172448
    assert result["nutrition_source"]["name"].startswith("USDA FoodData Central")


def test_adaptation_rejects_non_pantry_and_invalid_increase():
    non_pantry = AdaptationService(StubClient(proposal(ingredient_id="chicken")))
    with pytest.raises(AdaptationFailure, match="unknown_or_duplicate_ingredient"):
        non_pantry.adapt(source_recipe(), "tofu", 30, [], 2, {"protein": 18, "calories": 420, "fat": 12, "carbs": 55})

    missing_source = AdaptationService(StubClient(proposal(action="increase", ingredient_id="egg")))
    with pytest.raises(AdaptationFailure, match="ingredient_not_in_source"):
        missing_source.adapt(source_recipe(), "egg", 30, [], 2, {"protein": 18, "calories": 420, "fat": 12, "carbs": 55})


def test_adaptation_rejects_excluded_and_unsafe_proposals():
    excluded = AdaptationService(StubClient(proposal()))
    with pytest.raises(AdaptationFailure, match="no_supported_pantry_ingredients"):
        excluded.adapt(source_recipe(), "tofu", 30, ["tofu"], 2, {"protein": 18, "calories": 420, "fat": 12, "carbs": 55})

    unsafe_data = proposal()
    unsafe_data["instruction_notes"] = ["Finish with bacon."]
    unsafe = AdaptationService(StubClient(unsafe_data))
    with pytest.raises(AdaptationFailure, match="unsafe_proposal"):
        unsafe.adapt(source_recipe(), "tofu", 30, [], 2, {"protein": 18, "calories": 420, "fat": 12, "carbs": 55})


def test_recipe1m_totals_require_consistent_grounded_inputs():
    totals = _validated_recipe_totals(
        [100, 50],
        [{"pro": 10, "nrg": 120, "fat": 2}, {"pro": 5, "nrg": 60, "fat": 1}],
        (10, 120, 2),
    )
    assert totals == {"weight": 150, "protein": 15.0, "calories": 180.0, "fat": 3.0}
    assert _validated_recipe_totals([100], [], (10, 120, 2)) is None
    assert _validated_recipe_totals([100_000], [{"pro": 1, "nrg": 1, "fat": 1}], (1, 1, 1)) is None


def test_reference_resolves_only_supported_pantry_foods():
    matched = nutrition_reference.pantry_foods("leftover rice, tofu and dahi")
    assert set(matched) == {"tofu", "greek-yogurt"}


def test_adaptation_api_returns_only_validated_server_nutrition(monkeypatch):
    monkeypatch.setattr(adaptation_service, "client", StubClient(proposal()))
    client = create_app(testing=True).test_client()
    response = client.post("/api/recipes/miso-soup/adapt", json={
        "pantry": "tofu", "protein_target_g": 20, "exclusions": [],
    })
    assert response.status_code == 200
    assert response.json["model"] == "gemma-test"
    assert response.json["changes"][0]["fdc_id"] == 172448
    assert response.json["nutrition_delta"]["protein"] == 2.3


def test_adaptation_api_requires_a_real_recipe_and_valid_request():
    client = create_app(testing=True).test_client()
    assert client.post("/api/recipes/not-real/adapt", json={"pantry": "tofu"}).status_code == 404
    response = client.post("/api/recipes/miso-soup/adapt", json={"pantry": "", "servings": 0})
    assert response.status_code == 422
