#!/usr/bin/env python3

import faiss
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

INDEX_FILE = Path("data/processed/index/docs.faiss")
META_FILE = Path("data/processed/index/docs_meta.json")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load():
    index = faiss.read_index(str(INDEX_FILE))
    with META_FILE.open() as f:
        meta = json.load(f)
    model = SentenceTransformer(MODEL_NAME)
    return index, meta, model


def search(query: str, k: int = 5):
    index, meta, model = load()

    q_emb = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(q_emb, k)

    results = []
    for i, score in zip(ids[0], scores[0]):
        r = meta[i].copy()
        r["score"] = float(score)
        results.append(r)

    return results


if __name__ == "__main__":
    query = "Nova scheduler cannot find a valid host"
    results = search(query)

    for r in results:
        print("\n---")
        print(f"Score: {r['score']:.3f}")
        print(f"{r['service']} | {r['heading']}")
        print(r["text"][:400], "...")
