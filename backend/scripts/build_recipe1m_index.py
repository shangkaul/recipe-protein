#!/usr/bin/env python3
import argparse
import json
import math
import sqlite3
import sys
import time
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.services.safety import contains_red_meat  # noqa: E402


SCHEMA = """
CREATE TABLE recipes (
    rowid INTEGER PRIMARY KEY,
    recipe_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    partition_name TEXT,
    ingredients_json TEXT NOT NULL,
    instructions_json TEXT NOT NULL,
    image_id TEXT,
    image_url TEXT,
    protein_per_100g REAL,
    calories_per_100g REAL,
    fat_per_100g REAL
);
CREATE VIRTUAL TABLE recipe_fts USING fts5(
    recipe_id UNINDEXED, title, ingredients_json, instructions_json,
    content='recipes', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX recipes_recipe_id ON recipes(recipe_id);
"""


def iter_json_array(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[dict]:
    """Yield values from a top-level JSON array without retaining the full file."""
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8") as source:
        buffer = ""
        position = 0
        started = False
        eof = False
        while True:
            if position > chunk_size:
                buffer = buffer[position:]
                position = 0
            if not eof and len(buffer) - position < chunk_size:
                chunk = source.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
            while position < len(buffer) and buffer[position].isspace():
                position += 1
            if not started:
                if position >= len(buffer) and not eof:
                    continue
                if position >= len(buffer) or buffer[position] != "[":
                    raise ValueError(f"{path} is not a top-level JSON array")
                position += 1
                started = True
                continue
            while position < len(buffer) and (buffer[position].isspace() or buffer[position] == ","):
                position += 1
            if position < len(buffer) and buffer[position] == "]":
                return
            try:
                value, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                if eof:
                    raise ValueError(f"Incomplete JSON value in {path}")
                chunk = source.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
                continue
            yield value
            position = end


def create_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".building")
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    connection.executescript(SCHEMA)
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    return connection


def build_index(layer1: Path, output: Path, layer2: Path | None = None, nutrition: Path | None = None) -> dict:
    started = time.monotonic()
    connection = create_database(output)
    temporary = Path(connection.execute("PRAGMA database_list").fetchone()[2])
    scanned = safe = excluded = 0
    try:
        for item in iter_json_array(layer1):
            scanned += 1
            ingredients = [part.get("text", "").strip() for part in item.get("ingredients", []) if part.get("text", "").strip()]
            instructions = [part.get("text", "").strip() for part in item.get("instructions", []) if part.get("text", "").strip()]
            title = item.get("title", "").strip()
            safety_text = " ".join([title, *ingredients, *instructions])
            if not title or not ingredients or contains_red_meat(safety_text):
                excluded += 1
                continue
            cursor = connection.execute(
                """INSERT INTO recipes
                   (recipe_id, title, source_url, partition_name, ingredients_json, instructions_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    item["id"], title, item.get("url", ""), item.get("partition"),
                    json.dumps(ingredients, ensure_ascii=False),
                    json.dumps(instructions, ensure_ascii=False),
                ),
            )
            connection.execute(
                "INSERT INTO recipe_fts(rowid, recipe_id, title, ingredients_json, instructions_json) VALUES (?, ?, ?, ?, ?)",
                (cursor.lastrowid, item["id"], title, " ".join(ingredients), " ".join(instructions)),
            )
            safe += 1
            if scanned % 10_000 == 0:
                connection.commit()

        images = _attach_images(connection, layer2) if layer2 else 0
        nutrition_count = _attach_nutrition(connection, nutrition) if nutrition else 0
        metadata = {
            "schema_version": "1", "source_recipes": str(scanned), "safe_recipes": str(safe),
            "excluded_recipes": str(excluded), "image_recipes": str(images),
            "nutrition_recipes": str(nutrition_count), "complete": "1",
        }
        connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items())
        connection.commit()
        connection.execute("PRAGMA optimize")
        connection.execute("VACUUM")
        connection.close()
        temporary.replace(output)
        return {**metadata, "seconds": round(time.monotonic() - started, 2), "bytes": output.stat().st_size}
    except BaseException:
        connection.close()
        temporary.unlink(missing_ok=True)
        raise


def _attach_images(connection: sqlite3.Connection, path: Path) -> int:
    attached = 0
    for item in iter_json_array(path):
        images = item.get("images") or []
        if not images:
            continue
        image = images[0]
        cursor = connection.execute(
            "UPDATE recipes SET image_id = ?, image_url = ? WHERE recipe_id = ?",
            (image.get("id"), image.get("url"), item.get("id")),
        )
        attached += cursor.rowcount
    connection.commit()
    return attached


def _attach_nutrition(connection: sqlite3.Connection, path: Path) -> int:
    attached = 0
    for item in iter_json_array(path):
        values = item.get("nutr_values_per100g") or {}
        protein, calories, fat = values.get("protein"), values.get("energy"), values.get("fat")
        if not _plausible_nutrition(protein, calories, fat):
            continue
        cursor = connection.execute(
            """UPDATE recipes SET protein_per_100g = ?, calories_per_100g = ?, fat_per_100g = ?
               WHERE recipe_id = ?""",
            (round(protein, 2), round(calories, 2), round(fat, 2), item.get("id")),
        )
        attached += cursor.rowcount
    connection.commit()
    return attached


def _plausible_nutrition(protein, calories, fat) -> bool:
    values = (protein, calories, fat)
    return all(isinstance(value, (int, float)) and math.isfinite(value) for value in values) and (
        0 <= protein <= 100 and 0 <= calories <= 900 and 0 <= fat <= 100
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a private local Recipe1M SQLite FTS5 index")
    parser.add_argument("--layer1", type=Path, required=True)
    parser.add_argument("--layer2", type=Path)
    parser.add_argument("--nutrition", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / "data" / "recipe1m.sqlite")
    args = parser.parse_args()
    result = build_index(args.layer1, args.output, args.layer2, args.nutrition)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
