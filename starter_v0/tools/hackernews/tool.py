from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"


def hackernews_top(limit: int = 5, kind: str = "top") -> dict[str, Any]:
    try:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, 10))
        kind = kind if kind in {"top", "new"} else "top"
        url = HN_SEARCH_URL if kind == "top" else HN_SEARCH_BY_DATE_URL
        tags = "front_page" if kind == "top" else "story"
        response = requests.get(url, params={"tags": tags, "hitsPerPage": limit}, timeout=TIMEOUT)
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", [])[:limit]:
            object_id = hit.get("objectID", "")
            items.append({
                "title": hit.get("title") or "",
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
                "hn_url": f"https://news.ycombinator.com/item?id={object_id}",
                "source": "news.ycombinator.com",
                "summary": f"{hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments, by {hit.get('author', '')}",
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
            })
        return {"tool": "hackernews", "kind": kind, "items": items}
    except Exception as exc:
        return err("hackernews", exc)
