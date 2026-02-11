#!/usr/bin/env python3

import json
from pathlib import Path

SRC = Path("data/processed/chunks.jsonl")
OUT = Path("data/processed/chunks/docs_chunks.json")


def main():
    chunks = []
    with SRC.open() as f:
        for line in f:
            data = json.loads(line)
            data["source"] = "docs"
            chunks.append(data)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(chunks, indent=2))

    print(f"Saved {len(chunks)} docs chunks → {OUT}")


if __name__ == "__main__":
    main()
