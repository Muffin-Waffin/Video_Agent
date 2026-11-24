from pathlib import Path

GUIDELINES_DIR = Path("src/video_stuff/guidelines")

def load_visual_guidelines():
    files = [
        "STYLE_BIBLE.md",
        "reports/characters.md",
        "reports/depth.md",
        "reports/lighting.md",
        "reports/motion.md",
        "reports/outlines.md",
        "reports/textures.md",
        "reports/grade.md",
    ]

    return "\n\n".join(
        (GUIDELINES_DIR / file).read_text()
        for file in files
    )
