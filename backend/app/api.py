from flask import Blueprint, jsonify, request, send_file
from pydantic import ValidationError

from .models import AdaptRequest, PantryRequest, ServingRequest
from .services.adaptation import AdaptationFailure, adaptation_service
from .services.catalog import catalog
from .services.ollama import LocalModelError, ollama_client
from .services.recipe1m import recipe1m_index


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "recipes": len(catalog.recipes),
        "local_model": ollama_client.status().as_dict(),
        "recipe1m": recipe1m_index.status(),
    })


@api.get("/recipes/featured")
def featured():
    limit = min(max(request.args.get("limit", default=12, type=int), 1), 30)
    category = request.args.get("category")
    return jsonify({"results": catalog.featured(limit, category), "source": catalog.meta})


@api.post("/recipes/search")
def search():
    try:
        payload = PantryRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({"error": "Check your pantry details", "details": error.errors(include_url=False)}), 422
    return jsonify(catalog.search(
        payload.text, payload.protein_target_g, payload.preferred_minutes,
        payload.exclusions, payload.limit, payload.verified_nutrition_only,
    ))


@api.get("/recipes/<slug>")
def recipe_detail(slug: str):
    recipe = catalog.detail(slug)
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404
    return jsonify(recipe)


@api.get("/recipe1m/images/<recipe_id>")
def recipe1m_image(recipe_id: str):
    image = recipe1m_index.cached_image(recipe_id)
    if not image:
        return jsonify({"error": "Image unavailable"}), 404
    return send_file(image, max_age=86_400)


@api.post("/recipes/<slug>/nutrition")
def confirmed_nutrition(slug: str):
    try:
        payload = ServingRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({"error": "Choose between 1 and 24 servings", "details": error.errors(include_url=False)}), 422
    if not catalog.detail(slug):
        return jsonify({"error": "Recipe not found"}), 404
    result = catalog.nutrition_for_servings(slug, payload.servings)
    if not result:
        minimum = catalog.minimum_servings(slug)
        if minimum:
            return jsonify({
                "error": f"This recipe only divides into a plausible portion at {minimum} servings or more",
                "reason": "servings_too_low",
                "minimum_servings": minimum,
            }), 422
        return jsonify({
            "error": "Verified ingredient nutrition is unavailable for this recipe",
            "reason": "nutrition_unavailable",
        }), 422
    return jsonify(result)


@api.post("/recipes/<slug>/adapt")
def adapt_recipe(slug: str):
    recipe = catalog.detail(slug)
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404
    try:
        payload = AdaptRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return jsonify({"error": "Check the adaptation details", "details": error.errors(include_url=False)}), 422
    servings = recipe["servings"] or payload.servings
    if not servings:
        return jsonify({"error": "Confirm the recipe servings before adapting it", "reason": "servings_required"}), 422
    nutrition_result = catalog.nutrition_for_servings(slug, servings)
    if not nutrition_result:
        return jsonify({"error": "Verified source nutrition is unavailable for adaptation", "reason": "nutrition_unavailable"}), 422
    try:
        result = adaptation_service.adapt(
            recipe, payload.pantry, payload.protein_target_g, payload.exclusions,
            servings, nutrition_result["nutrition"],
        )
    except AdaptationFailure as error:
        messages = {
            "target_already_met": "This recipe already meets your protein target, so no increase is needed",
            "no_supported_pantry_ingredients": "No pantry ingredient has a verified local nutrient record for adaptation",
            "ingredient_not_in_source": "The proposed increase was not present in the source recipe",
            "excluded_ingredient": "The proposal used an ingredient you chose to avoid",
            "unsafe_proposal": "The proposal did not pass the red-meat safety check",
            "impractical_quantity": "The local proposal used an impractical quantity, so it was not applied",
            "excessive_quantity": "The local proposal asked for more than a practical kitchen amount",
            "no_meaningful_increase": "None of your pantry ingredients would meaningfully raise the protein in this recipe",
        }
        return jsonify({
            "error": messages.get(error.reason, "This adaptation could not be safely validated"),
            "reason": error.reason,
        }), 422
    except LocalModelError as error:
        messages = {
            "service_unavailable": "Start Ollama on this device, then try the adaptation again",
            "model_missing": f"Install the {adaptation_service.client.model} model in Ollama, then try again",
            "timeout": "The local model took too long; the original recipe is unchanged",
            "invalid_output": "The local proposal could not be safely validated; the original recipe is unchanged",
        }
        return jsonify({"error": messages.get(error.reason, "Local adaptation is unavailable"), "reason": error.reason}), 503
    return jsonify(result)
