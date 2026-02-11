#!/usr/bin/env python3

import json
from pathlib import Path

RAW_DIR = Path("data/raw/releasenotes")
OUT_FILE = Path("data/processed/chunks/releasenotes_chunks.json")

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def chunk_text(text: str, chunk_size: int = 500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def main():
    all_chunks = []

    for file in RAW_DIR.glob("*.json"):
        data = json.loads(file.read_text())
        project = data["project"]

        for note in data["notes"]:
            chunks = chunk_text(note["text"])

            for c in chunks:
                all_chunks.append({
                    "source": "releasenotes",
                    "project": project,
                    "text": c.strip()
                })

    OUT_FILE.write_text(json.dumps(all_chunks, indent=2))
    print(f"Saved {len(all_chunks)} chunks → {OUT_FILE}")


if __name__ == "__main__":
    main()
