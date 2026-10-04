from app import create_app
from app.services.catalog import catalog, ingredient_matches
from app.services.pantry import parse_pantry
from app.services.safety import recipe_is_safe


def test_all_loaded_recipes_exclude_red_meat():
    assert catalog.recipes
    assert all(recipe_is_safe(recipe) for recipe in catalog.recipes)


def test_indian_recipes_lead_featured_results():
    featured = catalog.featured(6)
    assert featured[0]["country"] == "India"


def test_search_returns_ranked_explanations():
    result = catalog.search("chicken, rice, yogurt", 35, 90, [], 10)
    assert result["results"]
    assert len(result["results"]) <= 10
    assert result["results"][0]["reasons"]
    assert all("nutrition_available" in item for item in result["results"])
    assert result["nutrition_ready_count"] <= result["total_eligible"]


def test_space_separated_pantry_recognizes_multiple_ingredients():
    parsed = parse_pantry("chicken rice", catalog.known_terms)
    assert "chicken" in parsed["recognized"]
    assert "rice" in parsed["recognized"]
    assert set(parsed["core"]) == {"chicken", "rice"}


def test_cuisine_boost_never_beats_pantry_relevance():
    result = catalog.search("chicken rice", 30, 45, [], 20)
    assert result["results"]
    assert all(item["available_ingredients"] for item in result["results"])
    assert "palak paneer" not in {item["name"].lower() for item in result["results"]}
    assert set(result["results"][0]["available_ingredients"]) == {"chicken", "rice"}


def test_full_core_matches_own_top_results():
    result = catalog.search("chicken rice", 30, None, [], 10)
    full_matches = [item for item in result["results"] if item["full_core_match"]]
    assert len(full_matches) >= 5
    assert all(item["full_core_match"] for item in result["results"][:len(full_matches)])
    assert all(set(item["matched_core_ingredients"]) == {"chicken", "rice"} for item in full_matches)


def test_derived_ingredients_do_not_fake_core_match():
    assert not ingredient_matches("rice", "rice noodles")
    assert not ingredient_matches("chicken", "chicken stock")
    assert ingredient_matches("chicken", "chicken thighs")


def test_preferred_time_changes_order_without_filtering():
    unrestricted = catalog.search("chicken rice", 30, None, [], 30)
    preferred = catalog.search("chicken rice", 30, 30, [], 30)
    assert preferred["total_eligible"] == unrestricted["total_eligible"]
    assert any(item["total_minutes"] is None or item["total_minutes"] > 30 for item in preferred["results"])


def test_spices_do_not_dilute_core_pantry_match():
    parsed = parse_pantry("chicken, rice, bread, oregano and other spices", catalog.known_terms)
    assert set(parsed["core"]) == {"chicken", "rice", "bread"}
    assert "oregano" in parsed["basics"]
    assert "spices" in parsed["basics"]
    assert not parsed["unresolved"]


def test_common_indian_english_aliases_use_corpus_vocabulary():
    parsed = parse_pantry("bhindi, chana, rajma, chawal, shimla mirch", catalog.known_terms)
    assert set(parsed["core"]) == {"okra", "chickpeas", "red kidney beans", "rice"}
    assert "pepper" in parsed["basics"]
    assert not parsed["unresolved"]


def test_optional_exclusions_remove_matching_recipes():
    result = catalog.search("rice", 25, None, ["chicken"], 30)
    assert result["results"]
    for item in result["results"]:
        recipe = catalog.detail(item["slug"])
        ingredient_terms = {ingredient["name"].lower() for ingredient in recipe["ingredients"]}
        assert not any("chicken" in ingredient for ingredient in ingredient_terms)


def test_api_rejects_empty_pantry():
    client = create_app(testing=True).test_client()
    response = client.post("/api/recipes/search", json={"text": "", "protein_target_g": 30})
    assert response.status_code == 422


def test_api_accepts_verified_nutrition_filter():
    client = create_app(testing=True).test_client()
    response = client.post("/api/recipes/search", json={
        "text": "tofu rice",
        "protein_target_g": 30,
        "verified_nutrition_only": True,
    })
    assert response.status_code == 200
    assert response.json["verified_nutrition_only"] is True
    assert all(item["nutrition_available"] for item in response.json["results"])


def test_recipe_detail_has_attribution():
    client = create_app(testing=True).test_client()
    slug = catalog.recipes[0]["slug"]
    response = client.get(f"/api/recipes/{slug}")
    assert response.status_code == 200
    assert response.json["source"]["license"] == "CC BY-SA 4.0"
