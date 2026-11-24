from kokoro_mlx import KokoroTTS
from pathlib import Path
import soundfile as sf

def generate_audio(text: str):
    output_path = Path("/Users/xon/company/Video_Agent/src/agents/audio_generation/output/output.wav")
    output_path.parent.mkdir(parents=True , exist_ok= True)

    print(text)

    with KokoroTTS.from_pretrained() as tts:
        tts.save(
            text,
            str(output_path),
            voice="af_heart",
            speed=1.0,
            sample_rate = 48000
        )
    info = sf.info(str(output_path))

    print("audio created suessfully!")

    return{
        "filename" : output_path.name,
        "filePath" : output_path,
        "audio_duration" : str(info.duration)
    }
