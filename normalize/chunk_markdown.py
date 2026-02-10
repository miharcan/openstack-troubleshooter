#!/usr/bin/env python3

from pathlib import Path
import yaml
import json
import re
import uuid

RAW_ROOT = Path("data/raw/openstack_docs")
OUT_FILE = Path("data/processed/chunks.jsonl")

HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)")


def clean_chunk_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.strip().startswith(":::"):
            continue
        if line.strip().startswith("[!["):
            continue
        if "OpenStack Documentation" in line:
            continue
        if "this page last updated" in line.lower():
            continue
        if line.strip().startswith("Languages"):
            continue
        lines.append(line)

    return "\n".join(lines).strip()


def load_markdown(md_path: Path):
    text = md_path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        raise ValueError(f"No front-matter in {md_path}")

    _, fm, body = text.split("---", 2)
    metadata = yaml.safe_load(fm)
    return metadata, body.strip()


def chunk_body(body: str):
    chunks = []
    current = {
        "heading": "Introduction",
        "content": [],
    }

    for line in body.splitlines():
        m = HEADING_RE.match(line)
        if m:
            if current["content"]:
                chunks.append(current)

            current = {
                "heading": m.group(2).strip(),
                "content": [],
            }
        else:
            current["content"].append(line)

    if current["content"]:
        chunks.append(current)

    return chunks


def clean_heading(h: str) -> str:
    # Remove markdown links: Text(#anchor "title")
    h = re.sub(r"\(#[^)]+\)", "", h)

    # Remove anything in braces {...}
    h = re.sub(r"\{.*?\}", "", h)

    # Remove stray brackets [...]
    h = re.sub(r"\[.*?\]", "", h)

    # Remove encoding artifacts
    h = h.replace("Â¶", "")

    return h.strip()



def normalize():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with OUT_FILE.open("w", encoding="utf-8") as out:
        for md_file in RAW_ROOT.rglob("*.md"):
            metadata, body = load_markdown(md_file)
            chunks = chunk_body(body)

            for c in chunks:
                raw_text = "\n".join(c["content"]).strip()
                text = clean_chunk_text(raw_text)
                if len(text) < 200:
                    continue

                record = {
                    "id": str(uuid.uuid4()),
                    "source": metadata.get("source"),
                    "service": metadata.get("service"),
                    "version": metadata.get("version"),
                    "url": metadata.get("url"),
                    "doc_path": str(md_file.relative_to(RAW_ROOT)),
                    "heading": clean_heading(c["heading"]),
                    "text": text,
                }

                out.write(json.dumps(record) + "\n")
                count += 1

    print(f"✔ Wrote {count} chunks to {OUT_FILE}")


if __name__ == "__main__":
    normalize()
