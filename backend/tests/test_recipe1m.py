import json
import sqlite3
from pathlib import Path

from app import create_app
from app.services.catalog import RecipeCatalog
from app.services.recipe1m import Recipe1MIndex
from scripts.build_recipe1m_index import build_index, iter_json_array


def write_json(path: Path, value) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def fixture_index(tmp_path: Path) -> Recipe1MIndex:
    layer1 = write_json(tmp_path / "layer1.json", [
        {
            "id": "0000000001",
            "title": "Weeknight Penne Pasta",
            "url": "https://example.com/penne",
            "partition": "train",
            "ingredients": [{"text": "8 ounces penne"}, {"text": "2 cups mushrooms"}],
            "instructions": [{"text": "Boil the pasta."}, {"text": "Fold in mushrooms."}],
        },
        {
            "id": "0000000002",
            "title": "Beef noodles",
            "url": "https://example.com/beef",
            "partition": "train",
            "ingredients": [{"text": "beef"}, {"text": "noodles"}],
            "instructions": [{"text": "Cook everything."}],
        },
        {
            "id": "0000000003",
            "title": "Pasta Primavera",
            "url": "https://example.com/primavera",
            "partition": "train",
            "ingredients": [{"text": "8 ounces pasta"}, {"text": "1 courgette"}],
            "instructions": [{"text": "Boil the pasta and fold in the vegetables."}],
        },
    ])
    layer2 = write_json(tmp_path / "layer2.json", [
        {"id": "0000000001", "images": [{"id": "abc.jpg", "url": "https://example.com/a.jpg"}]},
    ])
    nutrition = write_json(tmp_path / "nutrition.json", [
        {
            "id": "0000000001",
            "nutr_values_per100g": {"protein": 8.2, "energy": 180, "fat": 4.5},
            "weight_per_ingr": [100],
            "nutr_per_ingredient": [{"pro": 8.2, "nrg": 180, "fat": 4.5}],
        },
    ])
    database = tmp_path / "recipe1m.sqlite"
    build_index(layer1, database, layer2, nutrition)
    return Recipe1MIndex(database, tmp_path / "images")


def test_streams_top_level_json_array_in_small_chunks(tmp_path):
    path = write_json(tmp_path / "values.json", [{"value": "é" * 20}, {"value": 2}])
    assert list(iter_json_array(path, chunk_size=7)) == [{"value": "é" * 20}, {"value": 2}]


def test_builder_filters_red_meat_and_records_optional_metadata(tmp_path):
    index = fixture_index(tmp_path)
    status = index.status()
    assert status["available"] is True
    assert status["recipes"] == 2
    detail = index.detail("r1m-0000000001")
    assert detail["nutrition_basis"] == "per_100g"
    assert detail["nutrition"]["protein"] == 8.2
    assert detail["nutrition_available"] is True
    assert detail["photo"]["url"] == "/api/recipe1m/images/0000000001"
    assert index.detail("r1m-0000000002") is None
    confirmed = index.nutrition_for_servings("r1m-0000000001", 2)
    assert confirmed["nutrition"]["protein"] == 4.1
    assert confirmed["nutrition"]["calories"] == 90
    assert index.detail("r1m-0000000003")["nutrition_available"] is False


def test_local_pasta_results_join_existing_deterministic_ranking(tmp_path):
    catalog = RecipeCatalog(local_index=fixture_index(tmp_path))
    catalog.load()
    result = catalog.search("pasta", 30, 30, [], 10)
    assert result["parsed_pantry"]["recognized"] == ["pasta"]
    local = next(item for item in result["results"] if item["slug"] == "r1m-0000000001")
    assert local["name"] == "Weeknight Penne Pasta"
    assert local["total_minutes"] is None
    assert local["protein_g"] is None
    assert "local Recipe1M" in local["reasons"][1]


def test_verified_nutrition_filter_removes_unsupported_local_results(tmp_path):
    catalog = RecipeCatalog(local_index=fixture_index(tmp_path))
    catalog.load()
    unfiltered = catalog.search("pasta", 30, None, [], 10)
    filtered = catalog.search("pasta", 30, None, [], 10, verified_nutrition_only=True)

    assert any(not item["nutrition_available"] for item in unfiltered["results"])
    assert all(item["nutrition_available"] for item in filtered["results"])
    assert filtered["verified_nutrition_only"] is True
    assert filtered["nutrition_ready_count"] == filtered["total_eligible"]


def test_nutrition_label_matches_whether_a_plausible_serving_exists(tmp_path):
    index = fixture_index(tmp_path)
    # 8.2 g protein and 180 kcal in total is credible at any serving count.
    assert index.minimum_servings("r1m-0000000001") == 1
    assert index.detail("r1m-0000000001")["nutrition_available"] is True

    # A batch total can be arithmetically valid yet only divide into a real portion once the
    # serving count is high. The label must still admit that a plausible serving exists, and the
    # refusal must name the floor instead of dead-ending.
    with sqlite3.connect(index.path) as connection:
        connection.execute(
            "UPDATE recipes SET protein_total = 1075.89, calories_total = 12703.18, fat_total = 210.5 WHERE recipe_id = ?",
            ("0000000003",),
        )
    assert index.minimum_servings("r1m-0000000003") == 9
    assert index.detail("r1m-0000000003")["nutrition_available"] is True
    assert index.nutrition_for_servings("r1m-0000000003", 4) is None
    assert index.nutrition_for_servings("r1m-0000000003", 9) is not None

    # Beyond any confirmable serving count there is no plausible portion, so it is not nutrition
    # ready at all and the verified-nutrition filter must not offer it.
    with sqlite3.connect(index.path) as connection:
        connection.execute(
            "UPDATE recipes SET protein_total = 9000.0, calories_total = 90000.0, fat_total = 900.0 WHERE recipe_id = ?",
            ("0000000003",),
        )
    assert index.minimum_servings("r1m-0000000003") is None
    assert index.detail("r1m-0000000003")["nutrition_available"] is False
    filtered = index.search(["pasta"], set(), verified_nutrition_only=True)
    assert all(item["nutrition_available"] for item in filtered)
    assert "r1m-0000000003" not in {item["slug"] for item in filtered}


def test_api_names_the_serving_floor_instead_of_failing_without_guidance(tmp_path, monkeypatch):
    index = fixture_index(tmp_path)
    from app.services.recipe1m import recipe1m_index as shared_index

    monkeypatch.setattr(shared_index, "path", index.path)
    monkeypatch.setattr(shared_index, "image_cache", index.image_cache)
    client = create_app(testing=True).test_client()
    with sqlite3.connect(index.path) as connection:
        connection.execute(
            "UPDATE recipes SET protein_total = 716.15, calories_total = 15104.99, fat_total = 125.53 WHERE recipe_id = ?",
            ("0000000001",),
        )
    response = client.post("/api/recipes/r1m-0000000001/nutrition", json={"servings": 4})
    assert response.status_code == 422
    assert response.json["reason"] == "servings_too_low"
    assert response.json["minimum_servings"] == 11
    assert "11 servings or more" in response.json["error"]


def test_serving_calculation_refuses_impossible_portions(tmp_path):
    index = fixture_index(tmp_path)
    assert index.nutrition_for_servings("r1m-0000000001", 1) is not None

    # A recipe whose stored totals describe a catering batch must never be divided into one
    # human portion. This is the guard that stops absurd per-serving figures reaching the screen.
    # The runtime connection is deliberately read-only, so the fixture is edited directly.
    with sqlite3.connect(index.path) as connection:
        connection.execute(
            "UPDATE recipes SET protein_total = 1573.2, calories_total = 15200.4, fat_total = 300.0 WHERE recipe_id = ?",
            ("0000000001",),
        )
    assert index.nutrition_for_servings("r1m-0000000001", 1) is None
    # The guard is proportional, not a blanket rejection: a batch divided across a whole
    # neighbourhood is still refused, but one divided into a realistic number of portions is not.
    assert index.nutrition_for_servings("r1m-0000000001", 24) is not None


def test_local_exclusions_match_plural_ingredient_words(tmp_path):
    index = fixture_index(tmp_path)
    results = index.search(["pasta"], {"mushroom"})
    assert all(item["slug"] != "r1m-0000000001" for item in results)


def test_missing_index_keeps_public_catalog_available(tmp_path):
    catalog = RecipeCatalog(local_index=Recipe1MIndex(tmp_path / "missing.sqlite"))
    catalog.load()
    result = catalog.search("chicken rice", 30, None, [], 5)
    assert result["results"]
    assert all(item["corpus"] == "unitools" for item in result["results"])
