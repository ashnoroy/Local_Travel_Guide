# 🧭 Local Travel Guide Chatbot (TRV-03)

A **search-enabled LangChain agent** that helps travelers find nearby attractions and restaurants, and plan a realistic trip budget — built for the **Agentic AI Project Catalogue** (Project ID: `TRV-03`, Level: **Intermediate**).

| | |
|---|---|
| **Project ID** | TRV-03 |
| **Core Concept** | Search-enabled Agent (LangChain) |
| **Key Features** | Nearby attractions, restaurants, budget planning |
| **Suggested API** | Google Places API |

---

## ✨ Features

- 🔍 **Search-enabled agent** — a LangChain tool-calling agent decides when to call live search tools instead of hallucinating place names or prices.
- 📍 **Nearby attractions** — geocodes a location and queries the Google Places API for tourist attractions, landmarks, and points of interest.
- 🍽️ **Nearby restaurants** — same pipeline, filterable by cuisine/keyword (e.g. "vegetarian", "street food").
- 💰 **Budget planning** — two dedicated tools:
  - `plan_daily_budget` — splits a total trip budget into a per-day, per-person allowance with a food/activities/transport breakdown.
  - `estimate_itinerary_cost` — estimates a low/high cost range for a set of planned stops based on each place's Google price tier.
- 💬 **Two front ends** — a Streamlit chat UI (`app.py`) and a terminal chat loop (`cli.py`).
- 🧪 **Unit tests** for the budget logic (no API keys required to run them).

---

## 🏗️ Architecture

```
User query
   │
   ▼
LangChain Tool-Calling Agent (ChatOpenAI)
   │
   ├──► find_nearby_attractions ──► Google Places API (places_nearby)
   ├──► find_nearby_restaurants ──► Google Places API (places_nearby)
   ├──► plan_daily_budget       ──► local budgeting logic
   └──► estimate_itinerary_cost ──► local budgeting logic (uses price_level)
   │
   ▼
Formatted, cited response back to the user
```

The agent is built with `create_tool_calling_agent`, so the LLM autonomously decides *which* tool(s) to call, in what order, and whether to chain a places search with a budget estimate — the defining trait of a search-enabled agentic system rather than a scripted chatbot.

---

## 📂 Project Structure

```
local-travel-guide-chatbot/
├── app.py                     # Streamlit chat UI
├── cli.py                     # Terminal chat loop
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── src/
│   ├── config.py              # Centralized settings / env loading
│   ├── agent.py                # Agent construction (prompt + tools + executor)
│   └── tools/
│       ├── places_tool.py     # Google Places API wrapper -> LangChain tools
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

### 2. Configure API keys

```bash
cp .env.example .env
```

Fill in `.env`:

```
OPENAI_API_KEY=sk-...
GOOGLE_PLACES_API_KEY=AIza...
```

You'll need:
- An **OpenAI API key** (or swap `ChatOpenAI` in `src/agent.py` for another LangChain chat model).
- A **Google Cloud** project with the **Places API** (and **Geocoding API**) enabled — [console.cloud.google.com](https://console.cloud.google.com/apis/credentials).

### 3. Run it

**Streamlit UI:**
```bash
streamlit run app.py
```

**Terminal:**
```bash
python cli.py
```

---

## 💬 Example prompts

- "Find attractions near Jaipur, India"
- "Suggest budget-friendly vegetarian restaurants near Amer Fort"
- "I have $300 for 3 days with 2 travelers — plan my daily budget"
- "I'm visiting 2 moderate restaurants and 1 expensive attraction, 2 people — what's that going to cost?"
- "Find attractions near Jaipur and estimate the cost of visiting the top 3 with lunch at a nearby restaurant"

---

## 🧪 Running tests

```bash
pip install -r requirements.txt
python tests/test_budget_tool.py
# or
pytest tests/
```

The budget tests run fully offline — no API keys needed. The Places tools are exercised through the live app/CLI since they depend on the Google Places API.

---

## 🔑 Notes & limitations

- Google Places' `price_level` is a 0–4 scale, not a real price — `estimate_itinerary_cost` maps it to a **ballpark USD band** (see `PRICE_BAND_USD` in `src/tools/budget_tool.py`). Tune these bands for your destination/currency.
- The agent will only report places actually returned by the Places API — if nothing is found nearby, it says so rather than inventing results.
- Swap the LLM provider by editing `ChatOpenAI(...)` in `src/agent.py` to any other LangChain-supported chat model.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
