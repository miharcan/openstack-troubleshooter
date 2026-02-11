#!/usr/bin/env python3

import requests
import json
from pathlib import Path
from datetime import datetime, UTC
import os
import time

BASE_URL = "https://api.github.com/repos"
OUT_DIR = Path("data/raw/github")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECTS = [
    "openstack/nova",
    "openstack/neutron",
    "openstack/placement",
]

# Optional: set GITHUB_TOKEN to increase rate limit
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def fetch_repo_issues(repo: str, limit: int = 100):
    print(f"Fetching GitHub issues for {repo}")

    issues = []
    page = 1
    per_page = 30

    while len(issues) < limit:
        url = f"{BASE_URL}/{repo}/issues"

        params = {
            "state": "all",
            "per_page": per_page,
            "page": page,
        }

        resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
        resp.raise_for_status()

        data = resp.json()
        if not data:
            break

        for item in data:
            # Skip pull requests (GitHub mixes them in)
            if "pull_request" in item:
                continue

            issues.append({
                "id": item["id"],
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "labels": [l["name"] for l in item.get("labels", [])],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "url": item["html_url"],
                "body": item.get("body", ""),
            })

            if len(issues) >= limit:
                break

        page += 1
        time.sleep(0.5)  # gentle on rate limits

    return issues


def main():
    for repo in PROJECTS:
        issues = fetch_repo_issues(repo)

        safe_name = repo.replace("/", "_")
        out_file = OUT_DIR / f"{safe_name}.json"

        payload = {
            "repository": repo,
            "fetched_at": datetime.now(UTC).isoformat(),
            "count": len(issues),
            "issues": issues,
        }

        out_file.write_text(json.dumps(payload, indent=2))
        print(f"Saved {len(issues)} issues → {out_file}")


if __name__ == "__main__":
    main()
