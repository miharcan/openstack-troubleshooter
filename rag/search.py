#!/usr/bin/env python3

import faiss
import json
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


_index = faiss.read_index(str(INDEX_FILE))

with META_FILE.open() as f:
    _meta = json.load(f)

_model = SentenceTransformer(MODEL_NAME)


def search(query: str, service: str | None = None, k: int = 5):
    q_emb = _model.encode([query], normalize_embeddings=True).astype("float32")

    scores, ids = _index.search(q_emb, 50)  # fetch extra for filtering
    candidates = []

    for i, similarity_score in zip(ids[0], scores[0]):
        if i == -1:
            continue

        chunk = _meta[i]
        score = float(similarity_score)

        # Penalize release notes
        if chunk.get("source") == "releasenotes":
            score *= 0.5

        # Boost matching service if explicit
        if service and chunk.get("service") == service:
            score *= 1.1

        heading = (chunk.get("heading") or "").lower()
        if any(word in heading for word in query.lower().split()):
            score *= 1.15

        if "security" in query.lower() and chunk.get("service") == "neutron":
            score *= 1.2

        if service and chunk.get("service") != service:
            continue

        r = chunk.copy()
        r["score"] = score
        candidates.append(r)

    # Now sort AFTER boosting
    candidates.sort(key=lambda x: x["score"], reverse=True)

    return candidates[:k]


if __name__ == "__main__":
    query = "Nova scheduler cannot find a valid host"
    results = search(query, service="nova")

    for r in results:
        print("\n---")
        print(f"Score: {r['score']:.3f}")
        print(f"{r.get('service')} | {r.get('heading')}")
        print(r["text"][:400], "...")
