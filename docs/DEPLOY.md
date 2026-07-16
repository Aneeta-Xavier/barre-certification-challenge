# Deploying Barre Core Coach to a public URL (Render)

The repo ships a prebuilt FAISS index (`data/faiss_index/`) and corpus
(`data/combined_data.json`), so the container serves the knowledge base without
re-ingesting — it only needs the 3 runtime API keys.

## One-time steps
1. Go to **[dashboard.render.com](https://dashboard.render.com)** and sign in with GitHub.
2. **New +** → **Web Service** → connect the repo
   **`Aneeta-Xavier/barre-certification-challenge`**.
3. Render auto-detects the **Dockerfile** (and `render.yaml`). Confirm:
   - Environment: **Docker**
   - Instance type: **Starter** (free tier works; first request is slow while the
     reranker model downloads).
4. Add the **Environment Variables** (Render dashboard → *Environment*), same keys
   as your local `.env`:
   | Key | Value |
   |---|---|
   | `OPENROUTER_API_KEY` | your OpenRouter key |
   | `OPENAI_API_KEY` | your OpenAI key |
   | `TAVILY_API_KEY` | your Tavily key |
   | `CHAT_MODEL` | `openai/gpt-4.1-mini` |
   | `EMBED_MODEL` | `text-embedding-3-small` |
   | `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
5. **Create Web Service**. First build takes a few minutes (pip install).
6. When it goes live, you get a public URL like
   `https://barre-core-coach.onrender.com` — open it on your phone and laptop.

> ⚠️ Enter the API keys **in Render's dashboard yourself** — never commit them.
> The `.env` file is git-ignored and stays on your machine.

## Redeploys
Every `git push` to `main` triggers an automatic redeploy.
