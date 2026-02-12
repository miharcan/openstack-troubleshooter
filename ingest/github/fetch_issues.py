#!/usr/bin/env python3

"""
Production-grade GitHub Issues + PR fetcher.

Features:
- Authenticated GitHub API access
- Pagination support
- Rate limit handling
- Comment aggregation
- Issue vs PR detection
- Normalized JSONL output
- Framework-agnostic metadata

Usage:
    python fetch_issues.py --repo openstack/nova --output data/raw/github_nova.jsonl
"""

import os
import time
import argparse
import requests
from typing import Dict, List, Optional


GITHUB_API = "https://api.github.com"
PER_PAGE = 100


class GitHubFetcher:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required.")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

    # --------------------------------------------------------
    # Core request wrapper with rate limit handling
    # --------------------------------------------------------

    def _get(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        while True:
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 403:
                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                if remaining == 0:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
                    sleep_seconds = max(reset_time - int(time.time()), 5)
                    print(f"[Rate Limit] Sleeping {sleep_seconds} seconds...")
                    time.sleep(sleep_seconds)
                    continue

            response.raise_for_status()
            return response

    # --------------------------------------------------------
    # Fetch issues + PRs
    # --------------------------------------------------------

    def fetch_issues(self, repo: str, state: str = "all") -> List[Dict]:
        owner, name = repo.split("/")
        url = f"{GITHUB_API}/repos/{owner}/{name}/issues"

        page = 1
        all_items = []

        while True:
            params = {
                "state": state,
                "per_page": PER_PAGE,
                "page": page,
            }

            response = self._get(url, params=params)
            data = response.json()

            if not data:
                break

            all_items.extend(data)
            print(f"[INFO] Retrieved page {page} ({len(data)} items)")
            page += 1

        return all_items

    # --------------------------------------------------------
    # Fetch comments for a specific issue
    # --------------------------------------------------------

    def fetch_comments(self, repo: str, issue_number: int) -> List[str]:
        owner, name = repo.split("/")
        url = f"{GITHUB_API}/repos/{owner}/{name}/issues/{issue_number}/comments"

        comments = []
        page = 1

        while True:
            params = {"per_page": PER_PAGE, "page": page}
            response = self._get(url, params=params)
            data = response.json()

            if not data:
                break

            comments.extend([c["body"] for c in data if c.get("body")])
            page += 1

        return comments


# ------------------------------------------------------------
# Normalization
# ------------------------------------------------------------

def normalize_issue(repo: str, issue: Dict, comments: List[str]) -> Dict:
    issue_type = "pull_request" if "pull_request" in issue else "issue"

    text_parts = [
        issue.get("title", ""),
        issue.get("body", "") or "",
    ]

    if comments:
        text_parts.append("\n--- Comments ---\n")
        text_parts.extend(comments)

    combined_text = "\n".join(text_parts).strip()

    return {
        "id": f"github:{repo}:{issue_type}:{issue['number']}",
        "source": "github",
        "repo": repo,
        "type": issue_type,
        "number": issue["number"],
        "state": issue.get("state"),
        "labels": [label["name"] for label in issue.get("labels", [])],
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "url": issue.get("html_url"),
        "text": combined_text,
    }


# ------------------------------------------------------------
# CLI Entrypoint
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--state", default="all", help="Issue state (all/open/closed)")
    args = parser.parse_args()

    fetcher = GitHubFetcher()

    print(f"[INFO] Fetching issues for {args.repo}")
    raw_items = fetcher.fetch_issues(args.repo, state=args.state)

    print(f"[INFO] Total issues/PRs: {len(raw_items)}")

    with open(args.output, "w", encoding="utf-8") as f:
        for issue in raw_items:
            number = issue["number"]
            comments = fetcher.fetch_comments(args.repo, number)

            normalized = normalize_issue(args.repo, issue, comments)

            f.write(json_dumps_safe(normalized) + "\n")

    print(f"[INFO] Saved to {args.output}")


# ------------------------------------------------------------
# Safe JSON writer (avoids Unicode issues)
# ------------------------------------------------------------

import json

def json_dumps_safe(obj):
    return json.dumps(obj, ensure_ascii=False)


if __name__ == "__main__":
    main()
