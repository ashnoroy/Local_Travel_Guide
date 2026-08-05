"""
cli.py
------
Terminal chat loop for the Local Travel Guide Chatbot — useful for quick
testing without spinning up Streamlit. Reads keys from your local .env
file (fine for single-user terminal use).

Run with:
    python cli.py
"""

from langchain_core.messages import AIMessage, HumanMessage

from src.agent import build_agent, run_agent
from src.config import settings


def main() -> None:
    settings.validate()
    agent_executor = build_agent(
        openai_api_key=settings.OPENAI_API_KEY,
        google_places_api_key=settings.GOOGLE_PLACES_API_KEY,
    )
    chat_history = []

    print("🧭 Wanderly — Local Travel Guide Chatbot (type 'exit' to quit)\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Safe travels! 👋")
            break
        if not user_input:
            continue

        reply = run_agent(agent_executor, user_input, chat_history)
        print(f"\nWanderly: {reply}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=reply))


if __name__ == "__main__":
    main()
