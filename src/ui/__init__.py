from __future__ import annotations

import requests
import streamlit as st

from src.ui import chat, state
from src.ui.api_client import build_preferences, send_message
from src.ui.constants import BACKEND_URL
from src.ui.sidebar import SidebarValues, render as render_sidebar
from src.ui.tool_calls import render as render_tool_calls


_HIDE_TOOLBAR_CHROME = """
<style>
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
.stDeployButton { display: none !important; }
</style>
"""


def configure_page() -> None:
    st.set_page_config(
        page_title="Cycling Trip Planner",
        page_icon="🚴",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_HIDE_TOOLBAR_CHROME, unsafe_allow_html=True)


def run() -> None:
    configure_page()
    state.init()

    sidebar = render_sidebar()
    chat.render_header()
    chat.render_empty_state()
    chat.render_history()

    prompt = st.chat_input("Describe your trip, or ask the agent to adjust the plan...")
    if prompt:
        _handle_turn(prompt, sidebar)


def _handle_turn(prompt: str, sidebar: SidebarValues) -> None:
    state.append_user(prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    preferences = build_preferences(
        nationality=sidebar.nationality,
        month=sidebar.month,
        daily_km=sidebar.daily_km,
        lodging=sidebar.lodging,
        hostel_every=sidebar.hostel_every,
    )

    with st.chat_message("assistant"):
        with st.spinner("Planning..."):
            data = _call_backend(prompt, preferences)
            if data is None:
                st.stop()

        reply = data.get("reply") or "_(empty reply)_"
        st.session_state.conversation_id = data.get("conversation_id") or st.session_state.conversation_id

        if data.get("error"):
            st.warning(f"agent flag: {data['error']}")

        st.markdown(reply)

        tool_calls_data = data.get("tool_calls", [])
        rounds = int(data.get("rounds") or 0)
        state.append_assistant(reply, tool_calls_data, rounds)
        render_tool_calls(tool_calls_data, rounds)


def _call_backend(prompt: str, preferences: dict) -> dict | None:
    try:
        return send_message(BACKEND_URL, st.session_state.conversation_id, prompt, preferences)
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            retry_after = e.response.headers.get("Retry-After")
            wait = f" Wait {retry_after}s before trying again." if retry_after else ""
            st.warning(f"You're sending requests too quickly.{wait}")
            return None
        st.error(f"Backend error {e.response.status_code}")
        try:
            st.json(e.response.json())
        except Exception:
            st.code(e.response.text)
        return None
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
        return None
