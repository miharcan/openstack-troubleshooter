#!/usr/bin/env python3

"""
Indexes GitHub issues/PRs into existing FAISS + metadata store.

Usage:
    python index_github.py \
        --input data/raw/github_nova.jsonl \
        --index data/processed/index/docs.faiss \
        --meta data/processed/index/docs_meta.json
"""

import argparse
import json
from pathlib import Path
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def load_jsonl(path: Path) -> List[dict]:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    return items


def chunk_text(text: str, max_chars: int = 2500) -> List[str]:
    """
    Issues are semantic units.
    Only chunk if extremely long.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end

    return chunks


# ------------------------------------------------------------
# Main indexing logic
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSONL from fetch_issues.py")
    parser.add_argument("--index", required=True, help="FAISS index path")
    parser.add_argument("--meta", required=True, help="Metadata JSON path")
    args = parser.parse_args()

    input_path = Path(args.input)
    index_path = Path(args.index)
    meta_path = Path(args.meta)

    print("[INFO] Loading GitHub issues...")
    issues = load_jsonl(input_path)

    print("[INFO] Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("[INFO] Loading existing FAISS index...")
    index = faiss.read_index(str(index_path))

    print("[INFO] Loading existing metadata...")
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    embeddings = []
    new_meta = []

    print("[INFO] Processing issues...")

    for issue in issues:
        chunks = chunk_text(issue["text"])

        for i, chunk in enumerate(chunks):
            chunk_id = f"{issue['id']}::chunk{i}"

            metadata_entry = {
                "id": chunk_id,
                "source": "github",
                "repo": issue.get("repo"),
                "service": infer_service(issue),
                "type": issue.get("type"),
                "labels": issue.get("labels"),
                "url": issue.get("url"),
                "text": chunk,
            }

            new_meta.append(metadata_entry)
            embeddings.append(chunk)

    print(f"[INFO] Creating embeddings for {len(embeddings)} chunks...")

    vectors = model.encode(
        embeddings,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype("float32")

    print("[INFO] Adding to FAISS index...")
    index.add(vectors)

    print("[INFO] Updating metadata...")
    meta.extend(new_meta)

    print("[INFO] Saving updated index and metadata...")
    faiss.write_index(index, str(index_path))

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("[SUCCESS] GitHub issues indexed successfully.")


# ------------------------------------------------------------
# Optional service inference (generic)
# ------------------------------------------------------------

def infer_service(issue: dict) -> str | None:
    """
    Generic heuristic:
    - Try repo name
    - Try labels
    """
    repo = issue.get("repo", "")
    if "/" in repo:
        return repo.split("/")[-1]

    labels = issue.get("labels", [])
    if labels:
        return labels[0]

    return None


if __name__ == "__main__":
    main()
