import re


ALIASES = {
    "aubergine": "eggplant", "brinjal": "eggplant", "baingan": "eggplant",
    "capsicum": "pepper", "bell pepper": "pepper", "chilli": "chili",
    "chillies": "chili", "chilies": "chili", "coriander": "cilantro",
    "dhania": "cilantro", "curd": "yogurt", "dahi": "yogurt",
    "garbanzo": "chickpea", "garbanzo beans": "chickpea", "chana": "chickpea",
    "rajma": "kidney bean", "dal": "lentil", "daal": "lentil",
    "moong": "mung bean", "atta": "flour", "maida": "flour",
    "aloo": "potato", "palak": "spinach", "gobi": "cauliflower",
    "matar": "pea", "mutter": "pea", "paneer cheese": "paneer",
    "scallion": "spring onion", "green onion": "spring onion",
}

STOPWORDS = {
    "and", "with", "some", "a", "an", "the", "other", "leftover", "fresh", "frozen",
    "going", "soft", "about", "of", "plus", "have", "i", "we", "use", "please",
}

BASIC_INGREDIENTS = {
    "salt", "pepper", "black pepper", "white pepper", "water", "oil", "olive oil",
    "vegetable oil", "cooking oil", "sugar", "garlic", "ginger", "onion", "butter",
    "chili", "cilantro", "coriander", "cumin", "turmeric", "paprika", "cinnamon",
    "oregano", "thyme", "rosemary", "basil", "mint", "parsley", "cardamom",
    "clove", "cloves", "nutmeg", "seasoning", "spice", "spices", "herb", "herbs",
}

GENERIC_BASICS = {"seasoning", "seasonings", "spice", "spices", "herb", "herbs"}


def normalize(value: str) -> str:
    value = value.replace("-", " ")
    value = re.sub(r"[^a-z0-9\s]", " ", value.lower())
    value = re.sub(r"\s+", " ", value).strip()
    return ALIASES.get(value, value)


def parse_pantry(text: str, known_terms: set[str]) -> dict:
    chunks = re.split(r"[,;\n]+|\band\b|\bplus\b", text.lower())
    display, recognized, generic_basics, unresolved = [], [], [], []
    for chunk in chunks:
        cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l|cups?|tbsp|tsp|pieces?)?\b", "", chunk)
        words = [word for word in cleaned.split() if word not in STOPWORDS]
        display_term = normalize(" ".join(words))
        if not display_term:
            continue
        display.append(display_term)

        normalized_words = display_term.split()
        consumed: set[int] = set()
        for size in range(min(4, len(normalized_words)), 0, -1):
            for start in range(len(normalized_words) - size + 1):
                positions = set(range(start, start + size))
                if positions & consumed:
                    continue
                phrase = " ".join(normalized_words[start:start + size])
                canonical = ALIASES.get(phrase, phrase)
                if canonical in known_terms or any(canonical == term for term in known_terms):
                    recognized.append(canonical)
                    consumed.update(positions)

        leftover = [word for index, word in enumerate(normalized_words) if index not in consumed]
        if leftover:
            leftover_term = " ".join(leftover)
            if leftover_term in GENERIC_BASICS:
                generic_basics.append(leftover_term)
            else:
                unresolved.append(leftover_term)
    return {
        "display_terms": list(dict.fromkeys(display)),
        "recognized": list(dict.fromkeys(recognized)),
        "core": list(dict.fromkeys(term for term in recognized if term not in BASIC_INGREDIENTS)),
        "basics": list(dict.fromkeys([*(term for term in recognized if term in BASIC_INGREDIENTS), *generic_basics])),
        "unresolved": list(dict.fromkeys(unresolved)),
    }
