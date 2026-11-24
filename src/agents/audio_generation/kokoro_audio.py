from pathlib import Path
from kokoro import KPipeline
import soundfile as sf
import numpy as np

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 24000

pipeline = KPipeline(lang_code="a")


def generate_audio(text: str):
    output_path = OUTPUT_DIR / "output.wav"

    audio_chunks = []

    generator = pipeline(
        text,
        voice="af_heart",
        speed=1.0
    )

    for gs, ps, audio in generator:
        audio_chunks.append(audio.cpu().numpy())

    if not audio_chunks:
        raise ValueError("Kokoro generated no audio.")

    final_audio = np.concatenate(audio_chunks)

    sf.write(
        str(output_path),
        final_audio,
        SAMPLE_RATE
    )

    info = sf.info(str(output_path))

    print("Audio created successfully!")

    return {
        "filename": output_path.name,
        "filePath": str(output_path),
        "audio_duration": float(info.duration),
        "sample_rate": info.samplerate
    }


if __name__ == "__main__":
    result = generate_audio("Hello! Welcome to the world of animated shorts.")
    print(result)
