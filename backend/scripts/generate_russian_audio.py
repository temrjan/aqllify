"""Generate reusable course MP3s; never called by the application at runtime.

Run from the repository root: .venv/bin/python backend/scripts/generate_russian_audio.py
Requires network access for gTTS. Only public curriculum text is submitted.
"""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from gtts import gTTS

COURSE = Path(__file__).resolve().parents[2] / "courses" / "russian"


def generate(item: tuple[str, str]) -> None:
    name, text = item
    expected = hashlib.sha256(text.encode()).hexdigest()[:16] + ".mp3"
    if name != expected:
        raise ValueError("Audio filename must identify its exact text")
    target = COURSE / "audio" / name
    if target.is_file() and target.stat().st_size > 0:
        return
    temporary = target.with_suffix(".part")
    gTTS(text, lang="ru", timeout=20).save(str(temporary))
    temporary.replace(target)


def main() -> None:
    content = json.loads((COURSE / "course.json").read_text())
    items = {
        p["audio"]: p["russian"]
        for lesson in content["lessons"]
        for p in lesson["phrases"]
    }
    items.update(
        {q["audio"]: q["transcript"] for q in content["placement"] if q.get("audio")}
    )
    (COURSE / "audio").mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(generate, items.items()))


if __name__ == "__main__":
    main()
