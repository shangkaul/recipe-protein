import pytest
from pydantic import ValidationError

from app import create_app
from app.models import ModelAdaptation
from app.services.adaptation import AdaptationFailure, AdaptationService, adaptation_service
from app.services.nutrition import nutrition_reference
from app.services.ollama import LocalModelError
from scripts.build_recipe1m_index import _validated_recipe_totals


class StubClient:
    model = "gemma-test"

    def __init__(self, proposal: dict):
        self.proposal = proposal

    def structured(self, _system, _user, schema_model, timeout):
        assert timeout == 30
        return schema_model.model_validate(self.proposal)


class FailingClient:
    model = "gemma-test"

    def __init__(self, reason: str):
        self.reason = reason

    def structured(self, *_args, **_kwargs):
        raise LocalModelError(self.reason)


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
    # The host solves 9.04 g protein per 100 g of firm tofu for the 12 g per-serving gap across
    # 2 servings, which is 265 g. Every number below comes from Python arithmetic on the USDA record.
    assert result["changes"][0]["quantity_g"] == 265
    assert result["nutrition_delta"] == {"protein": 12.0, "calories": 103.3, "fat": 5.5}
    assert result["adapted_nutrition"]["protein"] == 30.0
    assert result["protein_difference_g"] == 0.0
    assert result["changes"][0]["fdc_id"] == 172448
    assert result["nutrition_source"]["name"].startswith("USDA FoodData Central")


def test_adaptation_rejects_non_pantry_and_invalid_increase():
    non_pantry = AdaptationService(StubClient(proposal(ingredient_id="chicken")))
    with pytest.raises(ValidationError):
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


def test_host_scales_token_model_quantities_to_a_practical_amount():
    service = AdaptationService(StubClient(proposal(quantity_g=1)))
    result = service.adapt(
        source_recipe(), "tofu", 30, [], 2,
        {"protein": 18, "calories": 420, "fat": 12, "carbs": 55},
    )
    # The model asked for 1 g; the host set a kitchen-real quantity that covers the 12 g gap.
    assert result["changes"][0]["quantity_g"] >= 25
    assert result["adapted_nutrition"]["protein"] >= 30
    assert result["protein_difference_g"] >= -0.1


def test_adaptation_rejects_insignificant_and_excessive_quantities():
    weak = AdaptationService(StubClient(proposal(quantity_g=25)))
    with pytest.raises(AdaptationFailure, match="no_meaningful_increase"):
        weak.adapt(source_recipe(), "tofu", 30, [], 4, {"protein": 29.5, "calories": 420, "fat": 12, "carbs": 55})

    excessive = AdaptationService(StubClient(proposal(quantity_g=900)))
    with pytest.raises(AdaptationFailure, match="excessive_quantity"):
        excessive.adapt(source_recipe(), "tofu", 30, [], 2, {"protein": 18, "calories": 420, "fat": 12, "carbs": 55})


def test_adaptation_does_not_add_protein_when_target_is_already_met():
    service = AdaptationService(StubClient(proposal()))
    with pytest.raises(AdaptationFailure, match="target_already_met"):
        service.adapt(source_recipe(), "tofu", 15, [], 2, {"protein": 18, "calories": 420, "fat": 12, "carbs": 55})


def test_recipe1m_totals_require_consistent_grounded_inputs():
    totals = _validated_recipe_totals(
        [100, 50],
        [{"pro": 10, "nrg": 120, "fat": 2}, {"pro": 5, "nrg": 60, "fat": 1}],
        (10, 120, 2),
    )
    assert totals == {"weight": 150, "protein": 15.0, "calories": 180.0, "fat": 3.0}
    assert _validated_recipe_totals([100], [], (10, 120, 2)) is None
    assert _validated_recipe_totals([100_000], [{"pro": 1, "nrg": 1, "fat": 1}], (1, 1, 1)) is None


def test_recipe1m_rejects_batch_scale_records_that_pass_every_ratio_check():
    # A garbled quantity that inflates one recipe to 11 kg still has believable per-100g values,
    # so ratio checks alone let it through and it later divides into an impossible serving.
    oversized = _validated_recipe_totals(
        [11_275], [{"pro": 570.0, "nrg": 2062.0, "fat": 200.0}], (5.06, 18.3, 1.78)
    )
    assert oversized is None

    energy_dense = _validated_recipe_totals(
        [1_000], [{"pro": 200, "nrg": 9_000, "fat": 100}], (20, 900, 10)
    )
    assert energy_dense is None

    # More protein than the mass of food it is measured in.
    impossible_mass = _validated_recipe_totals(
        [100], [{"pro": 140, "nrg": 560, "fat": 0}], (140, 560, 0)
    )
    assert impossible_mass is None


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
    assert response.json["nutrition_delta"]["protein"] == 11.0
    # Miso soup supplies 9 g per serving against a 20 g target, so 11 g is the gap the host closed.
    assert response.json["adapted_nutrition"]["protein"] == 20.0


def test_adaptation_api_requires_a_real_recipe_and_valid_request():
    client = create_app(testing=True).test_client()
    assert client.post("/api/recipes/not-real/adapt", json={"pantry": "tofu"}).status_code == 404
    response = client.post("/api/recipes/miso-soup/adapt", json={"pantry": "", "servings": 0})
    assert response.status_code == 422


def test_adaptation_api_preserves_original_when_local_model_fails(monkeypatch):
    monkeypatch.setattr(adaptation_service, "client", FailingClient("service_unavailable"))
    response = create_app(testing=True).test_client().post("/api/recipes/miso-soup/adapt", json={
        "pantry": "tofu", "protein_target_g": 20,
    })
    assert response.status_code == 503
    assert response.json["reason"] == "service_unavailable"
    assert "Start Ollama" in response.json["error"]
