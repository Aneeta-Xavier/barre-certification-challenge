"""
Build the Barre Core Coach knowledge base.

  python ingest.py

Steps
-----
1. Load barre-core YouTube transcripts (skips any without captions).
2. Load written barre-core workout guides (clean HTML -> text).
3. Load any PDFs dropped in data/pdfs/ (instructor manuals, anatomy books).
4. Save the raw corpus to data/combined_data.json (for inspection / eval).
5. Chunk (RecursiveCharacterTextSplitter, 800/50) and embed
   (OpenAI text-embedding-3-small), then persist a FAISS index to
   data/faiss_index/ for the app and the eval harness to reuse.

Chunking rationale: barre cues are short, self-contained instructions
("hold a hollow-body, ribs knitted, exhale on the crunch"). 800-character
chunks keep one full exercise/cue block intact while a 50-char overlap
preserves continuity across a cue that spans a boundary.
"""
import glob
import json
import os
import re

from dotenv import load_dotenv
from langchain_core.documents import Document

from data.barre_sources import BARRE_CORE_VIDEOS, GUIDE_URLS, PDF_DIR

load_dotenv()

DATA_DIR = "data"
CORPUS_JSON = os.path.join(DATA_DIR, "combined_data.json")
INDEX_DIR = os.path.join(DATA_DIR, "faiss_index")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 50


# --------------------------------------------------------------------------- #
# 1. YouTube transcripts (best-effort — captions are frequently unavailable)
# --------------------------------------------------------------------------- #
def _video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
    return m.group(1) if m else None


def load_youtube_docs(video_dict: dict) -> list[Document]:
    from youtube_transcript_api import YouTubeTranscriptApi

    docs: list[Document] = []
    for category, urls in video_dict.items():
        for url in urls:
            vid = _video_id(url)
            if not vid:
                continue
            try:
                transcript = YouTubeTranscriptApi.get_transcript(vid)
                text = "\n".join(entry["text"] for entry in transcript)
                if len(text.strip()) < 50:
                    raise ValueError("empty transcript")
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"source": url, "category": category, "type": "video"},
                    )
                )
                print(f"  ✅ transcript {vid} ({category})")
            except Exception as e:  # noqa: BLE001 - transcripts fail in many ways
                print(f"  ⚠️  no transcript for {url}: {e}")
    return docs


# --------------------------------------------------------------------------- #
# 2. Written workout guides (reliable full text)
# --------------------------------------------------------------------------- #
def load_guide_docs(urls: list[str]) -> list[Document]:
    from langchain_community.document_loaders import WebBaseLoader

    docs: list[Document] = []
    for url in urls:
        try:
            loaded = WebBaseLoader(url).load()
            for d in loaded:
                d.page_content = re.sub(r"\n{3,}", "\n\n", d.page_content).strip()
                d.metadata.update({"source": url, "category": "guide", "type": "article"})
            docs.extend(loaded)
            print(f"  ✅ guide {url}")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️  failed guide {url}: {e}")
    return docs


# --------------------------------------------------------------------------- #
# 3. PDFs (instructor manuals / core anatomy)
# --------------------------------------------------------------------------- #
def load_pdf_docs(pdf_dir: str) -> list[Document]:
    import fitz  # PyMuPDF

    docs: list[Document] = []
    for path in sorted(glob.glob(os.path.join(pdf_dir, "*.pdf"))):
        try:
            with fitz.open(path) as pdf:
                text = "\n".join(page.get_text() for page in pdf)
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": os.path.basename(path), "category": "textbook", "type": "pdf"},
                )
            )
            print(f"  ✅ pdf {os.path.basename(path)}")
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️  failed pdf {path}: {e}")
    return docs


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def main() -> None:
    os.makedirs(PDF_DIR, exist_ok=True)

    print("Loading YouTube transcripts…")
    video_docs = load_youtube_docs(BARRE_CORE_VIDEOS)
    print("Loading written guides…")
    guide_docs = load_guide_docs(GUIDE_URLS)
    print("Loading PDFs…")
    pdf_docs = load_pdf_docs(PDF_DIR)

    all_docs = video_docs + guide_docs + pdf_docs
    if not all_docs:
        raise SystemExit(
            "No documents loaded. Add PDFs to data/pdfs/ or check network access."
        )
    print(f"\n✅ Loaded {len(all_docs)} documents "
          f"({len(video_docs)} video, {len(guide_docs)} guide, {len(pdf_docs)} pdf)")

    with open(CORPUS_JSON, "w") as f:
        json.dump(
            [{"content": d.page_content, "metadata": d.metadata} for d in all_docs],
            f,
            indent=2,
        )
    print(f"✅ Wrote raw corpus -> {CORPUS_JSON}")

    # Chunk + embed + persist
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(all_docs)
    print(f"✅ Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(model=os.getenv("EMBED_MODEL", "text-embedding-3-small"))
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_DIR)
    print(f"✅ Saved FAISS index -> {INDEX_DIR}")


if __name__ == "__main__":
    main()
