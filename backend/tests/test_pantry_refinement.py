import pytest
from pydantic import ValidationError

from app.models import PantryRefinement
from app.services.ollama import LocalModelError, OllamaClient
from app.services.pantry import parse_pantry
from app.services.pantry_refinement import PantryRefinementService, candidate_terms


KNOWN = {"chicken", "okra", "onion", "rice", "salt", "spinach"}


class FakeClient:
    model = "gemma3:1b"

    def __init__(self, response=None, error: str | None = None):
        self.response = response
        self.error = error
        self.calls = 0

    def structured(self, _system, _user, _schema, timeout):
        self.calls += 1
        assert timeout == 10
        if self.error:
            raise LocalModelError(self.error)
        return PantryRefinement.model_validate(self.response)


def test_complete_deterministic_parse_skips_model():
    client = FakeClient()
    parsed = parse_pantry("chicken rice", KNOWN)
    result = PantryRefinementService(client).refine("chicken rice", parsed, KNOWN)
    assert client.calls == 0
    assert result["mode"] == "deterministic"
    assert result["model_status"]["reason"] == "not_needed"


def test_valid_local_refinement_merges_without_removing_deterministic_terms():
    client = FakeClient({
        "terms": [{"raw_term": "ladyfinger", "canonical_id": "okra", "role": "core", "confidence": 0.98}],
        "ignored_terms": [],
    })
    parsed = parse_pantry("chicken, ladyfinger", KNOWN)
    result = PantryRefinementService(client).refine("chicken, ladyfinger", parsed, KNOWN)
    assert result["recognized"] == ["chicken", "okra"]
    assert result["deterministic"] == ["chicken"]
    assert result["refined"] == ["okra"]
    assert not result["unresolved"]
    assert result["mode"] == "locally_refined"


def test_unknown_or_low_confidence_terms_are_not_accepted():
    client = FakeClient({
        "terms": [
            {"raw_term": "ladyfinger", "canonical_id": "invented food", "role": "core", "confidence": 1},
            {"raw_term": "ladyfinger", "canonical_id": "okra", "role": "core", "confidence": 0.4},
        ],
        "ignored_terms": [],
    })
    parsed = parse_pantry("ladyfinger", KNOWN)
    result = PantryRefinementService(client).refine("ladyfinger", parsed, KNOWN)
    assert not result["recognized"]
    assert result["unresolved"] == ["ladyfinger"]


@pytest.mark.parametrize("reason", ["timeout", "service_unavailable", "invalid_output", "model_missing"])
def test_model_failure_preserves_deterministic_parse(reason):
    client = FakeClient(error=reason)
    parsed = parse_pantry("chicken, ladyfinger", KNOWN)
    result = PantryRefinementService(client).refine("chicken, ladyfinger", parsed, KNOWN)
    assert result["recognized"] == ["chicken"]
    assert result["unresolved"] == ["ladyfinger"]
    assert result["mode"] == "deterministic_fallback"
    assert result["model_status"]["reason"] == reason


def test_candidates_are_bounded_and_include_common_food_matches():
    candidates = candidate_terms(["ladyfinger"], KNOWN, limit=6)
    assert len(candidates) == 6
    assert "okra" in candidates


def test_ollama_rejects_non_loopback_urls():
    with pytest.raises(ValueError, match="loopback"):
        OllamaClient(base_url="https://example.com")


def test_refinement_schema_rejects_extra_fields():
    with pytest.raises(ValidationError):
        PantryRefinement.model_validate({"terms": [], "ignored_terms": [], "nutrition": {"protein": 99}})
