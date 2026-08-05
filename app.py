"""
app.py
------
Streamlit front-end for the Local Travel Guide Chatbot (TRV-03).

Run with:
    streamlit run app.py
"""

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from src.agent import build_agent, run_agent
from src.config import settings

st.set_page_config(page_title="Wanderly — Local Travel Guide Chatbot", page_icon="🧭", layout="centered")

st.title("🧭 Wanderly — Local Travel Guide Chatbot")
st.caption(
    "Search-enabled agent · Nearby attractions & restaurants · Budget planning "
    "· Powered by LangChain + Google Places API"
)

with st.sidebar:
    st.header("⚙️ Trip Settings")
    st.text_input("Currency", value=settings.DEFAULT_CURRENCY, key="currency_hint")
    st.number_input(
        "Search radius (meters)",
        min_value=500,
        max_value=20000,
        value=settings.DEFAULT_SEARCH_RADIUS_METERS,
        step=500,
        key="radius_hint",
    )
    st.markdown("---")
    st.markdown(
        "**Try asking:**\n"
        "- *Find attractions near Jaipur, India*\n"
        "- *Suggest vegetarian restaurants near Amer Fort*\n"
        "- *I have $300 for 3 days, 2 travelers — plan my budget*\n"
        "- *Estimate cost for 2 moderate restaurants and 1 expensive attraction*"
    )
    if st.button("🔄 Reset conversation"):
        st.session_state.clear()
        st.rerun()

# --- Validate config before doing anything else ---
try:
    settings.validate()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

# --- Session state setup ---
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = build_agent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # LangChain message objects
if "display_history" not in st.session_state:
    st.session_state.display_history = []  # (role, text) tuples for rendering

# --- Render past messages ---
for role, text in st.session_state.display_history:
    with st.chat_message(role):
        st.markdown(text)

# --- Chat input ---
user_input = st.chat_input("Ask about attractions, restaurants, or your travel budget…")

if user_input:
    st.session_state.display_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Searching and planning…"):
            try:
                reply = run_agent(
                    st.session_state.agent_executor,
                    user_input,
                    st.session_state.chat_history,
                )
            except Exception as exc:
                reply = f"Sorry, something went wrong: {exc}"
            st.markdown(reply)

    st.session_state.chat_history.append(HumanMessage(content=user_input))
    st.session_state.chat_history.append(AIMessage(content=reply))
    st.session_state.display_history.append(("assistant", reply))
