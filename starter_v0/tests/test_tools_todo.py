"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    clarify = TOOL_FUNCTIONS["clarify"]
    options = ["Sam Altman", "Elon Musk"]
    result = clarify(question="Bạn muốn xem tài khoản nào?", response_type="choice", options=options)

    assert result["options"] == ["Sam Altman", "Elon Musk"]
    assert result["response_type"] == "choice"
    assert result["question"] == "Bạn muốn xem tài khoản nào?"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    result = TOOL_FUNCTIONS["format"](items=items, template="sections")
    md = result["markdown"]

    assert md.count("## A") == 1
    assert md.count("## B") == 1
    # both A items are listed under the single "## A" heading, before "## B"
    assert md.index("## A") < md.index("a1") < md.index("a2") < md.index("## B")
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    items = [{"title": f"Tweet {i}", "url": f"https://x.com/a/status/{i}"} for i in range(3)]
    result = TOOL_FUNCTIONS["format"](items=items, template="thread")
    lines = [line for line in result["markdown"].splitlines() if line.strip()]

    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]
    assert "Tweet 0" in lines[0] and "Tweet 2" in lines[2]


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    format_tool = TOOL_FUNCTIONS["format"]
    for empty in (None, []):
        for template in ("brief", "sections", "bullets", "thread", "daily_ai_vn"):
            result = format_tool(items=empty, template=template)
            assert result["item_count"] == 0
            assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "test-token" in calls[0]["url"]
    assert calls[0]["url"].endswith("/sendMessage")
    assert calls[0]["json"]["chat_id"] == "12345"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin AI", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert "status" not in result


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = TOOL_FUNCTIONS["lookup"](query="AI", timeframe=None)

    assert calls[0]["url"] == "https://api.tavily.com/search"
    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI"
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-key")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nbody text",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/final"},
    }}))

    result = TOOL_FUNCTIONS["fetch"](url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"] == {"url": "https://www.example.com/post", "formats": ["markdown"]}
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-key"
    assert result["items"][0] == {
        "title": "T",
        "url": "https://www.example.com/final",
        "source": "example.com",
        "summary": "# Hello\nbody text",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-key")
    fake_http(FakeResponse({"data": {"markdown": "z" * 9000, "metadata": {}}}))

    result = TOOL_FUNCTIONS["fetch"](url="https://example.com/long")

    summary = result["items"][0]["summary"]
    assert summary == "z" * 4000
    # With no metadata, title/url fall back to the requested URL.
    assert result["items"][0]["title"] == "https://example.com/long"
    assert result["items"][0]["url"] == "https://example.com/long"


# ---------------- timeline / social_search ----------------

def _raw_tweets() -> list[dict]:
    no_id = {"screen_name": "sama", "text": "no id here"}
    valid = [
        {"tweet_id": str(100 + i), "screen_name": "sama", "text": f"tweet {i}\nsecond line", "created_at": "2026-11-10"}
        for i in range(6)
    ]
    return [no_id, *valid]


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": _raw_tweets()}))

    result = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/timeline.php"
    assert calls[0]["params"] == {"screenname": "sama"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "rk"
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        "https://x.com/sama/status/100",
        "https://x.com/sama/status/101",
        "https://x.com/sama/status/102",
    ]
    assert result["items"][0]["title"] == "tweet 0"
    assert result["items"][0]["source"] == "@sama"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": _raw_tweets()}))

    top = TOOL_FUNCTIONS["social_search"](query="GPT-5", search_type="Top", limit=2)
    latest = TOOL_FUNCTIONS["social_search"](query="GPT-5")

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/search.php"
    assert calls[0]["params"] == {"query": "GPT-5", "search_type": "Top"}
    assert calls[1]["params"] == {"query": "GPT-5", "search_type": "Latest"}
    assert top["search_type"] == "Top"
    assert len(top["items"]) == 2
    assert len(latest["items"]) == 5  # default limit


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    policy = TOOL_FUNCTIONS["policy"]
    for query in ("", "   ", "là gì"):  # empty, whitespace, only stopwords
        result = policy(query=query)
        assert result["results"] == []
        assert "error" not in result


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    result = TOOL_FUNCTIONS["policy"](query="API key policy data", policy_area="data_privacy", top_k=5)

    assert result["policy_area"] == "data_privacy"
    assert result["results"], "expected at least one data_privacy hit"
    assert all(hit["policy_area"] == "data_privacy" for hit in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    result = TOOL_FUNCTIONS["policy"](query="injection probe citation", policy_area="source_citation", top_k=5)
    probe = [hit for hit in result["results"] if hit["section"] == "Injection probe"]

    assert probe, "the Injection probe section should be retrieved"
    hit = probe[0]
    assert any("ignore" in line.lower() for line in hit["untrusted_text"])
    assert "ignore" not in hit["facts"].lower()
    assert "untrusted" in result["trust_boundary"].lower()


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_my_new_tool_happy_path() -> None:
    pytest.skip(TODO)


def test_my_new_tool_bad_input_from_model() -> None:
    pytest.skip(TODO)


def test_my_new_tool_failure_returns_error_dict() -> None:
    pytest.skip(TODO)
