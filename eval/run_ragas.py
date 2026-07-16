"""
Score a retriever variant against the golden test set with RAGAS.

  python eval/run_ragas.py baseline     # dense-only FAISS (Tasks 1-4)
  python eval/run_ragas.py advanced     # hybrid + rerank  (Task 6)
  python eval/run_ragas.py compare      # run both, print a side-by-side table

Writes eval/results/ragas_<mode>.csv and prints a mean-metric markdown table.
Everything routes through the OpenRouter gateway; embeddings use OpenAI.
"""
import json
import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from rag.retriever import get_retriever

load_dotenv()

GOLDEN = "eval/golden_testset.json"
RESULTS_DIR = "eval/results"

QA_PROMPT = ChatPromptTemplate.from_template(
    "You are Barre Core Coach. Answer the question using ONLY the context.\n"
    "If the context is insufficient, say so.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)


def _gateway_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("EVAL_MODEL", "openai/gpt-4.1-mini"),
        temperature=0,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def run_pipeline(mode: str) -> pd.DataFrame:
    """Answer every golden question with the given retriever; collect contexts."""
    retriever = get_retriever(mode=mode, k=5)
    chain = QA_PROMPT | _gateway_llm() | StrOutputParser()

    with open(GOLDEN) as f:
        golden = json.load(f)

    records = []
    for i, row in enumerate(golden, 1):
        q = row["user_input"]
        try:
            docs = retriever.invoke(q)
            contexts = [d.page_content[:1500] for d in docs]
            answer = chain.invoke({"context": "\n\n".join(contexts), "question": q})
            records.append(
                {
                    "user_input": q,
                    "response": answer,
                    "retrieved_contexts": contexts,
                    "reference": row.get("reference", ""),
                }
            )
            print(f"  [{mode}] {i}/{len(golden)} ✓")
            time.sleep(0.5)  # be gentle with rate limits
        except Exception as e:  # noqa: BLE001
            print(f"  [{mode}] {i}/{len(golden)} ✗ {e}")
    return pd.DataFrame(records)


def evaluate_df(df: pd.DataFrame):
    from ragas import EvaluationDataset, RunConfig, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        ContextEntityRecall,
        FactualCorrectness,
        Faithfulness,
        LLMContextRecall,
        NoiseSensitivity,
        ResponseRelevancy,
    )

    dataset = EvaluationDataset.from_pandas(df)
    result = evaluate(
        dataset=dataset,
        metrics=[
            LLMContextRecall(),
            Faithfulness(),
            FactualCorrectness(),
            ResponseRelevancy(),
            ContextEntityRecall(),
            NoiseSensitivity(),
        ],
        llm=LangchainLLMWrapper(_gateway_llm()),
        embeddings=LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model=os.getenv("EMBED_MODEL", "text-embedding-3-small"))
        ),
        run_config=RunConfig(timeout=360, max_retries=10, max_workers=4),
    )
    return result.to_pandas()


def score(mode: str) -> pd.Series:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df = run_pipeline(mode)
    scored = evaluate_df(df)
    scored.to_csv(os.path.join(RESULTS_DIR, f"ragas_{mode}.csv"), index=False)
    return scored.mean(numeric_only=True).round(4)


def markdown_table(summaries: dict[str, pd.Series]) -> str:
    metrics = sorted(next(iter(summaries.values())).index)
    header = "| Metric | " + " | ".join(summaries) + " |\n"
    header += "| --- | " + " | ".join("---" for _ in summaries) + " |\n"
    body = ""
    for m in metrics:
        name = m.replace("_", " ").title()
        body += f"| {name} | " + " | ".join(
            f"{summaries[mode].get(m, float('nan')):.4f}" for mode in summaries
        ) + " |\n"
    return header + body


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "compare"
    modes = ["baseline", "advanced"] if mode == "compare" else [mode]
    summaries = {m: score(m) for m in modes}
    print("\n📊 RAGAS mean metrics\n")
    print(markdown_table(summaries))


if __name__ == "__main__":
    main()
