#!/usr/bin/env python3

import subprocess
import shutil
from pathlib import Path
import json
from datetime import datetime, UTC

REPO = "https://github.com/openstack/nova.git"
TMP_DIR = Path("data/tmp/nova_docs")
OUT_DIR = Path("data/raw/admin_docs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_PATH = "doc/source/admin"


def clone_repo():
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)

    subprocess.run(
        ["git", "clone", "--depth", "1", REPO, str(TMP_DIR)],
        check=True,
    )


def collect_rst_files():
    base = TMP_DIR / ADMIN_PATH
    docs = []

    for rst in base.rglob("*.rst"):
        try:
            text = rst.read_text(encoding="utf-8")
        except Exception:
            continue

        docs.append({
            "service": "nova",
            "source": "admin_docs",
            "path": str(rst.relative_to(TMP_DIR)),
            "text": text
        })

    return docs


def main():
    print("Cloning nova documentation repo")
    clone_repo()

    print("Collecting admin .rst files")
    docs = collect_rst_files()

    payload = {
        "service": "nova",
        "fetched_at": datetime.now(UTC).isoformat(),
        "count": len(docs),
        "docs": docs
    }

    out_file = OUT_DIR / "nova_admin_docs.json"
    out_file.write_text(json.dumps(payload, indent=2))

    print(f"Saved {len(docs)} admin docs → {out_file}")


if __name__ == "__main__":
    main()
