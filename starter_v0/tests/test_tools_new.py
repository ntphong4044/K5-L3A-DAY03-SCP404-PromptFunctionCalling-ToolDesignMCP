"""Unit tests for the team's new tools: wikipedia, hackernews, github_repo, datetime_now.

Offline: HTTP is mocked with `fake_http`; the clock is patched for datetime_now.
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.datetime_now import tool as dt_module

wikipedia = TOOL_FUNCTIONS["wikipedia"]
hackernews = TOOL_FUNCTIONS["hackernews"]
github_repo = TOOL_FUNCTIONS["github_repo"]
datetime_now = TOOL_FUNCTIONS["datetime_now"]


# ---------------------------------------------------------------- wikipedia

def test_wikipedia_happy_path_sends_title_and_maps_response(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Alan Turing", "description": "English mathematician", "extract": "Alan Turing was...",
        "type": "standard", "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Alan_Turing"}},
    }))
    result = wikipedia(title="Alan Turing", lang="en")

    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Alan_Turing"
    assert result["found"] is True
    assert result["summary"] == "Alan Turing was..."
    assert result["url"] == "https://en.wikipedia.org/wiki/Alan_Turing"
    assert result["source"] == "en.wikipedia.org"


def test_wikipedia_vietnamese_uses_vi_host_and_unknown_lang_falls_back(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "Hà Nội", "extract": "x"}))
    wikipedia(title="Hà Nội", lang="vi")
    wikipedia(title="Hanoi", lang="klingon")

    assert calls[0]["url"].startswith("https://vi.wikipedia.org/")
    assert "H%C3%A0_N%E1%BB%99i" in calls[0]["url"]
    assert calls[1]["url"].startswith("https://en.wikipedia.org/")


def test_wikipedia_empty_title_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = wikipedia(title="   ")

    assert result["error"] == "ValueError"
    assert calls == []


def test_wikipedia_missing_article_is_not_an_error(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = wikipedia(title="Zzzxqwv nonexistent")

    assert result["found"] is False
    assert "error" not in result


def test_wikipedia_truncates_long_extract(fake_http) -> None:
    fake_http(FakeResponse({"title": "T", "extract": "y" * 5000}))
    result = wikipedia(title="T")

    assert len(result["summary"]) == 1500
    assert result["summary"].endswith("...")


def test_wikipedia_network_failure_returns_error_dict(fake_http) -> None:
    fake_http(requests.ConnectionError("boom"))
    result = wikipedia(title="Python")

    assert result["error"] == "ConnectionError"


# --------------------------------------------------------------- hackernews

HITS = {"hits": [
    {"objectID": "1", "title": "Show HN: A", "url": "https://a.dev", "points": 120, "num_comments": 30, "author": "pg"},
    {"objectID": "2", "title": "Ask HN: B", "url": None, "points": 50, "num_comments": 7, "author": "dang"},
]}


def test_hackernews_top_uses_front_page_and_maps_items(fake_http) -> None:
    calls = fake_http(FakeResponse(HITS))
    result = hackernews(limit=2, kind="top")

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"tags": "front_page", "hitsPerPage": 2}
    assert result["items"][0]["title"] == "Show HN: A"
    assert result["items"][0]["summary"] == "120 points, 30 comments, by pg"
    assert result["items"][0]["source"] == "news.ycombinator.com"


def test_hackernews_story_without_url_falls_back_to_hn_item_page(fake_http) -> None:
    fake_http(FakeResponse(HITS))
    result = hackernews(limit=2)

    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=2"


def test_hackernews_new_uses_search_by_date(fake_http) -> None:
    calls = fake_http(FakeResponse(HITS))
    hackernews(limit=2, kind="new")

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"]["tags"] == "story"


def test_hackernews_bad_limit_values_are_clamped_not_crashing(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hackernews(limit=0)
    hackernews(limit=999)
    hackernews(limit="3")
    hackernews(limit="abc")
    hackernews(limit=None)

    assert [c["params"]["hitsPerPage"] for c in calls] == [1, 10, 3, 5, 5]


def test_hackernews_unknown_kind_defaults_to_top(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    result = hackernews(kind="best")

    assert result["kind"] == "top"
    assert calls[0]["params"]["tags"] == "front_page"


def test_hackernews_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    result = hackernews()

    assert result["error"] == "HTTPError"


# -------------------------------------------------------------- github_repo

REPO_JSON = {
    "full_name": "psf/requests", "description": "HTTP for Humans", "stargazers_count": 50000,
    "forks_count": 9000, "open_issues_count": 120, "language": "Python", "license": {"spdx_id": "Apache-2.0"},
    "topics": ["http"], "archived": False, "pushed_at": "2026-01-01T00:00:00Z",
    "html_url": "https://github.com/psf/requests",
}


def test_github_repo_happy_path_maps_fields(fake_http) -> None:
    calls = fake_http(FakeResponse(REPO_JSON))
    result = github_repo(repo="psf/requests")

    assert calls[0]["url"] == "https://api.github.com/repos/psf/requests"
    assert result["found"] is True
    assert result["stars"] == 50000
    assert result["license"] == "Apache-2.0"
    assert result["language"] == "Python"


def test_github_repo_accepts_full_url_and_dot_git_suffix(fake_http) -> None:
    calls = fake_http(FakeResponse(REPO_JSON))
    github_repo(repo="https://github.com/psf/requests/")
    github_repo(repo="https://github.com/psf/requests.git")

    assert calls[0]["url"] == calls[1]["url"] == "https://api.github.com/repos/psf/requests"


def test_github_repo_invalid_input_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse(REPO_JSON))
    for bad in ["", "just-a-name", "a/b/c", "../../etc/passwd", None]:
        result = github_repo(repo=bad)
        assert result["error"] == "ValueError", bad

    assert calls == []


def test_github_repo_not_found_is_not_an_error(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = github_repo(repo="nobody/nothing")

    assert result["found"] is False
    assert "error" not in result


def test_github_repo_rate_limit_returns_readable_error(fake_http) -> None:
    fake_http(FakeResponse(status_code=403))
    result = github_repo(repo="psf/requests")

    assert result["error"] == "RuntimeError"
    assert "rate limit" in result["message"]


def test_github_repo_null_description_and_license_do_not_crash(fake_http) -> None:
    fake_http(FakeResponse({"full_name": "a/b", "description": None, "license": None}))
    result = github_repo(repo="a/b")

    assert result["description"] == ""
    assert result["license"] is None


# ------------------------------------------------------------ datetime_now

FIXED_NOW = datetime(2026, 11, 10, 3, 30, 0, tzinfo=timezone.utc)  # a Tuesday


def _freeze(monkeypatch) -> None:
    monkeypatch.setattr(dt_module, "_utcnow", lambda: FIXED_NOW)


def test_datetime_now_defaults_to_utc(monkeypatch) -> None:
    _freeze(monkeypatch)
    result = datetime_now()

    assert result["iso"] == "2026-11-10T03:30:00+00:00"
    assert result["weekday"] == "Tuesday"
    assert result["timezone"] == "UTC"


def test_datetime_now_named_zone_applies_offset_and_crosses_date(monkeypatch) -> None:
    _freeze(monkeypatch)
    result = datetime_now(timezone_name="Asia/Ho_Chi_Minh")

    assert result["time"] == "10:30:00"
    assert result["utc_offset"] == "+0700"
    assert result["date"] == "2026-11-10"
    assert datetime_now(timezone_name="America/Los_Angeles")["date"] == "2026-11-09"


def test_datetime_now_utc_offset_formats(monkeypatch) -> None:
    _freeze(monkeypatch)

    assert datetime_now(timezone_name="UTC+7")["time"] == "10:30:00"
    assert datetime_now(timezone_name="utc-5")["time"] == "22:30:00"
    assert datetime_now(timezone_name="UTC+5:30")["time"] == "09:00:00"


def test_datetime_now_unknown_or_out_of_range_zone_returns_error(monkeypatch) -> None:
    _freeze(monkeypatch)

    assert datetime_now(timezone_name="Mars/Olympus")["error"] == "ValueError"
    assert datetime_now(timezone_name="UTC+99")["error"] == "ValueError"


def test_datetime_now_empty_zone_falls_back_to_utc(monkeypatch) -> None:
    _freeze(monkeypatch)

    assert datetime_now(timezone_name="")["timezone"] == "UTC"
    assert datetime_now(timezone_name=None)["timezone"] == "UTC"


def test_datetime_now_makes_no_network_call(monkeypatch, fake_http) -> None:
    _freeze(monkeypatch)
    calls = fake_http(FakeResponse({}))
    datetime_now(timezone_name="Asia/Tokyo")

    assert calls == []
