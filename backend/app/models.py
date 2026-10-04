from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PantryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    protein_target_g: float = Field(default=30, ge=5, le=100)
    preferred_minutes: int | None = Field(default=None, ge=5, le=240)
    exclusions: list[str] = Field(default_factory=list)
    limit: int = Field(default=24, ge=1, le=30)

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not any(char.isalpha() for char in value):
            raise ValueError("Add at least one ingredient name")
        return value

    @field_validator("exclusions")
    @classmethod
    def clean_exclusions(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if len(cleaned) > 20 or any(len(value) > 80 for value in cleaned):
            raise ValueError("Use at most 20 excluded ingredients")
        return list(dict.fromkeys(cleaned))


class RefinedTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_term: str = Field(min_length=1, max_length=120)
    canonical_id: str = Field(min_length=1, max_length=120)
    role: Literal["core", "basic"]
    confidence: float = Field(ge=0, le=1)


class IgnoredTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_term: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=180)


class PantryRefinement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terms: list[RefinedTerm] = Field(default_factory=list, max_length=20)
    ignored_terms: list[IgnoredTerm] = Field(default_factory=list, max_length=20)


class AdaptRequest(BaseModel):
    pantry: str = Field(min_length=1, max_length=1000)
    protein_target_g: float = Field(default=30, ge=5, le=100)
    exclusions: list[str] = Field(default_factory=list, max_length=20)
    servings: int | None = Field(default=None, ge=1, le=24)


class ServingRequest(BaseModel):
    servings: int = Field(ge=1, le=24)


class ModelChange(BaseModel):
    action: Literal["add", "increase"]
    ingredient_id: Literal[
        "chicken", "tofu", "egg", "lentils", "chickpeas", "greek-yogurt",
        "tuna", "shrimp", "cottage-cheese",
    ]
    quantity_g: float = Field(gt=0, le=500)
    reason: str = Field(min_length=1, max_length=180)


class ModelAdaptation(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    changes: list[ModelChange] = Field(min_length=1, max_length=3)
    instruction_notes: list[str] = Field(default_factory=list, max_length=4)


JsonDict = dict[str, Any]
