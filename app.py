"""
app.py
------
Streamlit front-end for the Local Travel Guide Chatbot (TRV-03).

Runs entirely on FREE platforms:
  - Groq (free LLM API key, no credit card) — each visitor enters their
    own key in the sidebar; it lives only in that browser session's
    st.session_state, never written to disk or shown to other users.
  - OpenStreetMap (Nominatim + Overpass) for places search — no key
    needed at all.

Run with:
    streamlit run app.py
"""

import base64
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from src.agent import build_agent, run_agent
from src.config import settings

st.set_page_config(page_title="Wanderly — Local Travel Guide Chatbot", page_icon="🧭", layout="centered")


def set_background(image_path: str) -> None:
    """
    Set a full-page background image via base64-embedded CSS.

    Base64-embedding (rather than a plain file path) is what makes this
    work both locally AND once deployed on Streamlit Cloud, since the
    browser can't otherwise reach a server-side file path.
    A dark translucent overlay is layered on top so text/widgets stay
    readable against a busy photo.
    """
    path = Path(image_path)
    if not path.exists():
        return  # fail quietly — app still works without a background
    encoded = base64.b64encode(path.read_bytes()).decode()
    ext = path.suffix.lstrip(".")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(10, 20, 20, 0.72), rgba(10, 20, 20, 0.72)),
                url("data:image/{ext};base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        [data-testid="stSidebar"] {{
            background-color: rgba(10, 20, 20, 0.85);
        }}
        [data-testid="stChatMessage"] {{
            background-color: rgba(20, 30, 30, 0.75);
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


set_background(str(Path(__file__).parent / "assets" / "background.jpg"))

st.title("🧭 Wanderly — Local Travel Guide Chatbot")
st.caption(
    "Search-enabled agent · Nearby attractions & restaurants · Budget planning "
    "· Powered by LangChain + Groq (free LLM) + OpenStreetMap (free places)"
)

# --- Sidebar: each visitor supplies their own FREE Groq API key ---
with st.sidebar:
    st.header("🔑 Your Groq API Key")
    st.caption(
        "Free, no credit card required. Your key is used only for your "
        "session and is never stored, logged, or shown to other users."
    )
    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        value=st.session_state.get("groq_api_key", ""),
        help="Get a free key at console.groq.com/keys — no credit card needed.",
    )
    st.markdown(
        "[👉 Get a free Groq API key](https://console.groq.com/keys)",
        help="Sign up, go to API Keys, click 'Create API Key'.",
    )

    keys_changed = groq_api_key != st.session_state.get("groq_api_key", "")
    st.session_state.groq_api_key = groq_api_key

    st.markdown("---")
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
        "- *Suggest restaurants near Amer Fort*\n"
        "- *I have $300 for 3 days, 2 travelers — plan my budget*\n"
        "- *Estimate cost for 2 moderate restaurants and 1 expensive attraction*"
    )
    st.caption("Places search runs on free OpenStreetMap data — no key needed for that part.")
    if st.button("🔄 Reset conversation"):
        for key in ("agent_executor", "chat_history", "display_history"):
            st.session_state.pop(key, None)
        st.rerun()

# --- Gate the app until a Groq key is present ---
if not groq_api_key:
    st.info("👈 Enter your free Groq API key in the sidebar to start chatting.")
    st.stop()

# --- (Re)build the agent if it doesn't exist yet, or the key changed ---
if "agent_executor" not in st.session_state or keys_changed:
    try:
        st.session_state.agent_executor = build_agent(groq_api_key=groq_api_key)
    except Exception as e:
        st.error(f"Couldn't start the agent with the key provided: {e}")
        st.stop()

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
