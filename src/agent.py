"""
agent.py
--------
Builds the search-enabled LangChain agent for the Local Travel Guide
Chatbot, running entirely on FREE platforms:

  - LLM: Groq (free API key, no credit card) via ChatGroq.
  - Places search: OpenStreetMap (Nominatim + Overpass) — no key at all.
  - Budget planning: local logic, no external calls.

The Groq key is passed in by the caller — typically the Streamlit
sidebar — so each visitor uses their own free key instead of the app
owner's.
"""

from langchain.agents import create_tool_calling_agent
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from src.config import settings
from src.tools.places_tool import get_places_tools
from src.tools.budget_tool import get_budget_tools

SYSTEM_PROMPT = """You are Wanderly, a friendly local travel guide chatbot.

Your job:
1. Help travelers discover nearby attractions and restaurants using the
   search tools available to you — never invent places or addresses;
   only report what the tools return. Places come from OpenStreetMap,
   so mention that listings/hours may be incomplete for some spots.
2. Help travelers plan a realistic budget for their trip using the
   budget tools. Since OpenStreetMap doesn't provide prices, ask the
   traveler for a rough price tier (free/budget/moderate/expensive) for
   each place when estimating cost, rather than guessing.
3. Ask a clarifying question if the traveler's location, budget, or
   trip length is missing or ambiguous — don't guess wildly.
4. Keep answers concise, structured, and practical. Use bullet points
   for lists of places. Always mention cost figures are ballpark
   estimates, not guaranteed prices.

You have tools for live search — use them instead of relying on your
own knowledge, since place listings and hours change over time.
"""


def build_agent(groq_api_key: str, verbose: bool = None) -> AgentExecutor:
    """
    Construct and return a ready-to-invoke AgentExecutor, scoped to the
    Groq API key passed in (per-user key, not a shared server secret).
    Places search needs no key at all — it's free/keyless OpenStreetMap.
    """
    llm = ChatGroq(
        model=settings.LLM_MODEL,
        api_key=groq_api_key,
        temperature=0.3,
    )

    tools = get_places_tools() + get_budget_tools()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose if verbose is not None else settings.AGENT_VERBOSE,
        handle_parsing_errors=True,
    )


def run_agent(agent_executor: AgentExecutor, user_input: str, chat_history: list) -> str:
    """Invoke the agent with the running chat history and return its text reply."""
    result = agent_executor.invoke(
        {"input": user_input, "chat_history": chat_history}
    )
    return result["output"]
