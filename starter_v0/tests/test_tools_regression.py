"""Regression tests for bugs found by probing boundary inputs (Challenge+, REPORT B5).

Every test here FAILED against the starter code and passes after the fix.
Bug ids (B1..B6) match the table in artifacts/REPORT.md section B5.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
format_tool = TOOL_FUNCTIONS["format"]


def _tweets(n: int = 8) -> dict:
    return {"timeline": [{"tweet_id": str(i), "screen_name": "a", "text": f"t{i}"} for i in range(n)]}


@pytest.fixture
def keys(monkeypatch) -> None:
    for name in ("RAPIDAPI_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY"):
        monkeypatch.setenv(name, "test-key")


# B1: a negative limit used as a slice index silently dropped items from the END ------------

@pytest.mark.parametrize("func,kwargs", [(timeline, {"screenname": "a"}), (social_search, {"query": "q"})])
def test_b1_negative_limit_falls_back_to_default_instead_of_slicing_from_end(keys, fake_http, func, kwargs) -> None:
    fake_http(FakeResponse(_tweets(8)))
    result = func(limit=-1, **kwargs)

    assert len(result["items"]) == 5  # default, not 7 (= 8 items minus the last one)


@pytest.mark.parametrize("func,kwargs", [(timeline, {"screenname": "a"}), (social_search, {"query": "q"})])
def test_b1_limit_is_capped(keys, fake_http, func, kwargs) -> None:
    fake_http(FakeResponse(_tweets(40)))

    assert len(func(limit=999, **kwargs)["items"]) == 20


# B2: invalid limit still spent a paid RapidAPI request before failing ------------------------

@pytest.mark.parametrize("func,kwargs", [(timeline, {"screenname": "a"}), (social_search, {"query": "q"})])
def test_b2_non_numeric_limit_uses_default_and_does_not_error(keys, fake_http, func, kwargs) -> None:
    fake_http(FakeResponse(_tweets(8)))
    result = func(limit="abc", **kwargs)

    assert "error" not in result
    assert len(result["items"]) == 5


@pytest.mark.parametrize("func,kwargs", [(timeline, {"screenname": "a"}), (social_search, {"query": "q"})])
def test_b2_numeric_string_limit_is_accepted(keys, fake_http, func, kwargs) -> None:
    fake_http(FakeResponse(_tweets(8)))

    assert len(func(limit="3", **kwargs)["items"]) == 3


# B3: lookup sent max_results <= 0 or > 20 straight to Tavily -------------------------------

@pytest.mark.parametrize("given,expected", [(0, 5), (-1, 5), ("5", 5), ("abc", 5), (None, 5), (999, 20), (3, 3)])
def test_b3_lookup_max_results_is_normalised_before_request(keys, fake_http, given, expected) -> None:
    calls = fake_http(FakeResponse({"results": []}))
    lookup(query="AI", max_results=given)

    assert calls[0]["json"]["max_results"] == expected


# B4: empty required args still triggered a paid API call ------------------------------------

@pytest.mark.parametrize("func,kwargs", [
    (lookup, {"query": ""}), (lookup, {"query": "   "}),
    (timeline, {"screenname": ""}), (timeline, {"screenname": "@"}),
    (social_search, {"query": ""}),
    (fetch, {"url": ""}),
])
def test_b4_empty_required_arg_returns_error_without_http_call(keys, fake_http, func, kwargs) -> None:
    calls = fake_http(FakeResponse({}))
    result = func(**kwargs)

    assert result["error"] == "ValueError"
    assert calls == []


@pytest.mark.parametrize("url", ["not a url", "ftp://example.com/file", "javascript:alert(1)"])
def test_b4_fetch_rejects_non_http_urls_without_http_call(keys, fake_http, url) -> None:
    calls = fake_http(FakeResponse({}))
    result = fetch(url=url)

    assert result["error"] == "ValueError"
    assert calls == []


# B5: handle/search_type conventions the model breaks -------------------------------------------

def test_b5_timeline_strips_leading_at_from_handle(keys, fake_http) -> None:
    calls = fake_http(FakeResponse(_tweets(2)))
    timeline(screenname="@sama")

    assert calls[0]["params"] == {"screenname": "sama"}


@pytest.mark.parametrize("given,expected", [("top", "Top"), ("TOP", "Top"), ("latest", "Latest"), ("Hot", "Latest"), ("", "Latest")])
def test_b5_social_search_normalises_search_type(keys, fake_http, given, expected) -> None:
    calls = fake_http(FakeResponse(_tweets(2)))
    social_search(query="GPT-5", search_type=given)

    assert calls[0]["params"]["search_type"] == expected


# B6: format raised AttributeError on malformed items (tools must return, not raise) ----------

@pytest.mark.parametrize("bad_item", [None, "just a string", 42])
def test_b6_format_skips_non_dict_items_instead_of_raising(bad_item) -> None:
    result = format_tool(items=[{"summary": "good"}, bad_item], template="bullets")

    assert "good" in result["markdown"]
    assert result["item_count"] == 1


def test_b6_format_coerces_non_string_summary() -> None:
    result = format_tool(items=[{"summary": 123, "url": "https://example.com/a"}], template="bullets")

    assert "123" in result["markdown"]


def test_b6_format_item_without_url_has_no_dangling_separator() -> None:
    result = format_tool(items=[{"summary": "only text"}], template="bullets")

    assert result["markdown"] == "- only text"


def test_b6_format_none_section_uses_default_heading() -> None:
    result = format_tool(items=[{"summary": "s", "section": None}], template="sections")

    assert "## None" not in result["markdown"]
    assert "## Tổng hợp" in result["markdown"]
