from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

WIKI_SUMMARY_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
SUPPORTED_LANGS = {"en", "vi"}
MAX_EXTRACT_CHARS = 1500


def wikipedia_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    try:
        title = " ".join(str(title or "").split())
        if not title:
            raise ValueError("title is required")
        lang = lang if lang in SUPPORTED_LANGS else "en"
        url = WIKI_SUMMARY_URL.format(lang=lang, title=quote(title.replace(" ", "_"), safe=""))
        response = requests.get(
            url,
            headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)", "Accept": "application/json"},
            params={"redirect": "true"},
            timeout=TIMEOUT,
        )
        if response.status_code == 404:
            return {"tool": "wikipedia", "title": title, "lang": lang, "found": False,
                    "message": f"No Wikipedia article found for '{title}'. Try a different spelling."}
        response.raise_for_status()
        data = response.json()
        extract = (data.get("extract") or "").strip()
        if len(extract) > MAX_EXTRACT_CHARS:
            extract = extract[: MAX_EXTRACT_CHARS - 3] + "..."
        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page", "")
        return {
            "tool": "wikipedia",
            "found": True,
            "lang": lang,
            "title": data.get("title", title),
            "description": data.get("description", ""),
            "summary": extract,
            "url": page_url,
            "source": f"{lang}.wikipedia.org",
            "is_disambiguation": data.get("type") == "disambiguation",
        }
    except Exception as exc:
        return err("wikipedia", exc)
