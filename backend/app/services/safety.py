import re


RED_MEAT_TERMS = (
    "beef", "veal", "lamb", "mutton", "pork", "ham", "bacon", "guanciale",
    "pancetta", "prosciutto", "salami", "pepperoni", "lard", "gelatin",
    "gelatine", "venison", "goat", "bison", "boar", "oxtail",
)
RED_MEAT_RE = re.compile(r"\b(?:" + "|".join(RED_MEAT_TERMS) + r")\b", re.I)


def contains_red_meat(text: str) -> bool:
    return bool(RED_MEAT_RE.search(text))


def recipe_is_safe(recipe: dict) -> bool:
    parts = [recipe.get("name", {}).get("en", ""), recipe.get("summary", {}).get("en", "")]
    parts.extend(item.get("name", {}).get("en", "") for item in recipe.get("ingredients", []))
    return not contains_red_meat(" ".join(parts))
