"""
Generate a synthetic golden test set from the barre-core corpus (RAGAS).

  python eval/generate_testset.py [--size 12]

Writes eval/golden_testset.json with {user_input, reference} rows. Both
retriever variants are later scored against this same set by run_ragas.py.

The generator LLM is routed through the OpenRouter gateway; embeddings use
OpenAI directly (gateways don't proxy embeddings).
"""
import argparse
import json
import os

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator

load_dotenv()

CORPUS_JSON = "data/combined_data.json"
OUT = "eval/golden_testset.json"


def _gateway_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("EVAL_MODEL", "openai/gpt-4.1-mini"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def main(size: int) -> None:
    with open(CORPUS_JSON) as f:
        raw = json.load(f)
    docs = [Document(page_content=r["content"], metadata=r["metadata"]) for r in raw]

    generator = TestsetGenerator(
        llm=LangchainLLMWrapper(_gateway_llm()),
        embedding_model=LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model=os.getenv("EMBED_MODEL", "text-embedding-3-small"))
        ),
    )
    testset = generator.generate_with_langchain_docs(docs, testset_size=size)
    df = testset.to_pandas()

    rows = [
        {"user_input": r["user_input"], "reference": r.get("reference", "")}
        for _, r in df.iterrows()
    ]
    os.makedirs("eval", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"✅ Wrote {len(rows)} test questions -> {OUT}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--size", type=int, default=12)
    main(p.parse_args().size)
