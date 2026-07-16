"""
Retrievers for Barre Core Coach.

baseline  : dense-only FAISS similarity search (OpenAI embeddings), k=5.
            This is the Task 1-4 retriever.

advanced  : hybrid ensemble (BM25 lexical + dense semantic) whose union is
            re-scored by a FlashRank cross-encoder reranker. This is the
            Task 6 retriever.

Why advanced helps here: barre cues mix exact anatomical terms ("transverse
abdominis", "hollow-body", "C-curve") with paraphrased instruction. BM25 nails
the exact-term recall a pure embedding model misses, the dense arm catches
semantic paraphrase, and the cross-encoder reranker then promotes the chunk
that actually answers the question to the top.
"""
import json
import os

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = "data"
CORPUS_JSON = os.path.join(DATA_DIR, "combined_data.json")
INDEX_DIR = os.path.join(DATA_DIR, "faiss_index")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 50


def _embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=os.getenv("EMBED_MODEL", "text-embedding-3-small"))


def load_vectorstore() -> FAISS:
    """Load the FAISS index built by ingest.py."""
    if not os.path.isdir(INDEX_DIR):
        raise FileNotFoundError(
            f"No FAISS index at {INDEX_DIR}. Run `python ingest.py` first."
        )
    return FAISS.load_local(
        INDEX_DIR, _embeddings(), allow_dangerous_deserialization=True
    )


def load_chunks():
    """Re-create the exact chunk set from the raw corpus (for BM25)."""
    from langchain_core.documents import Document

    with open(CORPUS_JSON) as f:
        raw = json.load(f)
    docs = [Document(page_content=r["content"], metadata=r["metadata"]) for r in raw]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)


def get_baseline_retriever(k: int = 5):
    """Dense-only similarity retriever (Tasks 1-4)."""
    return load_vectorstore().as_retriever(search_kwargs={"k": k})


def get_advanced_retriever(k: int = 5, candidate_k: int = 12):
    """Hybrid (BM25 + dense) union, cross-encoder reranked to top-k (Task 6)."""
    from langchain.retrievers import ContextualCompressionRetriever, EnsembleRetriever
    from langchain_community.retrievers import BM25Retriever
    from langchain_community.document_compressors import FlashrankRerank

    dense = load_vectorstore().as_retriever(search_kwargs={"k": candidate_k})

    bm25 = BM25Retriever.from_documents(load_chunks())
    bm25.k = candidate_k

    hybrid = EnsembleRetriever(retrievers=[bm25, dense], weights=[0.4, 0.6])

    reranker = FlashrankRerank(top_n=k)
    return ContextualCompressionRetriever(
        base_compressor=reranker, base_retriever=hybrid
    )


def get_retriever(mode: str = "advanced", k: int = 5):
    """Factory: mode in {'baseline', 'advanced'}."""
    if mode == "baseline":
        return get_baseline_retriever(k=k)
    return get_advanced_retriever(k=k)
