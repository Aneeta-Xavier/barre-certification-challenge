# Barre Core Coach 🩰

An **Agentic RAG** assistant for **barre core training** — standing and floor
abdominal/oblique barre work: cues, form, progressions, modifications, and the
anatomy behind each move. Ask it in any phone or laptop browser.

Built for the AI Makerspace **Certification Challenge**. 📄 **Full submission
document** (all 7 tasks, diagrams, eval numbers, product depth):
**[`docs/SUBMISSION.md`](docs/SUBMISSION.md)**.

> ⚕️ Fitness education, not medical advice. For injury, pregnancy, or
> diastasis-recti concerns, see a qualified professional.

## What it does
- **Grounds first in a private barre-core library** (YouTube transcripts +
  written guides + instructor/anatomy PDFs) via hybrid retrieval (BM25 + dense,
  cross-encoder reranked).
- **Falls back to live web search** (Tavily) for out-of-corpus / recent questions.
- **Remembers the conversation** per browser session for natural follow-ups.
- **Routes every model call through the OpenRouter LLM gateway.**

## Architecture
```
browser chat ─▶ Chainlit ─▶ tool-calling agent (OpenRouter gateway)
                              ├─ barre_core_kb  → FAISS (hybrid + rerank)
                              └─ web_search     → Tavily
                 memory: ChatMessageHistory per session
```
| Layer | Tech |
|-------|------|
| UI / server | Chainlit |
| Gateway | OpenRouter (`gpt-4.1-mini`) |
| Agent | LangChain tool-calling agent |
| Retrieval | FAISS + BM25 ensemble + FlashRank rerank |
| Embeddings | OpenAI `text-embedding-3-small` |
| Web tool | Tavily |
| Evals | RAGAS |

## Quickstart
```bash
pip install -r requirements.txt
cp .env.example .env          # add OPENROUTER_API_KEY, OPENAI_API_KEY, TAVILY_API_KEY

# add any barre/core PDFs to data/pdfs/ (see data/pdfs/README.md)
python ingest.py              # builds data/faiss_index/ + data/combined_data.json
chainlit run app.py           # http://localhost:8000
```

## Evaluate
```bash
python eval/generate_testset.py --size 12   # synthetic golden set (RAGAS)
python eval/run_ragas.py compare            # baseline vs advanced retriever table
```

## Repo layout
```
app.py                 Chainlit chat app (browser UI + session memory)
ingest.py              Build the knowledge base → FAISS
rag/agent.py           Agent: OpenRouter gateway + KB tool + Tavily + memory
rag/retriever.py       Baseline (dense) and advanced (hybrid+rerank) retrievers
data/barre_sources.py  Curated barre-CORE videos, guides, PDF list
eval/                  RAGAS test-set generator + baseline-vs-advanced harness
docs/SUBMISSION.md     ⭐ Full submission — all 7 tasks, diagrams, results
docs/DEPLOY.md         Render deploy steps
```
