from flask import Blueprint, jsonify, request, send_file
from pydantic import ValidationError

from .models import PantryRequest
from .services.catalog import catalog
from .services.ollama import ollama_client
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
        payload.exclusions, payload.limit,
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
