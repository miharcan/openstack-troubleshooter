#!/usr/bin/env python3

import subprocess
import yaml
import json
from pathlib import Path
from datetime import datetime, UTC

OUT_DIR = Path("data/raw/releasenotes")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECTS = ["nova", "neutron", "placement"]

BASE_GIT = "https://opendev.org/openstack"


def clone_or_update(repo_url: str, local_path: Path):
    if local_path.exists():
        subprocess.run(["git", "-C", str(local_path), "pull"], check=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, str(local_path)], check=True)


def extract_notes(repo_path: Path, project: str):
    notes_dir = repo_path / "releasenotes" / "notes"
    if not notes_dir.exists():
        return []

    entries = []

    for file in notes_dir.glob("*.yaml"):
        try:
            data = yaml.safe_load(file.read_text())
            if not isinstance(data, dict):
                continue

            text_blocks = []

            for key, value in data.items():
                if isinstance(value, list):
                    text_blocks.extend(str(v) for v in value)
                elif isinstance(value, str):
                    text_blocks.append(value)

            if not text_blocks:
                continue

            entries.append({
                "project": project,
                "file": file.name,
                "text": "\n".join(text_blocks),
            })

        except Exception:
            continue

    return entries


def main():
    for project in PROJECTS:
        print(f"Fetching release notes for {project}")

        repo_url = f"{BASE_GIT}/{project}"
        local_path = Path("data/tmp") / project

        clone_or_update(repo_url, local_path)

        notes = extract_notes(local_path, project)

        payload = {
            "project": project,
            "fetched_at": datetime.now(UTC).isoformat(),
            "count": len(notes),
            "notes": notes,
        }

        out_file = OUT_DIR / f"{project}.json"
        out_file.write_text(json.dumps(payload, indent=2))

        print(f"Saved {len(notes)} notes → {out_file}")


if __name__ == "__main__":
    main()
