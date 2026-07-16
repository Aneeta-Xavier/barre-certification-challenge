"""
Barre Core Coach — Chainlit chat app.

Runs in any phone or laptop browser and deploys to a public endpoint.
  chainlit run app.py

Architecture:
  browser chat  ->  Chainlit  ->  tool-calling agent (OpenRouter gateway)
                                      ├─ barre_core_kb  (FAISS RAG)
                                      └─ web_search     (Tavily)
  Memory: one LangChain ChatMessageHistory per browser session.
"""
import chainlit as cl
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory

from rag.agent import build_agent

load_dotenv()

# Build the agent once (loads FAISS + BM25); memory is per-session below.
AGENT = build_agent(retriever_mode="advanced")

WELCOME = (
    "👋 **Barre Core Coach** — your barre core & abs specialist.\n\n"
    "Ask me about standing or floor barre-core work: cues, form, progressions, "
    "modifications, or the anatomy behind a move. Try:\n"
    "- *How do I keep my lower back safe during barre bicycles?*\n"
    "- *Give me a 10-minute standing barre core sequence.*\n"
    "- *What's the difference between a hollow-body and a C-curve?*"
)


@cl.on_chat_start
async def start():
    cl.user_session.set("history", ChatMessageHistory())
    await cl.Message(content=WELCOME).send()


@cl.on_message
async def on_message(message: cl.Message):
    history: ChatMessageHistory = cl.user_session.get("history")

    result = await AGENT.ainvoke(
        {"input": message.content, "chat_history": history.messages}
    )
    answer = result["output"]

    # Persist this turn to session memory.
    history.add_user_message(message.content)
    history.add_ai_message(answer)

    # Surface which tools the agent used this turn (RAG vs web).
    tools_used = sorted({step[0].tool for step in result.get("intermediate_steps", [])})
    if tools_used:
        label = {"barre_core_kb": "📚 knowledge base", "web_search": "🌐 web"}
        answer += "\n\n---\n*Sources: " + ", ".join(
            label.get(t, t) for t in tools_used
        ) + "*"

    await cl.Message(content=answer).send()
