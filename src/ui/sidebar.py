from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from src.ui import state
from src.ui.api_client import health
from src.ui.constants import (
    BACKEND_URL,
    DAILY_KM_DEFAULT,
    DAILY_KM_MAX,
    DAILY_KM_MIN,
    DAILY_KM_STEP,
    HOSTEL_CADENCE_DEFAULT,
    HOSTEL_CADENCE_MAX,
    HOSTEL_CADENCE_MIN,
    LODGING_OPTIONS,
    MONTH_OPTIONS,
)


@dataclass
class SidebarValues:
    nationality: str
    month: str
    daily_km: int
    lodging: str
    hostel_every: int


def render() -> SidebarValues:
    prefs = st.session_state.prefs

    if st.session_state.view_mode != "sidebar":
        return _values_from_prefs(prefs)

    with st.sidebar:
        st.markdown("### 🚴 Trip Planner")

        info = health(BACKEND_URL)
        if info:
            st.success(f"Backend online · {info['provider']}/{info['model']}", icon="✅")
        else:
            st.error(f"Backend unreachable at {BACKEND_URL}", icon="🔌")
            st.caption("Start with `./src/scripts/backend.sh`")

        st.divider()
        st.markdown("**Preferences**")
        month = st.selectbox(
            "Travel month",
            MONTH_OPTIONS,
            index=MONTH_OPTIONS.index(prefs["month"]) if prefs["month"] in MONTH_OPTIONS else 4,
        )
        daily_km = st.slider(
            "Daily km target",
            min_value=DAILY_KM_MIN,
            max_value=DAILY_KM_MAX,
            value=int(prefs["daily_km"]),
            step=DAILY_KM_STEP,
        )
        lodging = st.selectbox(
            "Lodging style",
            LODGING_OPTIONS,
            index=LODGING_OPTIONS.index(prefs["lodging"]) if prefs["lodging"] in LODGING_OPTIONS else 0,
        )
        hostel_every = st.number_input(
            "Hostel cadence (every N nights, 0 = off)",
            min_value=HOSTEL_CADENCE_MIN,
            max_value=HOSTEL_CADENCE_MAX,
            value=int(prefs["hostel_every"]),
            step=1,
        )
        nationality = st.text_input("Nationality (for visa note, optional)", value=prefs["nationality"])

        st.divider()
        st.button("🗑️ New conversation", on_click=state.reset, use_container_width=True)

    prefs["month"] = month
    prefs["daily_km"] = int(daily_km)
    prefs["lodging"] = lodging
    prefs["hostel_every"] = int(hostel_every)
    prefs["nationality"] = nationality

    return _values_from_prefs(prefs)


def _values_from_prefs(prefs: dict) -> SidebarValues:
    return SidebarValues(
        nationality=prefs["nationality"],
        month=prefs["month"],
        daily_km=int(prefs["daily_km"]),
        lodging=prefs["lodging"],
        hostel_every=int(prefs["hostel_every"]),
    )
