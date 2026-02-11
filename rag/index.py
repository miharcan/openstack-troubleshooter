import json
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

CHUNKS_DIR = Path("data/processed/chunks")
INDEX_DIR = Path("data/processed/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_FILES = [
    "data/processed/chunks/docs_chunks.json",
    "data/processed/chunks/releasenotes_chunks.json",
    "data/processed/chunks/admin_chunks.json",
]

INDEX_FILE = INDEX_DIR / "docs.faiss"
META_FILE = INDEX_DIR / "docs_meta.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_chunks():
    chunks = []
    for f in CHUNKS_DIR.glob("*.json"):
        print(f"Loading {f}")
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
            chunks.extend(data)
    return chunks


def main():
    print("Loading chunks")
    chunks = load_chunks()
    texts = [c["text"] for c in chunks]

    print(f"Loaded {len(texts)} chunks")

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    embeddings = np.array(embeddings).astype("float32")

    dim = embeddings.shape[1]
    print(f"Embedding dimension: {dim}")

    print("Building FAISS index")
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    print(f"Index contains {index.ntotal} vectors")

    print(f"Saving index to {INDEX_FILE}")
    faiss.write_index(index, str(INDEX_FILE))

    print(f"Saving metadata to {META_FILE}")
    with META_FILE.open("w") as f:
        json.dump(chunks, f, indent=2)

    print("✔ Embedding + indexing complete")


if __name__ == "__main__":
    main()
