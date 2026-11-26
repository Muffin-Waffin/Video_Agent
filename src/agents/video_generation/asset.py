from __future__ import annotations

import json
from pathlib import Path
from typing import NotRequired, TypedDict
from langchain_chroma import Chroma
from rich import print
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from agents.models import (
    AssetDesc,
    AssetDescBatch,
    AssetSelection,
    EntityModel,
    StoryScriptModel,
)
from agents.video_generation.prompt import asset_desc_prompt, asset_list_prompt
from agents.video_generation.video_stuff.guideline_loader import (
    embeddings,
    retrieve_visual_guidelines,
)

load_dotenv()


CATALOGUE_PATH = Path(
    "/Users/xon/company/Video_Agent/entity_extraction/available_kenney_assets.json"
)


def load_asset_catalogue(path: Path = CATALOGUE_PATH) -> list[dict]:
    """Load the Kenney catalogue and return its asset records."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Asset catalogue not found: {path.resolve()}\n"
            "Update CATALOGUE_PATH to the location of "
            "available_kenney_assets.json."
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # The generated catalogue is expected to contain {"assets": [...]}.
    # Accept a plain list as well, in case the JSON was exported that way.
    assets = data["assets"] if isinstance(data, dict) else data

    if not isinstance(assets, list):
        raise ValueError("The asset catalogue must contain a list of assets.")

    required_fields = {"asset_id", "name", "relative_path"}
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict) or not required_fields.issubset(asset):
            raise ValueError(
                f"Invalid catalogue record at index {index}. "
                f"Expected fields: {sorted(required_fields)}"
            )

    return assets


ASSET_CATALOGUE = load_asset_catalogue()

# Keep the prompt compact. The model only needs to choose an asset ID.
ASSET_CATALOGUE_FOR_LLM = [
    {
        "asset_id": asset["asset_id"],
        "name": asset["name"],
        "pack": asset.get("pack", ""),
    }
    for asset in ASSET_CATALOGUE
]

VALID_ASSET_IDS = {asset["asset_id"] for asset in ASSET_CATALOGUE}

_CHROMA_DIR = Path("/Users/xon/company/Video_Agent/kenney_chroma_db")
_KENNEY_STORE: Chroma | None = None


def _get_kenney_store() -> Chroma:
    """Return (and lazily populate) the Chroma vector store for Kenney assets using NVIDIAEmbeddings."""
    global _KENNEY_STORE
    if _KENNEY_STORE is not None:
        return _KENNEY_STORE

    store = Chroma(
        collection_name="kenney_assets",
        embedding_function=embeddings,
        persist_directory=str(_CHROMA_DIR),
    )
    if store._collection.count() == 0 and ASSET_CATALOGUE_FOR_LLM:
        store.add_texts(
            texts=[f"{a['name']} ({a['pack']})" for a in ASSET_CATALOGUE_FOR_LLM],
            metadatas=ASSET_CATALOGUE_FOR_LLM,
            ids=[a["asset_id"] for a in ASSET_CATALOGUE_FOR_LLM],
        )
    _KENNEY_STORE = store
    return store


def retrieve_candidate_assets(entities: list[str], top_k: int = 3) -> list[dict]:
    """Retrieve only the top-k matching Kenney assets per entity from ChromaDB."""
    if not entities:
        return []
    store = _get_kenney_store()
    seen: set[str] = set()
    candidates: list[dict] = []
    for entity in entities:
        docs = store.similarity_search(entity, k=top_k)
        for doc in docs:
            meta = doc.metadata
            aid = meta["asset_id"]
            if aid not in seen:
                seen.add(aid)
                candidates.append(meta)
    return candidates


class EntityState(TypedDict):
    script: StoryScriptModel
    entity: NotRequired[EntityModel]
    selected_assets: NotRequired[list[str]]
    missing_assets: NotRequired[list[str]]
    assets: NotRequired[AssetDescBatch]



llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
)

entity_prompt = ChatPromptTemplate(
    [
        ("system", asset_list_prompt),
        (
            "human",
            """
You are receiving a StoryScriptModel.

Visual guidelines:
{guideline}

Story script:
{storyscript}

Identify every visual entity required to represent the story through
animation. Categorize each entity into the supplied EntityModel schema:
environment, living_objects, non_living_objects, and extras.

Do not generate asset descriptions or select catalogue assets.
Return only the structured entity extraction result.
""",
        ),
    ]
)

entity_chain = entity_prompt | llm.with_structured_output(EntityModel)

asset_selection_prompt = ChatPromptTemplate(
    [
        (
            "system",
            """
You are an asset-selection agent.

For every required entity, find the best matching asset in the supplied
catalogue.

Rules:
- Select only exact asset_id values that appear in the catalogue.
- Do not invent, modify, or approximate asset IDs.
- Prefer a semantically and visually suitable match.
- If no suitable asset exists, put the original entity name in missing_assets.
- Do not omit any required entity.
- Do not put an entity in both available_assets and missing_assets.
- Return the result using the supplied AssetSelection schema.
""",
        ),
        (
            "human",
            """
Required entities:
{entities}

Available asset catalogue:
{asset_catalogue}
""",
        ),
    ]
)

asset_selector = (
    asset_selection_prompt
    | llm.with_structured_output(AssetSelection)
)


asset_description_prompt = ChatPromptTemplate(
    [
        ("system", asset_desc_prompt),
        (
            "human",
            """
Generate a visual description for this asset that will need to be created.

Asset name: {asset_name}
Asset category: {category}

Visual guidelines:
{guideline}

Describe its visible appearance in a way that can guide later asset creation:
- overall shape and silhouette
- proportions and distinctive features
- materials and surface details
- colors and visual style

Keep the description consistent with the supplied guidelines.
Do not select an existing catalogue asset.
Do not generate code.
Return the result using the supplied AssetDesc schema.
""",
        ),
    ]
)

asset_desc_llm = llm.with_structured_output(AssetDesc)
asset_chain = asset_description_prompt | asset_desc_llm



def get_asset_list(state: EntityState) -> dict:
    """Extract visual entities from the story script."""
    script = state["script"]

    guidelines = retrieve_visual_guidelines(
        query="visual style, environments, characters and objects for this story",
        k=7,
    )

    result = entity_chain.invoke(
        {
            "guideline": guidelines,
            "storyscript": script,
        }
    )

    return {"entity": result}


def select_assets(state: EntityState) -> dict:
    """Match extracted entities against the available Kenney catalogue."""
    entities = state["entity"]

    all_entities = (
        entities.environment
        + entities.living_objects
        + entities.non_living_objects
        + entities.extras
    )

    # Preserve order while removing duplicate names.
    all_entities = list(dict.fromkeys(all_entities))

    candidate_assets = retrieve_candidate_assets(all_entities, top_k=3)

    result = asset_selector.invoke(
        {
            "entities": json.dumps(all_entities, ensure_ascii=False),
            "asset_catalogue": json.dumps(
                candidate_assets,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
    )

    # Validate every ID returned by the model against the real catalogue.
    selected_assets = list(
        dict.fromkeys(
            asset_id
            for asset_id in result.available_assets
            if asset_id in VALID_ASSET_IDS
        )
    )

    # If the model returned an unknown ID, treat it as an invalid selection.
    invalid_ids = [
        asset_id
        for asset_id in result.available_assets
        if asset_id not in VALID_ASSET_IDS
    ]

    missing_assets = list(
        dict.fromkeys(result.missing_assets + invalid_ids)
    )

    return {
        "selected_assets": selected_assets,
        "missing_assets": missing_assets,
    }


def get_asset_desc(asset_name: str, category: str) -> AssetDesc:
    """Generate a description for one entity that has no catalogue match."""
    guidelines = retrieve_visual_guidelines(
        query=f"{category} asset: {asset_name}",
        k=4,
    )

    return asset_chain.invoke(
        {
            "asset_name": asset_name,
            "category": category,
            "guideline": guidelines,
        }
    )


def asset_description(state: EntityState) -> dict:
    """Describe only missing entities, retaining their original categories."""
    entities = state["entity"]
    missing = set(state.get("missing_assets", []))

    category_groups = {
        "environment": entities.environment,
        "living_objects": entities.living_objects,
        "non_living_objects": entities.non_living_objects,
        "extras": entities.extras,
    }

    descriptions: list[AssetDesc] = []

    for category, names in category_groups.items():
        for asset_name in names:
            if asset_name not in missing:
                continue

            description = get_asset_desc(asset_name, category)
            descriptions.append(description)

    batch = AssetDescBatch(assets=descriptions)

    # Optional debug output. The graph state remains the source of truth.
    output_path = Path("output.json")
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(batch.model_dump(), file, indent=4, ensure_ascii=False)

    return {"assets": batch}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

graph = StateGraph(EntityState)

graph.add_node("entity_list", get_asset_list)
graph.add_node("asset_selection", select_assets)
graph.add_node("asset_desc", asset_description)

graph.add_edge(START, "entity_list")
graph.add_edge("entity_list", "asset_selection")
graph.add_edge("asset_selection", "asset_desc")
graph.add_edge("asset_desc", END)

get_asset = graph.compile()
