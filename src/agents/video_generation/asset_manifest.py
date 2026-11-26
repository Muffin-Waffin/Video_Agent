from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agents.models import AssetDescBatch


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RENDERER_ROOT = PROJECT_ROOT / "renderer"
COMPONENT_CATALOGUE_PATH = RENDERER_ROOT / "engine" / "catalogue" / "component_catalogue.json"
STORIES_ROOT = RENDERER_ROOT / "stories"


def slugify_story_id(title: str) -> str:
    """Convert a story title into a deterministic, filesystem-safe story_id."""
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug or "generated_story"


def load_component_catalogue(path: Path = COMPONENT_CATALOGUE_PATH) -> dict[str, Any]:
    """Load the machine-readable component catalogue for LLM context."""
    if not path.is_file():
        raise FileNotFoundError(f"Component catalogue not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_asset_manifest(
    story_id: str,
    selected_asset_ids: list[str],
    missing_assets: AssetDescBatch | None,
    catalogue_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Build a deterministic asset_manifest.json structure.
    Distinguishes between existing catalogue assets and story-specific assets.
    """
    catalogue_by_id = {
        rec["asset_id"]: rec for rec in (catalogue_records or []) if "asset_id" in rec
    }
    manifest_assets: dict[str, dict[str, Any]] = {}

    for asset_id in selected_asset_ids:
        rec = catalogue_by_id.get(asset_id, {})
        manifest_assets[asset_id] = {
            "asset_id": asset_id,
            "name": rec.get("name", asset_id),
            "category": rec.get("category", "non_living_objects"),
            "asset_type": rec.get("asset_type", "3d_model"),
            "file_path": rec.get("relative_path", f"assets/{asset_id}"),
            "reusable": True,
            "metadata": {"source": "catalogue", "pack": rec.get("pack", "")},
        }

    if missing_assets:
        for asset in missing_assets.assets:
            manifest_assets[asset.asset_id] = {
                "asset_id": asset.asset_id,
                "name": asset.name,
                "category": asset.category,
                "asset_type": asset.asset_type,
                "file_path": f"stories/{story_id}/assets/{asset.asset_id}.json",
                "reusable": asset.reusable,
                "metadata": {
                    "source": "generated_story_asset",
                    "visual_description": asset.visual_description,
                },
            }

    return {"story_id": story_id, "assets": manifest_assets}


def write_asset_manifest(story_id: str, manifest: dict[str, Any]) -> Path:
    """Persist asset_manifest.json into renderer/stories/<story_id>/."""
    story_dir = STORIES_ROOT / story_id
    story_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = story_dir / "asset_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path
