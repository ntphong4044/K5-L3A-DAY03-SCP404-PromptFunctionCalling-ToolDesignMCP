from __future__ import annotations

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

load_lab_env(ROOT)


@st.cache_resource
def load_agent_config() -> tuple[str, list[dict[str, object]]]:
    prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    return prompt, to_openai_tools(declarations)


st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("🔎 Research Agent")
st.caption("Tìm kiếm web/X, đọc URL, tổng hợp digest và gửi Telegram sau khi xác nhận.")

provider_name = st.sidebar.selectbox("Provider", ["openai", "openrouter", "ollama"])
model = st.sidebar.text_input("Model (tuỳ chọn)", value="")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Bạn muốn nghiên cứu điều gì?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
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
                model=model or getattr(provider, "default_model", None),
                max_tool_rounds=4,
            )
            answer = result["assistant_text"] or "Đã xử lý yêu cầu."
            st.markdown(answer)
            for event in result.get("tool_events", []):
                st.caption(f"Tool: {event['tool']}")
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.history.extend(
                [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]
            )
        except Exception as exc:
            st.error(f"Không thể xử lý yêu cầu: {type(exc).__name__}: {exc}")
