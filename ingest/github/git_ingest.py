#!/usr/bin/env python3

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Iterable

# -----------------------------
# Configuration
# -----------------------------

DEFAULT_EXTENSIONS = {
    ".py", ".go", ".js", ".ts",
    ".java", ".yaml", ".yml",
    ".json", ".md", ".txt"
}

MAX_CHARS = 1200
OVERLAP = 200


# -----------------------------
# Git Utilities
# -----------------------------

def clone_or_update_repo(repo_url: str, target_dir: Path):
    """
    Clone repo if not present.
    Otherwise pull latest changes.
    """
    if target_dir.exists():
        print(f"[INFO] Updating existing repo at {target_dir}")
        subprocess.run(["git", "-C", str(target_dir), "pull"], check=True)
    else:
        print(f"[INFO] Cloning repo into {target_dir}")
        subprocess.run(["git", "clone", repo_url, str(target_dir)], check=True)


# -----------------------------
# File Collection
# -----------------------------

def collect_files(repo_path: Path,
                  allowed_extensions: set = DEFAULT_EXTENSIONS) -> List[Path]:
    files = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() in allowed_extensions:
            files.append(path)

    return files


# -----------------------------
# Chunking
# -----------------------------

def chunk_text(text: str,
               max_chars: int = MAX_CHARS,
               overlap: int = OVERLAP) -> Iterable[str]:
    start = 0
    while start < len(text):
        end = start + max_chars
        yield text[start:end]
        start = end - overlap


# -----------------------------
# Parsing Code Files
# -----------------------------

def parse_file(file_path: Path,
               repo_name: str) -> List[Dict]:
    """
    Parse a file and return chunked documents.
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    chunks = []
    for idx, chunk in enumerate(chunk_text(text)):
        chunks.append({
            "id": f"{repo_name}:{file_path}:{idx}",
            "source": "code",
            "repo": repo_name,
            "file_path": str(file_path),
            "service": None,  # intentionally general
            "heading": file_path.name,
            "text": chunk
        })

    return chunks


# -----------------------------
# Commit Messages (Optional)
# -----------------------------

def extract_commit_messages(repo_path: Path,
                            repo_name: str,
                            limit: int = 200) -> List[Dict]:
    """
    Extract recent commit messages.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", f"-n{limit}", "--pretty=%H%n%B%n==END=="],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        return []

    raw = result.stdout.split("==END==")
    chunks = []

    for block in raw:
        lines = block.strip().splitlines()
        if not lines:
            continue

        commit_hash = lines[0]
        message = "\n".join(lines[1:]).strip()

        if not message:
            continue

        chunks.append({
            "id": f"{repo_name}:commit:{commit_hash}",
            "source": "commit",
            "repo": repo_name,
            "file_path": None,
            "service": None,
            "heading": f"Commit {commit_hash[:7]}",
            "text": message
        })

    return chunks


# -----------------------------
# Main Ingestion
# -----------------------------

def ingest_repo(repo_url: str,
                output_jsonl: Path,
                clone_dir: Path):
    """
    Clone repo, parse files, output JSONL chunks.
    """

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = clone_dir / repo_name

    clone_or_update_repo(repo_url, repo_path)

    print("[INFO] Collecting files...")
    files = collect_files(repo_path)

    print(f"[INFO] Parsing {len(files)} files...")
    all_chunks = []

    for file_path in files:
        chunks = parse_file(file_path, repo_name)
        all_chunks.extend(chunks)

    print("[INFO] Extracting commit messages...")
    commits = extract_commit_messages(repo_path, repo_name)
    all_chunks.extend(commits)

    print(f"[INFO] Writing {len(all_chunks)} chunks to {output_jsonl}")

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with output_jsonl.open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")


# -----------------------------
# CLI
# -----------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Git repository URL")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--clone-dir", default="data/repos", help="Local clone directory")

    args = parser.parse_args()

    ingest_repo(
        repo_url=args.repo,
        output_jsonl=Path(args.output),
        clone_dir=Path(args.clone_dir)
    )
