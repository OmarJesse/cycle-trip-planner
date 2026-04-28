import streamlit as st
import requests
import datetime
import uuid

BASE_URL = "http://127.0.0.1:8000"
API_PATH = "/api/v1/chat"

st.set_page_config(
    page_title="Cycling Trip Planner",
    page_icon="🚴",
    layout="centered",
    initial_sidebar_state="expanded",
)

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())

if "conversation_ids" not in st.session_state:
    st.session_state.conversation_ids = {}

with st.sidebar:
    st.markdown("## 💬 Chat Sessions")
    with st.container():
        with st.expander("View Sessions", expanded=False):
            delete_keys = []
            for chat_id, data in st.session_state.chat_sessions.items():
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    if st.button(data["title"], key=f"title_{chat_id}"):
                        st.session_state.current_chat_id = chat_id
                with col2:
                    delete_button_key = f"del_{chat_id}"
                    if st.button("❌", key=delete_button_key):
                        delete_keys.append(chat_id)

            for key in delete_keys:
                del st.session_state.chat_sessions[key]
                st.session_state.conversation_ids.pop(key, None)
                if st.session_state.current_chat_id == key:
                    st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0] if st.session_state.chat_sessions else str(uuid.uuid4())
                    break

    st.markdown("---")
    if st.button("➕ New Chat"):
        new_chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_sessions[new_chat_id] = {"title": f"New Chat", "messages": []}
        st.session_state.conversation_ids[new_chat_id] = None

    st.markdown("---")
    st.markdown("## ⚙️ Backend")
    st.caption("Make sure FastAPI is running on `http://127.0.0.1:8000`.")
    BASE_URL = st.text_input("Base URL", value=BASE_URL)
    API_PATH = st.text_input("API Path", value=API_PATH)

    st.markdown("---")
    st.markdown("## 🧾 Preferences")
    pref_nationality = st.text_input("Nationality (for visa note)", value="")
    pref_month = st.selectbox("Travel month", ["", "May", "June", "July", "August", "September"], index=2)
    pref_daily_km = st.number_input("Daily km target", min_value=20, max_value=300, value=100, step=5)
    pref_lodging = st.selectbox("Lodging preference", ["mixed", "camping", "hostel", "hotel"], index=0)
    pref_hostel_every = st.number_input("Hostel every N nights (0=off)", min_value=0, max_value=30, value=4, step=1)
    if st.button("Reset conversation (this chat)"):
        st.session_state.conversation_ids[st.session_state.current_chat_id] = None

if st.session_state.current_chat_id not in st.session_state.chat_sessions:
    st.session_state.chat_sessions[st.session_state.current_chat_id] = {"title": "New Chat", "messages": []}

chat_data = st.session_state.chat_sessions[st.session_state.current_chat_id]
conversation_id = st.session_state.conversation_ids.get(st.session_state.current_chat_id)

st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🚴 Cycling Trip Planner Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Plan a multi-day cycling trip via chat</p>", unsafe_allow_html=True)
st.divider()

st.markdown("### Start chatting")
st.markdown("*Example:* `I want to cycle from Amsterdam to Copenhagen. I can do ~100km/day. Prefer camping but want a hostel every 4th night. Traveling in June.`")

tool_tab, chat_tab = st.tabs(["Tools", "Chat"])

with tool_tab:
    st.markdown("### Optional tools")
    tool = st.selectbox("Tool", ["get_points_of_interest", "check_visa_requirements", "estimate_budget"])

    if tool == "get_points_of_interest":
        with st.form("poi_form"):
            near = st.text_input("Near", value="Copenhagen")
            category = st.selectbox("Category", ["any", "sights", "food", "bike_shops", "nature", "museums"])
            limit = st.number_input("Limit", min_value=1, max_value=20, value=6, step=1)
            ok = st.form_submit_button("Run")
        if ok:
            r = requests.post(
                f"{BASE_URL}/api/v1/tools/points_of_interest",
                json={"near": near, "category": category, "limit": int(limit)},
                timeout=60,
            )
            st.json(r.json())

    if tool == "check_visa_requirements":
        with st.form("visa_form"):
            nationality = st.text_input("Nationality", value=pref_nationality or "Canadian")
            destination_country = st.text_input("Destination country", value="Denmark")
            stay_days = st.number_input("Stay days", min_value=1, max_value=365, value=14, step=1)
            ok = st.form_submit_button("Run")
        if ok:
            r = requests.post(
                f"{BASE_URL}/api/v1/tools/visa_requirements",
                json={"nationality": nationality, "destination_country": destination_country, "stay_days": int(stay_days)},
                timeout=60,
            )
            st.json(r.json())

    if tool == "estimate_budget":
        with st.form("budget_form"):
            days = st.number_input("Days", min_value=1, max_value=90, value=7, step=1)
            daily_distance_km = st.number_input("Daily km", min_value=20, max_value=300, value=int(pref_daily_km), step=5)
            lodging_style = st.selectbox("Lodging style", ["mixed", "camping", "hostel", "hotel"])
            food_style = st.selectbox("Food style", ["balanced", "budget", "treats"])
            ok = st.form_submit_button("Run")
        if ok:
            r = requests.post(
                f"{BASE_URL}/api/v1/tools/estimate_budget",
                json={
                    "days": int(days),
                    "daily_distance_km": int(daily_distance_km),
                    "lodging_style": lodging_style,
                    "food_style": food_style,
                },
                timeout=60,
            )
            st.json(r.json())

with chat_tab:
    st.markdown("### Chat")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Message", placeholder="Type your trip request or an adjustment…")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input.strip():
    with st.spinner("Planning..."):
        try:
            preferences = {
                "nationality": pref_nationality or None,
                "month": pref_month or None,
                "daily_km": int(pref_daily_km),
                "lodging_preference": pref_lodging,
                "hostel_every_n_nights": int(pref_hostel_every) if pref_hostel_every else None,
            }
            payload = {"conversation_id": conversation_id, "message": user_input, "preferences": preferences}
            response = requests.post(f"{BASE_URL}{API_PATH}", json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                answer = data.get("reply", "No reply returned.")
                new_conversation_id = data.get("conversation_id")
                st.session_state.conversation_ids[st.session_state.current_chat_id] = new_conversation_id

                message = {
                    "question": user_input,
                    "answer": answer,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                chat_data["messages"].append(message)

                suggested_title = user_input.strip()
                if len(suggested_title) > 30:
                    suggested_title = suggested_title[:27] + "..."
                chat_data["title"] = suggested_title

            else:
                details = None
                try:
                    details = response.json()
                except Exception:
                    details = response.text

                st.error(f"Bot failed to respond (HTTP {response.status_code}).")
                st.caption("Response details (from backend):")
                st.write(details)
        except Exception as e:
            st.error(f"Request failed due to: {e}")

if chat_data["messages"]:
    for msg in chat_data["messages"]:
        with st.chat_message("user"):
            st.markdown(msg["question"])
        with st.chat_message("assistant"):
            st.markdown(msg["answer"])
else:
    st.info("Start a chat to build your cycling itinerary.")

st.markdown("---")
st.markdown("<p style='text-align: center;'>Cycling Trip Planner Agent (demo UI)</p>", unsafe_allow_html=True)