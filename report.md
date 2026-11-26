# Video_Agent — Progress Report & Roadmap

## 1. Changes Made

1. **Ported `BridgeShort` Rendering Engine (`renderer/src/videos/bridge/`)**
   - Copied `claude-animated-shorts/templates/bridge/` into `renderer/src/videos/bridge/` (`Bridge.tsx`, `ink.ts`, `lensblur.ts`, `grade.ts`, `lights.ts`, `shade.ts`, `paint.ts`, `toon.ts`, `cast.ts`, `cardshade.ts`, `world.ts`, `build.ts`, `story.ts`).
   - Installed `@react-three/postprocessing@^2.16.0` and `postprocessing@^6.35.0` in `renderer/package.json`.
   - Fixed `EffectComposer` child typing in `renderer/src/videos/bridge/Bridge.tsx` and registered `BridgeShort` in `renderer/src/Root.tsx`.
   - Verified `npx tsc --noEmit` in `renderer/` passes with 0 errors.

2. **Added Word-Level Timings (`words.json`)**
   - Created `src/agents/audio_generation/word_timings.py` using `faster-whisper` (`word_timestamps=True`) to generate `words.json` (`word`, `start`, `end`, `start_frame`, `end_frame` at 30 fps).
   - Wired `extract_word_timings()` into `src/agents/audio_generation/audio.py` and added `words_json_path` to `StatusState` in `src/agents/orchestrator.py`.

3. **Updated Video Generation to Target `BridgeShort` (`src/agents/video_generation/video_generator.py`)**
   - Refactored `video_generation_node` to copy the fixed `renderer/src/videos/bridge/` engine into `renderer/src/videos/<story_id>/` and generate only the three story-specific files (`story.ts`, `build.ts`, `cast.ts`) timed to `words.json`.

---

## 2. What Is Currently Happening & How It Works

The LangGraph pipeline in `src/agents/orchestrator.py` runs sequentially with SQLite checkpointing (`video_pipeline.db`) and human-in-the-loop (HITL) interrupts:

1. **`idea_generation`** → Generates and scores video ideas; pauses for user approval.
2. **`script_generation`** → Generates the story script; pauses for user approval.
3. **`audio_generation`** → Synthesizes `output.wav` via Kokoro TTS (`kokoro_audio.py`), then runs `faster-whisper` (`word_timings.py`) to produce `words.json`.
4. **`get_asset_requirement`** → Identifies required assets.
5. **`get_shot`** → Generates shot-by-shot direction (`ShotBatch`).
6. **`video_generation`** → Copies the `BridgeShort` 2D-in-3D Three.js/Remotion engine to `renderer/src/videos/<story_id>/`, injects `words.json` + `shot_direction` into the LLM, writes `story.ts`, `build.ts`, and `cast.ts`, and validates with `npx tsc --noEmit`.

---

## 3. What Is Remaining & How to Do It

| Remaining Step | What It Does | How to Implement |
| :--- | :--- | :--- |
| **8. Sound Design & Mixing** | Procedural SFX + score ducked under voice (`mix.wav`). | Add a `sound_design` node in `orchestrator.py` after `video_generation` that maps `SHOTS`, `KICKS`, and `words.json` to `claude-animated-shorts/templates/audio/` (`timeline.py`, `sfx_gen.py`, `music.py`, `mix.py`) to output `mix.wav` (`music +3 dB`, `SFX -6 dB`, `voice` unchanged). |
| **9. Look Checks (Stills)** | Render key frames & compare against reference. | Run `claude-animated-shorts/templates/scripts/bridge-stills.mjs` and `sbs_sheet.py` for automated visual verification. |
| **10. Final Render & Audio Mux** | Render 2K vertical MP4 (1440×2560) and mux `mix.wav`. | Add a `render_and_mux` node in `orchestrator.py` running `npx remotion render src/index.ts <Comp> out/<story_id>/video.mp4 --codec h264 --crf 16 --scale 1.3333` followed by `ffmpeg -i video.mp4 -i mix.wav -map 0:v:0 -map 1:a:0 -c:v copy final.mp4`. |
| **11. Automated QA** | Catch black/white/frozen/pop frames & loudness issues. | Run `claude-animated-shorts/templates/scripts/short_qa.py final.mp4 out/<story_id>/qa shots.json` and loop back to fix any flagged frames before final delivery. |
