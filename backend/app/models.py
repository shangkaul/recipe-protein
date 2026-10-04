from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


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


class AdaptRequest(BaseModel):
    pantry: str = Field(min_length=1, max_length=1000)
    protein_target_g: float = Field(default=30, ge=5, le=100)


class ModelChange(BaseModel):
    action: Literal["add", "increase"]
    ingredient_id: str
    quantity_g: float = Field(gt=0, le=500)
    reason: str = Field(min_length=1, max_length=180)


class ModelAdaptation(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    changes: list[ModelChange] = Field(min_length=1, max_length=3)
    instruction_notes: list[str] = Field(default_factory=list, max_length=4)


JsonDict = dict[str, Any]
