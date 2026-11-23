from kokoro_mlx import KokoroTTS

text = """
At four thousand meters beneath the Atlantic,
the pressure is so immense that every square inch
of a submersible's hull faces thousands of pounds of force.
"""

with KokoroTTS.from_pretrained() as tts:
    result = tts.save(
        text,
        "output.wav",
        voice="af_heart",
        speed=1.0,
        sample_rate=48000
    )

    print("Audio generated successfully!")
