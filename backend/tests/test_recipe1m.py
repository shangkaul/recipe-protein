import json
from pathlib import Path

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
            "ingredients": [{"text": "8 ounces penne"}, {"text": "2 cups spinach"}],
            "instructions": [{"text": "Boil the pasta."}, {"text": "Fold in spinach."}],
        },
        {
            "id": "0000000002",
            "title": "Beef noodles",
            "url": "https://example.com/beef",
            "partition": "train",
            "ingredients": [{"text": "beef"}, {"text": "noodles"}],
            "instructions": [{"text": "Cook everything."}],
        },
    ])
    layer2 = write_json(tmp_path / "layer2.json", [
        {"id": "0000000001", "images": [{"id": "abc.jpg", "url": "https://example.com/a.jpg"}]},
    ])
    nutrition = write_json(tmp_path / "nutrition.json", [
        {"id": "0000000001", "nutr_values_per100g": {"protein": 8.2, "energy": 180, "fat": 4.5}},
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
    assert status["recipes"] == 1
    detail = index.detail("r1m-0000000001")
    assert detail["nutrition_basis"] == "per_100g"
    assert detail["nutrition"]["protein"] == 8.2
    assert detail["photo"]["url"] == "/api/recipe1m/images/0000000001"
    assert index.detail("r1m-0000000002") is None


def test_local_pasta_results_join_existing_deterministic_ranking(tmp_path):
    catalog = RecipeCatalog(local_index=fixture_index(tmp_path))
    catalog.load()
    result = catalog.search("pasta", 30, 30, [], 10)
    local = next(item for item in result["results"] if item["corpus"] == "recipe1m")
    assert local["name"] == "Weeknight Penne Pasta"
    assert local["total_minutes"] is None
    assert local["protein_g"] is None
    assert "local Recipe1M" in local["reasons"][1]


def test_missing_index_keeps_public_catalog_available(tmp_path):
    catalog = RecipeCatalog(local_index=Recipe1MIndex(tmp_path / "missing.sqlite"))
    catalog.load()
    result = catalog.search("chicken rice", 30, None, [], 5)
    assert result["results"]
    assert all(item["corpus"] == "unitools" for item in result["results"])
