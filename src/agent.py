"""
agent.py
--------
Builds the search-enabled LangChain agent for the Local Travel Guide
Chatbot. The agent has access to:
  - find_nearby_attractions / find_nearby_restaurants (Google Places API)
  - plan_daily_budget / estimate_itinerary_cost (budget planning)

It uses the OpenAI tool-calling agent pattern (Agentic Concept: a
"Search-enabled Agent" that decides which tool to call, observes the
result, and can chain multiple tool calls before answering).
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from src.config import settings
from src.tools import get_places_tools, get_budget_tools

SYSTEM_PROMPT = """You are Wanderly, a friendly local travel guide chatbot.

Your job:
1. Help travelers discover nearby attractions and restaurants using the
   search tools available to you — never invent places, ratings, or
   addresses; only report what the tools return.
2. Help travelers plan a realistic budget for their trip using the
   budget tools, and connect it back to the places you found (e.g. use
   each place's price tier when estimating cost).
3. Ask a clarifying question if the traveler's location, budget, or
   trip length is missing or ambiguous — don't guess wildly.
4. Keep answers concise, structured, and practical. Use bullet points
   for lists of places. Always mention you're giving ballpark estimates
   for cost, not guaranteed prices.

You have tools for live search — use them instead of relying on your
own knowledge, since place listings and hours change over time.
"""


def build_agent(verbose: bool = None) -> AgentExecutor:
    """Construct and return a ready-to-invoke AgentExecutor."""
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
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
