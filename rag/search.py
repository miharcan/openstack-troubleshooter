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

# --- LOAD ONCE AT IMPORT ---
_index = faiss.read_index(str(INDEX_FILE))

with META_FILE.open() as f:
    _meta = json.load(f)

_model = SentenceTransformer(MODEL_NAME)


def search(query: str, service: str | None = None, k: int = 5):
    q_emb = _model.encode([query], normalize_embeddings=True).astype("float32")

    scores, ids = _index.search(q_emb, 20)  # fetch extra for filtering

    # index, meta, model = load()

    # q_emb = model.encode([query], normalize_embeddings=True).astype("float32")
    # scores, ids = index.search(q_emb, 20)  # fetch more to allow filtering

    candidates = []

    for i, similarity_score in zip(ids[0], scores[0]):
        if i == -1:
            continue

        chunk = _meta[i]
        score = float(similarity_score)

        # Penalize release notes
        if chunk.get("source") == "releasenotes":
            score *= 0.8

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
