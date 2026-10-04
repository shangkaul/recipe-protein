from difflib import SequenceMatcher

from app.models import PantryRefinement

from .ollama import LocalModelError, OllamaClient, ollama_client
from .pantry import BASIC_INGREDIENTS, normalize


COMMON_CANDIDATES = {
    "almond", "beans", "beef", "bread", "butter", "cabbage", "carrot", "cauliflower",
    "cheese", "chicken", "chickpea", "chili", "cilantro", "coconut", "cucumber", "egg",
    "eggplant", "fish", "flour", "garlic", "ginger", "kidney bean", "lentil", "milk",
    "mushroom", "mutton", "okra", "onion", "paneer", "pea", "peanut", "pepper", "pork",
    "potato", "prawn", "rice", "shrimp", "spinach", "tofu", "tomato", "tuna", "turkey",
    "yogurt",
}

SYSTEM_PROMPT = """You normalize household pantry language for recipe retrieval.
Return only the requested schema. Map each unresolved phrase to an exact candidate string only when
the meaning is clear. Do not invent candidates. Use role 'basic' for seasonings, aromatics, oil,
water, and incidental staples; otherwise use 'core'. Ignore vague phrases rather than guessing."""


def candidate_terms(unresolved: list[str], known_terms: set[str], limit: int = 120) -> list[str]:
    needles = " ".join(unresolved).split()

    def relevance(term: str) -> float:
        words = term.split()
        overlap = len(set(needles) & set(words)) * 2
        fuzzy = max((SequenceMatcher(None, needle, word).ratio() for needle in needles for word in words), default=0)
        common = 0.7 if term in COMMON_CANDIDATES else 0
        short = 0.1 if len(words) <= 2 else 0
        return overlap + fuzzy + common + short

    return sorted(known_terms, key=lambda term: (-relevance(term), len(term), term))[:limit]


class PantryRefinementService:
    def __init__(self, client: OllamaClient = ollama_client):
        self.client = client

    def refine(self, raw_text: str, parsed: dict, known_terms: set[str]) -> dict:
        deterministic = list(parsed["recognized"])
        result = {
            **parsed,
            "deterministic": deterministic,
            "refined": [],
            "mode": "deterministic",
            "model_status": {"available": True, "model": self.client.model, "reason": "not_needed"},
        }
        if not parsed["unresolved"]:
            return result

        candidates = candidate_terms(parsed["unresolved"], known_terms)
        prompt = (
            f"Pantry text: {raw_text}\n"
            f"Already recognized: {deterministic}\n"
            f"Unresolved phrases: {parsed['unresolved']}\n"
            f"Allowed canonical candidates: {candidates}"
        )
        try:
            proposal = self.client.structured(SYSTEM_PROMPT, prompt, PantryRefinement, timeout=10)
        except LocalModelError as error:
            result["mode"] = "deterministic_fallback"
            result["model_status"] = {"available": False, "model": self.client.model, "reason": error.reason}
            return result

        unresolved_by_normalized = {normalize(term): term for term in parsed["unresolved"]}
        accepted: list[tuple[str, str, str]] = []
        for term in proposal.terms:
            raw = normalize(term.raw_term)
            canonical = normalize(term.canonical_id)
            if (
                raw in unresolved_by_normalized
                and canonical in candidates
                and canonical in known_terms
                and term.confidence >= 0.65
            ):
                role = "basic" if canonical in BASIC_INGREDIENTS else term.role
                accepted.append((raw, canonical, role))

        if accepted:
            refined = list(dict.fromkeys(term for _raw, term, _role in accepted if term not in deterministic))
            basics = list(dict.fromkeys([
                *parsed["basics"], *(term for _raw, term, role in accepted if role == "basic"),
            ]))
            core = list(dict.fromkeys([
                *parsed["core"], *(term for _raw, term, role in accepted if role == "core"),
            ]))
            recognized = list(dict.fromkeys([*deterministic, *refined]))
            resolved_raw = {raw for raw, _term, _role in accepted}
            result.update({
                "recognized": recognized,
                "refined": refined,
                "core": core,
                "basics": basics,
                "unresolved": [term for term in parsed["unresolved"] if normalize(term) not in resolved_raw],
                "mode": "locally_refined",
            })
        result["model_status"] = {"available": True, "model": self.client.model, "reason": "ready"}
        return result


pantry_refinement = PantryRefinementService()
