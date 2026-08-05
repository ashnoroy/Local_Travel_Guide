# 🧭 Local Travel Guide Chatbot (TRV-03)

A **search-enabled LangChain agent** that helps travelers find nearby attractions and restaurants, and plan a realistic trip budget — built entirely on **free platforms**, no credit card required anywhere.

| | |
|---|---|
| **Project ID** | TRV-03 |
| **Core Concept** | Search-enabled Agent (LangChain) |
| **Key Features** | Nearby attractions, restaurants, budget planning |
| **LLM** | [Groq](https://console.groq.com/keys) — free API key, no card |
| **Places data** | [OpenStreetMap](https://www.openstreetmap.org/) — free, no key at all |

---

## ✨ Features

- 🔍 **Search-enabled agent** — a LangChain tool-calling agent decides when to call live search tools instead of hallucinating place names.
- 📍 **Nearby attractions** — geocodes a location via Nominatim and queries the Overpass API for tourist attractions, landmarks, and points of interest tagged on OpenStreetMap.
- 🍽️ **Nearby restaurants** — same pipeline, filterable by cuisine keyword.
- 💰 **Budget planning** — two dedicated tools:
  - `plan_daily_budget` — splits a total trip budget into a per-day, per-person allowance with a food/activities/transport breakdown.
  - `estimate_itinerary_cost` — estimates a low/high cost range for a set of planned stops based on a stated price tier (free/budget/moderate/expensive).
- 💬 **Two front ends** — a Streamlit chat UI (`app.py`) with a background image and per-visitor API key input, and a terminal chat loop (`cli.py`).
- 🧪 **Unit tests** for the budget logic (no API keys required to run them).
- 💸 **Zero cost to run** — Groq's free tier covers the LLM, OpenStreetMap needs no key at all.

---

## 🏗️ Architecture

```
User query
   │
   ▼
LangChain Tool-Calling Agent (ChatGroq — free LLM)
   │
   ├──► find_nearby_attractions ──► OpenStreetMap (Nominatim + Overpass)
   ├──► find_nearby_restaurants ──► OpenStreetMap (Nominatim + Overpass)
   ├──► plan_daily_budget       ──► local budgeting logic
   └──► estimate_itinerary_cost ──► local budgeting logic
   │
   ▼
Formatted response back to the user
```

The agent is built with `create_tool_calling_agent`, so the LLM autonomously decides *which* tool(s) to call, in what order, and whether to chain a places search with a budget estimate.

---

## 📂 Project Structure

```
local-travel-guide-chatbot/
├── app.py                     # Streamlit chat UI (per-visitor Groq key input)
├── cli.py                     # Terminal chat loop
├── requirements.txt
├── runtime.txt                # Pins Python 3.11 for reliable wheel installs
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── assets/
│   └── background.jpg         # App background image
├── src/
│   ├── config.py              # Centralized settings / env loading
│   ├── agent.py                # Agent construction (ChatGroq + tools + executor)
│   └── tools/
│       ├── places_tool.py     # OpenStreetMap wrapper -> LangChain tools (no key needed)
│       └── budget_tool.py     # Budget planning -> LangChain tools
└── tests/
    └── test_budget_tool.py    # Offline unit tests for budget logic
```

---

## ⚙️ Setup

### 1. Clone and install

```bash
git clone https://github.com/ashnoroy/local-travel-guide-chatbot.git
cd local-travel-guide-chatbot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get your free Groq API key

1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Sign up (no credit card required)
3. Click **"Create API Key"** and copy it

That's the *only* key this project needs — places search runs on free, keyless OpenStreetMap APIs.

### 3. Configure

```bash
cp .env.example .env
```

Fill in `.env`:
```
GROQ_API_KEY=gsk_...
```

### 4. Run it

**Streamlit UI** (each visitor enters their own free Groq key in the sidebar):
```bash
streamlit run app.py
```

**Terminal** (reads the key from your local `.env`):
```bash
python cli.py
```

---

## 💬 Example prompts

- "Find attractions near Jaipur, India"
- "Suggest restaurants near Amer Fort"
- "I have $300 for 3 days with 2 travelers — plan my daily budget"
- "I'm visiting 2 moderate restaurants and 1 expensive attraction, 2 people — what's that going to cost?"

---

## 🧪 Running tests

```bash
pip install -r requirements.txt
python tests/test_budget_tool.py
# or
pytest tests/
```

The budget tests run fully offline — no API keys needed. The places tools are exercised through the live app/CLI since they call live OpenStreetMap endpoints.

---

## 🔑 Notes & limitations

- OpenStreetMap is community-contributed, so coverage and detail (hours, cuisine tags, price info) vary by location — the agent is instructed to report only what's actually returned, and say so when nothing is found.
- OpenStreetMap has no price data, so `estimate_itinerary_cost` relies on you (or the agent, when it asks) providing a rough price tier per stop, rather than pulling it automatically.
- Groq's free tier has generous but not unlimited rate limits — if you hit a rate-limit error, wait a bit or check your usage at console.groq.com.
- Swap the LLM provider by editing `ChatGroq(...)` in `src/agent.py` for any other LangChain-supported chat model.
- The Overpass API's public instance is also free but shared/rate-limited; for heavy production use, consider self-hosting an Overpass instance or using a paid provider.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
