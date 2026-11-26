from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agents.models import AssetDescBatch, ShotBatch, StoryScriptModel
from agents.video_generation.asset import ASSET_CATALOGUE
from agents.video_generation.asset_manifest import (
    RENDERER_ROOT,
    STORIES_ROOT,
    build_asset_manifest,
    load_component_catalogue,
    slugify_story_id,
    write_asset_manifest,
)

load_dotenv()


class SceneProp(BaseModel):
    name: str = Field(description="Exact .glb stem from KENNEY_ASSETS or procedural shape name.")
    pos: list[float] = Field(description="[x, y, z] position.")
    scale: float = Field(default=1.0, description="Uniform scale.")
    color: str = Field(default="#8899aa", description="Hex color for procedural fallback.")


class SceneCharacter(BaseModel):
    char_id: str = Field(description="Unique character identifier.")
    shirt: str = Field(default="#3a6ea5")
    pants: str = Field(default="#2c3440")
    hair: str = Field(default="#2a1d18")
    start_pos: list[float] = Field(description="[x, y, z] starting position.")


class SceneBeat(BaseModel):
    shot_id: int = Field(description="1-indexed shot ID.")
    start_frame: int
    end_frame: int
    light: str = Field(default="day", description="'day' or 'golden'.")
    cam_pos_start: list[float]
    cam_pos_end: list[float]
    cam_look: list[float]
    actions: str = Field(description="Concrete character movements, expressions (neutral/shock/smug/happy), and prop animations timed to words.")


class ScenePlan(BaseModel):
    environment_summary: str = Field(description="Ground, sky, and backdrop description.")
    props: list[SceneProp]
    characters: list[SceneCharacter]
    beats: list[SceneBeat]


class GeneratedStoryFiles(BaseModel):
    story_ts: str = Field(description="Shot timeline, SHOTS, XFADE, FLASH_AT, CAMS, KICKS, DOF/dofAt, FOREGROUND.")
    build_ts: str = Field(description="World/town/props layout and sight-line culling matching bridge/build.ts exports.")
    cast_ts: str = Field(description="Character billboards, crowds, effect cards, blinks, and walk cycles matching bridge/cast.ts exports.")


class VideoGenState(TypedDict):
    script: StoryScriptModel
    assets: AssetDescBatch
    selected_assets: NotRequired[list[str]]
    shot_direction: ShotBatch
    words_json_path: NotRequired[str]
    story_id: NotRequired[str]
    story_dir: NotRequired[str]
    validation_ok: NotRequired[bool]
    validation_errors: NotRequired[list[str]]


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
)

scene_plan_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a 3D Scene Planner for vertical (1080x1920) 30fps cartoon shorts.
Given the SCRIPT, WORD_TIMINGS, SHOT_PLAN, and ASSET_MANIFEST, design a concrete ScenePlan:
- Place characters (`[x, y, z]` around `y=0`, `x` in `[-4, 4]`, `z` in `[-6, 4]`) and props (using ONLY exact `.glb` stems from `source: "catalogue"` assets in `ASSET_MANIFEST`, plus procedural props).
- Choreograph every shot (`1..N`) with camera start/end positions, look targets, lighting (`day`/`golden`), and exact character expressions (`neutral`, `shock`, `smug`, `happy`) + movements timed to `WORD_TIMINGS`.""",
        ),
        (
            "human",
            """TITLE: {title}
SCRIPT: {script_text}
WORD_TIMINGS: {word_timings}
SHOT_PLAN: {shot_plan}
ASSET_MANIFEST: {asset_manifest}""",
        ),
    ]
)

scene_plan_chain = scene_plan_prompt | llm.with_structured_output(ScenePlan)

tsx_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a Remotion/Three.js Scene Director for the 2D-in-3D cartoon short engine (`story_template`).
Generate ONLY the three story-specific TypeScript files (`story.ts`, `build.ts`, `cast.ts`) that plug into `Bridge.tsx` and `world.ts`.

EXACT EXPORTS REQUIRED:
1. `story.ts`:
   - `export type V3 = [number, number, number];`
   - `export type Light = "day" | "golden";`
   - `export type ShotDef = {{ id: number; a: number; b: number; light: Light }};`
   - `export type Cam = {{ pos: V3; look: V3; fov: number; roll: number }};`
   - `export const TOTAL: number` (total frames at 30 fps)
   - `export const FLASH_AT: number` (frame for white flash after hook, or -1)
   - `export const SHOTS: ShotDef[]` (1-indexed `id: 1..N`, contiguous `a`..`b` frames)
   - `export const layersAt = (f: number): {{ id: number; alpha: number }}[] => ...`
   - `export const camAt = (id: number, f: number): Cam => ...` (creeping holds, smootherstep glides, 4-4.6 deg rolls)
   - `export const dofAt = (f: number): {{ cInf: number; focus?: (f: number) => V3 }} => ...`
2. `build.ts`:
   - `export type Kit = Record<string, THREE.Object3D>;`
   - `export const KENNEY_ASSETS: string[] = [...];` (ONLY exact `.glb` stems from `file_path` of `source: "catalogue"` entries in `ASSET_MANIFEST`, e.g. `"computerScreen"`, NEVER `missing_assets` IDs).
   - `export function buildWorld(root: THREE.Group, kit: Kit): {{ update?: (f: number) => void }} | void` (ALWAYS build a rich procedural 3D environment matching the story—ground plane, buildings/rooms/screens/props with Three.js geometry + `MeshStandardMaterial` + cloned `kit[name]` props—and animate world props per frame `f` in `update(f)`).
3. `cast.ts`:
   - `export function buildCast(root: THREE.Group): {{ update?: (f: number, cam: THREE.PerspectiveCamera) => void }} | void`
   - Import `drawBeanCard` from `./toon` and `NOINK` from `./ink`! Create multiple distinct 2D bean-head characters + story props on 256x512 `HTMLCanvasElement`s using `drawBeanCard(ctx, {{ shirt, pants, hair, expr, armAngle }})` + `THREE.CanvasTexture` sprites/planes on layer `NOINK`.
   - In `update(f, cam)`, animate character positions, walk bob, reactions, and visibility per shot/word timing so the characters act out what the `SCRIPT` says!

STRICT RULES:
- Time every visual reaction, cut, and camera movement 0-3 frames before its word in `WORD_TIMINGS` (30 fps).
- All engine files (`./toon`, `./ink`, `./world`, `./cardshade`, `./shade`, `./paint`, `./lights`) are in the SAME directory — NEVER import from `./bridge` or `../../bridge/`. Always declare `V3`, `Light`, `ShotDef`, `Cam` directly in `story.ts` and `Kit` directly in `build.ts`.
- Pure TypeScript ONLY — NEVER write JSX/React tags (`<group>`, `<mesh>`, etc.) in `.ts` files.""",
        ),
        (
            "human",
            """STORY_ID: {story_id}
TITLE: {title}
SCRIPT: {script_text}

WORD_TIMINGS (words.json, 30 fps):
{word_timings}

SHOT_PLAN:
{shot_plan}

SCENE_PLAN:
{scene_plan}

ASSET_MANIFEST:
{asset_manifest}

Generate `story.ts`, `build.ts`, and `cast.ts` implementing every prop, character, camera move, and action in SCENE_PLAN.""",
        ),
    ]
)

tsx_chain = tsx_prompt | llm.with_structured_output(GeneratedStoryFiles)

BRIDGE_TEMPLATE_DIR = RENDERER_ROOT / "src" / "videos" / "story_template"


def write_story_files(story_id: str, files: GeneratedStoryFiles) -> Path:
    """Copy the fixed bridge engine to renderer/src/videos/<story_id>/ and write story.ts, build.ts, cast.ts."""
    story_dir = RENDERER_ROOT / "src" / "videos" / story_id
    story_dir.mkdir(parents=True, exist_ok=True)
    if BRIDGE_TEMPLATE_DIR.exists():
        for item in BRIDGE_TEMPLATE_DIR.iterdir():
            if item.is_file() and item.name not in {"story.ts", "build.ts", "cast.ts"}:
                shutil.copy2(item, story_dir / item.name)

    mapping = {
        "story.ts": files.story_ts,
        "build.ts": files.build_ts,
        "cast.ts": files.cast_ts,
    }
    for filename, content in mapping.items():
        (story_dir / filename).write_text(content, encoding="utf-8")
    register_story_in_root(story_id)
    return story_dir


def register_story_in_root(story_id: str, duration_in_frames: int = 2010) -> None:
    """Register <Composition id={comp_id}> in renderer/src/Root.tsx if not already present."""
    root_path = RENDERER_ROOT / "src" / "Root.tsx"
    if not root_path.exists():
        return
    text = root_path.read_text(encoding="utf-8")
    comp_id = story_id.replace("_", "-")
    comp_name = "".join(part.capitalize() for part in story_id.split("_") if part) or "GeneratedStory"
    import_line = f'import {{ BridgeShort as {comp_name} }} from "./videos/{story_id}/Bridge";'
    if f'id="{comp_id}"' in text:
        return

    if import_line not in text:
        text = text.replace(
            'import { BridgeShort } from "./videos/bridge/Bridge";',
            f'import {{ BridgeShort }} from "./videos/bridge/Bridge";\n{import_line}',
        )

    comp_block = (
        f'      <Composition\n'
        f'        id="{comp_id}"\n'
        f'        component={{{comp_name}}}\n'
        f'        durationInFrames={{{duration_in_frames}}}\n'
        f'        fps={{30}}\n'
        f'        width={{1080}}\n'
        f'        height={{1920}}\n'
        f'      />\n'
    )
    text = text.replace("    </>", f"{comp_block}    </>")
    root_path.write_text(text, encoding="utf-8")


def render_and_mux_video(story_id: str, audio_path: str | None = None) -> str:
    """Render the Remotion composition to MP4 and mux with voiceover audio via ffmpeg."""
    comp_id = story_id.replace("_", "-")
    out_dir = RENDERER_ROOT / "out" / story_id
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_mp4 = out_dir / "video.mp4"
    final_mp4 = out_dir / "final.mp4"

    subprocess.run(
        [
            "npx",
            "remotion",
            "render",
            "src/index.ts",
            comp_id,
            str(raw_mp4),
            "--codec",
            "h264",
            "--crf",
            "16",
            "--scale",
            "0.6666666666666666",
            "--concurrency",
            "1",
            "--timeout",
            "120000",
            "--frames",
            "0-90",
        ],
        cwd=str(RENDERER_ROOT),
        check=True,
    )

    if audio_path and Path(audio_path).exists():
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_mp4),
                "-i",
                str(audio_path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-shortest",
                str(final_mp4),
            ],
            check=True,
        )
        return str(final_mp4)

    return str(raw_mp4)


def validate_renderer_typescript() -> tuple[bool, list[str]]:
    """Run TypeScript typecheck in renderer/ if node_modules is installed."""
    if not (RENDERER_ROOT / "node_modules").exists():
        return True, ["Skipped tsc: renderer/node_modules not installed yet."]

    proc = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=str(RENDERER_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, []
    errors = [line for line in (proc.stdout + "\n" + proc.stderr).splitlines() if line.strip()]
    return False, errors


def video_generation_node(state: VideoGenState) -> dict[str, Any]:
    """LangGraph node: build manifest, generate TSX, and validate."""
    script = state["script"]
    story_id = state.get("story_id") or slugify_story_id(script.title)

    manifest = build_asset_manifest(
        story_id=story_id,
        selected_asset_ids=state.get("selected_assets", []),
        missing_assets=state.get("assets"),
        catalogue_records=ASSET_CATALOGUE,
    )
    write_asset_manifest(story_id, manifest)

    words_timings = "[]"
    words_path = state.get("words_json_path")
    if words_path and Path(words_path).exists():
        raw_words = json.loads(Path(words_path).read_text(encoding="utf-8"))
        words_timings = " ".join(f"{w['word']}@{w['start_frame']}" for w in raw_words)

    scene_plan: ScenePlan = scene_plan_chain.invoke(
        {
            "title": script.title,
            "script_text": script.script,
            "word_timings": words_timings,
            "shot_plan": state["shot_direction"].model_dump_json(),
            "asset_manifest": json.dumps(manifest, separators=(",", ":")),
        }
    )

    generated: GeneratedStoryFiles = tsx_chain.invoke(
        {
            "story_id": story_id,
            "title": script.title,
            "script_text": script.script,
            "word_timings": words_timings,
            "asset_manifest": json.dumps(manifest, separators=(",", ":")),
            "shot_plan": state["shot_direction"].model_dump_json(),
            "scene_plan": scene_plan.model_dump_json(),
        }
    )

    story_dir = write_story_files(story_id, generated)
    ok, errors = validate_renderer_typescript()

    # Self-heal up to 2 times if tsc reports errors in the generated .ts files
    for _ in range(2):
        if ok:
            break
        err_text = "\n".join(errors[:20])
        generated = tsx_chain.invoke(
            {
                "story_id": story_id,
                "title": f"{script.title}\n\nFIX THESE TYPESCRIPT ERRORS (NO JSX IN .ts FILES):\n{err_text}",
                "script_text": script.script,
                "word_timings": words_timings,
                "asset_manifest": json.dumps(manifest, separators=(",", ":")),
                "shot_plan": state["shot_direction"].model_dump_json(),
                "scene_plan": scene_plan.model_dump_json(),
            }
        )
        story_dir = write_story_files(story_id, generated)
        ok, errors = validate_renderer_typescript()

    return {
        "story_id": story_id,
        "story_dir": str(story_dir),
        "validation_ok": ok,
        "validation_errors": errors,
    }
