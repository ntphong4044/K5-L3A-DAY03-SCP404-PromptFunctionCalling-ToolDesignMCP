from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

TRANSCRIPTS_DIR = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
AGENT_VERSION = "v8"


@st.cache_resource
def load_agent_config() -> tuple[str, list[dict[str, object]]]:
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    declarations = load_tool_declarations(TOOLS_PATH)
    return prompt, to_openai_tools(declarations)


def configured_provider() -> tuple[str, str | None]:
    for name, env_name in (
        ("openai", "OPENAI_API_KEY"),
        ("openrouter", "OPENROUTER_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
    ):
        if os.getenv(env_name):
            return name, os.getenv("OPENAI_MODEL") if name == "openai" else None
    return "ollama", os.getenv("OLLAMA_MODEL")


def transcript_files() -> list[Path]:
    return sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), key=lambda path: path.stat().st_mtime, reverse=True)


def read_transcript(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def new_transcript() -> dict[str, Any]:
    version = build_artifact_version(AGENT_VERSION, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    provider_name, model = configured_provider()
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"{AGENT_VERSION}_{provider_name}_{timestamp}"
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "turns": [],
    }


def save_transcript(transcript: dict[str, Any]) -> None:
    if not transcript.get("turns"):
        return
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    transcript["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path = TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json"
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def reset_chat() -> None:
    save_transcript(st.session_state.get("active_transcript", {}))
    st.session_state.active_transcript = new_transcript()
    st.session_state.messages = []
    st.session_state.history = []


def load_chat(path: Path) -> None:
    transcript = read_transcript(path)
    st.session_state.active_transcript = transcript
    st.session_state.messages = [
        {"role": role, "content": content, "tools": tools}
        for turn in transcript.get("turns", [])
        for role, content, tools in (
            ("user", turn.get("user", ""), []),
            ("assistant", turn.get("assistant_text", ""), [
                event.get("tool") for event in turn.get("tool_events", []) if event.get("tool")
            ]),
        )
    ]
    st.session_state.history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]


def chat_title(path: Path) -> str:
    transcript = read_transcript(path)
    turns = transcript.get("turns", [])
    if turns and turns[0].get("user"):
        title = " ".join(str(turns[0]["user"]).split())
        return title[:38] + ("..." if len(title) > 38 else "")
    return path.stem


st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("🔎 Research Agent")
st.caption("Tìm kiếm web/X, đọc URL, tổng hợp digest và gửi Telegram sau khi xác nhận.")

provider_name, configured_model = configured_provider()
st.sidebar.caption(f"Provider: `{provider_name}`")
if configured_model:
    st.sidebar.caption(f"Model: `{configured_model}`")

files = transcript_files()
st.session_state.setdefault("messages", [])
st.session_state.setdefault("history", [])
st.session_state.setdefault("active_transcript", new_transcript())

if st.sidebar.button("✎  Trò chuyện mới", use_container_width=True):
    reset_chat()
    st.rerun()

st.sidebar.markdown("### Lịch sử chat")
if not files:
    st.sidebar.caption("Chưa có cuộc trò chuyện nào.")
for index, path in enumerate(files):
    turns = len(read_transcript(path).get("turns", []))
    label = f"{chat_title(path)} · {turns} lượt"
    if st.sidebar.button(label, key=f"history_{index}", use_container_width=True):
        load_chat(path)
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("tools"):
            st.caption("🔧 Tool: " + ", ".join(message["tools"]))

prompt = st.chat_input("Bạn muốn nghiên cứu điều gì?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "tools": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt, tools = load_agent_config()
    provider = make_provider(provider_name)
    messages = [
        *trim_history(st.session_state.history, 5),
        {"role": "user", "content": prompt},
    ]
    with st.chat_message("assistant"):
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=[{"role": "system", "content": system_prompt}, *messages],
                tools=tools,
                model=configured_model or getattr(provider, "default_model", None),
                max_tool_rounds=4,
            )
            answer = result["assistant_text"] or "Đã xử lý yêu cầu."
            called_tools = [
                event["tool"] for event in result.get("tool_events", []) if event.get("tool")
            ]
            st.markdown(answer)
            if called_tools:
                st.caption("🔧 Tool: " + ", ".join(called_tools))
            st.session_state.messages.append({
                "role": "assistant", "content": answer, "tools": called_tools,
            })
            st.session_state.history.extend(
                [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]
            )
            transcript = st.session_state.active_transcript
            transcript["turns"].append({
                "turn_index": len(transcript["turns"]) + 1,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "user": prompt,
                **result,
                "ended_at": datetime.now().isoformat(timespec="seconds"),
            })
            save_transcript(transcript)
        except Exception as exc:
            st.error(f"Không thể xử lý yêu cầu: {type(exc).__name__}: {exc}")
