# Barre Core Assistant — Product Requirements Document
### An AI-powered at-home coach for barre *core* training

> Companion to [`WRITEUP.md`](WRITEUP.md), which maps each certification task to
> its deliverable. This PRD is the product narrative; the writeup is the
> task-by-task rubric answer. Both describe the **same** shipped system:
> a Chainlit agentic-RAG app, routed through the **OpenRouter** LLM gateway, with
> per-session **memory**, a hybrid **BM25 + dense + rerank** retriever, and a
> **Tavily** web-search agent — runnable in any phone/laptop browser.

---

## Certification rubric map

| Task | Where it's answered |
|---|---|
| 1 — Problem, audience, workflow, eval questions | *Problem Statement*, *Consumer Pain Points*, [`WRITEUP.md` Task 1](WRITEUP.md) (current-workflow diagram + eval Qs) |
| 2 — Solution, infra diagram, agent-flow diagram, gateway/memory/browser | *Product Vision*, *Technical Architecture*, [`WRITEUP.md` Task 2](WRITEUP.md) (diagrams) |
| 3 — Data sources + chunking | *Data & Chunking*, Appendix B |
| 4 — Prototype + public deploy | *Technical Architecture*; code in `app.py`, `ingest.py`, `rag/` |
| 5 — Test set, eval harness, conclusions | *Evaluation Framework* (real RAGAS numbers) |
| 6 — Advanced retriever + comparison + 2nd improvement | *Retrieval Quality & Improvements* |
| 7 — Next steps | *Roadmap* |

---

## Executive Summary
The **Barre Core Assistant** is an AI-powered application that makes barre
**core** training — the standing and floor abdominal/oblique work at the heart of
every barre class — accessible, affordable, and personalized at home. Barre is
one of the most popular low-impact modalities for core strength, posture, and
stability, but studio access is expensive and time-bound, and the online
alternatives are unsearchable video libraries. This PRD describes how an agentic
Retrieval-Augmented Generation (RAG) system delivers grounded, safety-aware,
on-demand answers about barre-core form, cues, progressions, and anatomy — a
studio-quality "ask the instructor" experience in a scalable, browser-based
format.

---

## Context — the barre market landscape
Barre has become one of the most durable segments of boutique fitness. Built from
ballet, Pilates, and isometric strength work, it draws a loyal base — heavily
women aged 25–45 — who value posture, core strength, and low-impact training.
Chains like Pure Barre, Barre3, and The Bar Method have made it a national
category, and at-home platforms (Peloton, Alo Moves, Apple Fitness+) have proven
that this demographic will adopt digital fitness.

Yet demand meets structural barriers:
- **Cost:** studio memberships commonly run **$150–$250/month** ($1,800–$3,000+/yr).
- **Access & scheduling:** prime class times book up; suburban/rural users travel.
- **The digital gap:** at-home barre is *video*, which you cannot ask a question.

*(Market framing here is directional analysis, not a claim of completed user
research; it builds on prior work exploring an AI at-home fitness assistant.)*

---

## Consumer pain points
Recurring themes for the target user (at-home barre enthusiasts and newer barre
instructors building core blocks):

1. **No personalization mid-class.** Group classes of 10–20 can't correct each
   person's form; modifications for injuries or **diastasis recti** are rarely
   addressed.
2. **Digital alternatives fall short.** YouTube barre is a 10–20 min video with no
   search — you can't ask "which move protects my lower back?" Generic apps give
   "barre-inspired" routines without precise, cue-level guidance.
3. **Safety concerns.** Without form cues, users risk lumbar strain in core work;
   online content rarely flags contraindications for postpartum or injured users.
4. **Scattered knowledge.** The real answers live across video transcripts, blog
   guides, and dense instructor manuals — never in one searchable place.

These point to a need for **safe, affordable, personalized, barre-core guidance
on demand**.

---

## Competitive landscape
| Platform | Strengths | Weaknesses |
|---|---|---|
| YouTube (free) | Huge library | No personalization, no search, no grounding |
| Peloton / Apple Fitness+ | Community + polish | Barre is a minor category; no Q&A |
| Alo Moves | Premium niche instructors | Video only; no adaptive answers |
| Local studios | Hands-on correction | Expensive; limited access |

**Gap identified:** a digital-first, **barre-core-specific** assistant that
*answers questions* with grounded, safety-aware guidance at a fraction of studio
cost.

---

## Problem Statement (Task 1)
> People doing barre workouts at home cannot get trustworthy, on-demand answers
> about **core-specific** barre technique — the cues, form corrections,
> progressions, and the anatomy behind each move — at the moment they need them.

The at-home barre user (and the newer barre instructor) wants to perform or teach
core work correctly and safely, and to understand *why* a cue matters. Today they
scrub through videos, open a second tab to Google an anatomy term, and dig through
PDF manuals — slow, repetitive, and error-prone, with no way to verify an answer
is safe and barre-specific. The Barre Core Assistant closes that gap with grounded
retrieval over a curated barre-core corpus plus a web-search fallback.

---

## Product Vision
Not to replicate the studio, but to reimagine the *ask-the-instructor* moment:
a knowledgeable barre-core coach available 24/7, grounded in expert content,
delivered conversationally, and affordable at scale.

**User journey.** The user opens the app in a browser (phone or laptop) and asks:
- *"How do I keep my lower back safe during barre bicycles?"*
- *"Give me a 10-minute standing barre core sequence."*
- *"What's the difference between a hollow-body and a C-curve?"*

The agent retrieves relevant passages from the curated barre-core corpus,
synthesizes a grounded answer via `gpt-4.1-mini` (through the OpenRouter gateway),
adds a safety note where relevant, and remembers the conversation so follow-ups
("make that easier on my knees") need no repetition. When the corpus can't answer
(new classes, gear, recent guidance), it calls Tavily web search and labels the
source.

---

## Technical Architecture (Task 2)
Deliberately lightweight and modular for fast iteration and cheap hosting:

| Component | Choice | Why |
|---|---|---|
| LLM | `gpt-4.1-mini` | Strong grounded synthesis at low cost/latency. |
| **LLM gateway** | **OpenRouter** | One OpenAI-compatible key; swap/fallback models without code changes. |
| Agent framework | LangChain tool-calling agent | Mature, model-agnostic agent + tools. |
| Tools | `barre_core_kb` (retriever) + `web_search` (Tavily) | Ground in private data; cover the long tail. |
| Embeddings | OpenAI `text-embedding-3-small` | Cheap, high-quality; embeddings run direct-to-OpenAI. |
| Vector store | FAISS (local, persisted) | Zero-ops, ships in the container. |
| Advanced retriever | BM25 + dense **ensemble → FlashRank rerank** | Lexical + semantic recall, then precision rerank — no GPU. |
| **Memory** | LangChain `ChatMessageHistory` per session | Multi-turn follow-ups without a database. |
| Evaluation | RAGAS | Purpose-built RAG metrics for before/after evidence. |
| Monitoring | Chainlit traces + LangChain callbacks | Per-turn tool/latency visibility. |
| UI | Chainlit | Mobile+desktop browser chat with streaming + sessions. |
| Deployment | Docker → Render (public HTTPS) | Container runs anywhere; secret env vars. |

Infrastructure and agent-workflow **diagrams** are in
[`WRITEUP.md` Task 2](WRITEUP.md).

> **Note on the advanced retriever.** A *prior* iteration of this project explored
> a **fine-tuned Snowflake Arctic embedding** model as the retrieval upgrade. For
> the barre build we chose **hybrid retrieval + cross-encoder reranking** instead:
> it is deployable with no GPU, requires no training run, and — critically — we
> can A/B it against the baseline with the eval harness (see below). Fine-tuned
> domain embeddings remain a documented future option.

---

## Data & Chunking (Task 3)
**Sources (private RAG corpus)** — see `data/barre_sources.py`, built by
`ingest.py`:
1. **Barre-core YouTube transcripts** (standing + floor), fetched when captions
   are available.
2. **Written barre-core workout guides** — reliable full-text fallback so the
   corpus is never thin when captions fail (they frequently do).
3. **Instructor manuals & core-anatomy PDFs** in `data/pdfs/`.

**External API (Agent):** **Tavily** web search (`web_search` tool) — the
freshness/long-tail layer. The agent treats the **corpus as primary ground truth**
and **Tavily as fallback**, labeling which source each part of an answer came from.

**Chunking:** `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=50)`.
Barre content is a stream of short, self-contained cues; an 800-char window keeps
one full exercise/cue block (and its *why*) intact in a single chunk, maximizing
the chance a retrieved chunk fully answers a question, while staying small enough
for precise retrieval and low token cost. The 50-char overlap preserves continuity
across boundaries. The same chunk set backs the BM25 index so lexical and dense
retrieval stay aligned.

---

## Evaluation Framework (Task 5)
Accuracy and trust are safety requirements here — a wrong cue on spinal loading is
harm, not a typo. We combine automated RAGAS metrics with the option of
human-in-the-loop review.

**Test set:** a synthetic golden set generated from the barre corpus with RAGAS
(`eval/generate_testset.py`, 12 `{question, reference}` pairs).
**Harness:** `eval/run_ragas.py` runs each question through a chosen retriever and
scores six metrics, with the evaluator LLM routed through the gateway.

**Baseline results (dense-only retriever, k=5; 14-doc / 958-chunk corpus):**

| Metric | Value | Read |
|---|---|---|
| Faithfulness | 0.8232 | Well-grounded. |
| Answer Relevancy | 0.8028 | On-topic answers. |
| Context Recall | 0.6643 | Right chunks usually retrieved. |
| Context Entity Recall | 0.4949 | Moderate on exact anatomy terms. |
| Factual Correctness (F1) | 0.4592 | Some over-generalization. |
| Noise Sensitivity (↓) | 0.4193 | Distraction from extra chunks. |

**Conclusion:** relevancy and grounding are healthy; the weak spots are **factual
correctness and noise sensitivity** — across a large mixed corpus the retriever
pulls in loosely-related chunks that dilute precision. The problem is **too much
extra context, not too little** — a precision problem, which motivates reranking.

---

## Retrieval Quality & Improvements (Task 6)
### Advanced retriever — hybrid + rerank
Barre cues mix exact anatomical vocabulary ("transverse abdominis," "C-curve,"
"posterior pelvic tilt") with paraphrased instruction. **BM25** recovers exact-term
matches a pure embedding model misses, the **dense** arm catches paraphrase, and a
**FlashRank cross-encoder** reranks to the chunk that actually answers the question.

**Baseline vs Advanced vs Advanced-tuned (same 12 questions, 958-chunk corpus):**

| Metric | Baseline | Advanced | Advanced-tuned |
|---|---|---|---|
| Faithfulness | 0.8232 | 0.8180 | **0.8764** |
| Factual Correctness | 0.4592 | 0.5392 | **0.5533** |
| Context Recall | 0.6643 | 0.7117 | **0.7415** |
| Context Entity Recall | 0.4949 | 0.3518 | 0.4453 |
| Answer Relevancy | **0.8028** | 0.7450 | 0.7500 |
| Noise Sensitivity (↓) | 0.4193 | 0.3126 | **0.3144** |

**Honest read:** plain reranking (Advanced) was a **precision-for-recall
tradeoff** — more factually correct and far less noisy, but it over-trimmed
entity-rich context (Entity Recall 0.49 → 0.35).

### Second improvement — tuned retriever (eval-driven)
Because the eval *diagnosed* the over-trimming, the second change widens the
funnel: `candidate_k` 12 → 24, reranked `k` 5 → 8, ensemble weighted toward the
dense arm (`advanced_tuned` in `rag/retriever.py`). It **worked**: entity recall
recovered (+0.094 vs Advanced) and Faithfulness hit **0.876 — best of all three**,
with every other metric flat or up. `advanced_tuned` is the shipped default.
Full deltas in [`WRITEUP.md` Task 6.3](WRITEUP.md).

---

## Guardrails & Responsible AI
A barre-core coach operates in a **safety-critical** domain; guardrails are core,
not optional.

| Guardrail | Implementation | Purpose |
|---|---|---|
| Hallucination mitigation | RAG grounding; answer from retrieved context | Prevent fabricated cues |
| Scope restriction | System prompt keeps it to barre core; declines off-topic | Clear boundaries |
| Safety disclaimers | Mandatory note for injury/pregnancy/diastasis + "see a professional" | Avoid harm |
| Context awareness | Prompts for injury/level where relevant | Personalization |
| Human-in-the-loop (future) | Instructor review of golden answers; thumbs up/down | External validation |

Responsible-AI principles: **transparency** (answers label their sources: 📚 KB /
🌐 web), **safety-first** (caution over creativity), **inclusivity** (modifications
for levels and life stages), **continuous monitoring** (track flagged answers).

---

## Value Proposition
Make high-quality barre-core guidance accessible and safe at home — grounded form
cues and expert-backed answers at a fraction of studio cost — reducing barriers of
expense, geography, and inconsistent instruction while increasing confidence,
safety, and habit formation.

**Pricing direction:** freemium for discovery; **$12–18/month** premium — roughly
**5–10× cheaper than studio** memberships, competitive with generic fitness apps
but barre-core-specialized.

**Market sizing (directional):** barre sits inside the multi-billion-dollar U.S.
boutique-fitness category; a digital, barre-specific assistant targets the
cost-sensitive 25–45 demographic underserved by video-only apps. Figures are
estimates to validate, not booked revenue.

---

## Roadmap / Next Steps (Task 7)
**Keep:** the agentic RAG + Tavily-fallback trust model; hybrid + rerank retriever;
Chainlit + OpenRouter (fast, mobile, model-swappable); the RAGAS harness that turns
"feels better" into measured deltas.

**Improve:**
- **Richer corpus:** caption-verified core videos + properly licensed manuals;
  per-chunk metadata (move name, standing/floor, difficulty) for filtered retrieval.
- **Durable memory:** move from per-session to a lightweight store so a returning
  user's injuries/level persist.
- **Structured outputs:** sequences as step lists with reps/tempo + source-video
  timestamps.
- **Safety-guardrail eval:** an LLM-as-judge check that injury/pregnancy answers
  always include the safety note.
- **Cost/latency:** cache embeddings and rerank; smaller reranker for mobile.
- **Longer term:** thumbs up/down feedback loop; expansion to adjacent modalities.

---

## FAQ
**Q: How is this different from YouTube or a fitness app?** It *answers questions*
with grounded, barre-core-specific guidance and labels its sources — video and
generic apps can't.
**Q: Why FAISS not Pinecone?** Cost-free local prototyping that ships in the
container; a managed DB is a scale-time option.
**Q: How does it handle injuries / postpartum?** It prompts for context, adds a
safety note, and recommends a professional; final medical clearance is the user's.
**Q: What if it hallucinates?** Answers are grounded in retrieved context;
out-of-corpus questions route to web search and are labeled; future LLM-as-judge
moderation is planned.

---

## Appendices
**A — Chunking parameters**

| Parameter | Value | Notes |
|---|---|---|
| Chunk size | 800 | Keeps a full cue/exercise block intact |
| Overlap | 50 | Continuity across boundaries |
| Retriever k (baseline) | 5 | Configurable |
| Retriever k / candidate_k (tuned) | 8 / 24 | Task 6.3 second improvement |

**B — Sample golden questions** (barre core): "key cues for a hollow-body hold,"
"keep the low back safe in barre bicycles," "hollow-body vs C-curve," "modify core
work for diastasis recti," "why cue 'knit the ribs'." (Full set:
`eval/golden_testset.json`.)

**C — System prompt** (see `SYSTEM_PROMPT` in `rag/agent.py`): constrains scope to
barre core, forces `barre_core_kb` first, requires grounding, mandates a safety
note for injury/pregnancy/diastasis, and keeps answers tight and actionable.
