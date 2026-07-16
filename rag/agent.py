"""
Agentic RAG core for Barre Core Coach.

An OpenRouter-gated tool-calling agent with two tools:
  * barre_core_kb   -> retrieval over the private barre-core knowledge base (RAG)
  * web_search      -> Tavily search for anything outside the KB (recency, gear,
                       studios, "is this safe with diastasis recti?", etc.)

The agent decides per turn whether to ground its answer in the private corpus,
reach out to the web, or both. Conversation memory is passed in by the caller
(the Chainlit app keeps one message history per browser session).
"""
import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from rag.retriever import get_retriever

SYSTEM_PROMPT = """You are **Barre Core Coach**, a focused assistant for BARRE \
CORE work only — standing and floor abdominal/oblique barre exercises, the cues, \
form, progressions, modifications, and the anatomy behind them.

Rules:
- For anything about barre-core technique, cues, form, or anatomy, ALWAYS call \
`barre_core_kb` first and ground your answer in what it returns. Cite the move \
or source when helpful.
- Use `web_search` only when the knowledge base lacks the answer or the user \
asks about current/external info (new classes, equipment, studios, research).
- If a question is outside barre core (e.g. nutrition plans, unrelated sports), \
say so briefly and steer back to barre core.
- Be concrete and safe: give form cues, common mistakes, and modifications. \
Add a one-line safety note for pregnancy/injury/diastasis-recti questions and \
recommend a professional when appropriate. You are not a medical provider.
- Keep answers tight and actionable."""


def _llm(temperature: float = 0) -> ChatOpenAI:
    """Chat model routed through the OpenRouter LLM gateway."""
    return ChatOpenAI(
        model=os.getenv("CHAT_MODEL", "openai/gpt-4.1-mini"),
        temperature=temperature,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def _web_search_tool():
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    @tool
    def web_search(query: str) -> str:
        """Search the public web for barre-core info not in the knowledge base:
        current classes, equipment, studios, or recent guidance."""
        res = client.search(query=query, search_depth="basic", max_results=4)
        return "\n\n".join(
            f"{r['title']}\n{r['url']}\n{r['content']}" for r in res["results"]
        ) or "No results."

    return web_search


def build_agent(retriever_mode: str = "advanced") -> AgentExecutor:
    """Construct the tool-calling agent executor."""
    retriever = get_retriever(mode=retriever_mode, k=5)
    kb_tool = create_retriever_tool(
        retriever,
        name="barre_core_kb",
        description=(
            "Search the private barre-core knowledge base of workout transcripts, "
            "instructor manuals, and core-anatomy references. Use for any question "
            "about barre-core exercises, cues, form, progressions, or anatomy."
        ),
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    tools = [kb_tool, _web_search_tool()]
    agent = create_tool_calling_agent(_llm(), tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=True,
        max_iterations=6,
    )
