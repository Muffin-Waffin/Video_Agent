from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel

_MODEL: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return _MODEL


def extract_word_timings(
    audio_path: str | Path,
    output_json_path: str | Path | None = None,
    fps: int = 30,
) -> tuple[list[dict[str, Any]], Path]:
    """Transcribe audio_path with faster-whisper and write word-level timings to words.json."""
    audio_file = Path(audio_path)
    out_path = Path(output_json_path) if output_json_path else audio_file.with_name("words.json")

    model = _get_model()
    segments, _ = model.transcribe(str(audio_file), word_timestamps=True)

    words: list[dict[str, Any]] = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            start = round(float(w.start), 3)
            end = round(float(w.end), 3)
            words.append(
                {
                    "word": w.word.strip(),
                    "start": start,
                    "end": end,
                    "start_frame": int(round(start * fps)),
                    "end_frame": int(round(end * fps)),
                }
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(words, indent=2), encoding="utf-8")
    return words, out_path
