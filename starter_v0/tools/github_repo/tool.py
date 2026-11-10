from __future__ import annotations

import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err

GITHUB_REPO_URL = "https://api.github.com/repos/{owner}/{repo}"
_REPO_RE = re.compile(r"^(?:https?://github\.com/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


def _parse_repo(value: str) -> tuple[str, str]:
    match = _REPO_RE.match((value or "").strip())
    if not match:
        raise ValueError("repo must look like 'owner/name' or https://github.com/owner/name")
    return match.group(1), match.group(2)


def github_repo_info(repo: str = "") -> dict[str, Any]:
    try:
        owner, name = _parse_repo(repo)
        response = requests.get(
            GITHUB_REPO_URL.format(owner=owner, repo=name),
            headers={"Accept": "application/vnd.github+json", "User-Agent": "AI20k-Day03-Research-Agent/1.0"},
            timeout=TIMEOUT,
        )
        if response.status_code == 404:
            return {"tool": "github_repo", "repo": f"{owner}/{name}", "found": False,
                    "message": f"Repository {owner}/{name} not found."}
        if response.status_code in (403, 429):
            raise RuntimeError("GitHub API rate limit reached (60 requests/hour without a token). Try again later.")
        response.raise_for_status()
        data = response.json()
        return {
            "tool": "github_repo",
            "found": True,
            "repo": data.get("full_name", f"{owner}/{name}"),
            "description": data.get("description") or "",
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "language": data.get("language"),
            "license": (data.get("license") or {}).get("spdx_id"),
            "topics": data.get("topics", []),
            "archived": data.get("archived", False),
            "last_push": data.get("pushed_at"),
            "url": data.get("html_url", f"https://github.com/{owner}/{name}"),
            "source": "github.com",
        }
    except Exception as exc:
        return err("github_repo", exc)
