"""
Barre CORE data sources for the RAG corpus.

Scope: core / abdominal / oblique barre work ONLY (standing + floor).
This is the barre-core replacement for last year's reformer-Pilates sources.

Three source types, in decreasing reliability:
  1. GUIDE_URLS  - written barre-core workout articles (always fetchable text)
  2. PDF_DIR     - instructor manuals / anatomy books you legitimately own
  3. VIDEOS      - YouTube barre-core workouts (captions fetched when available)

Ingestion tries all three and simply skips any source that fails, so an empty
YouTube transcript never breaks the corpus.
"""

# ---------------------------------------------------------------------------
# 1. Written barre-core workout guides (reliable, full-text)
# ---------------------------------------------------------------------------
GUIDE_URLS = [
    "https://www.nourishmovelove.com/10-minute-barre-core-workout/",
    "https://www.nourishmovelove.com/barre-class-workout-video/",
    "https://tgffitness.com/workouts/10-minute-barre-abs-workout/",
    "https://evergreenclinic.ca/a-complete-guide-to-barre-pilates/",
    "https://la-pilatesstudio.com/what-is-barre-pilates/",
]

# ---------------------------------------------------------------------------
# 2. PDFs you place in data/pdfs/ (instructor manuals, core-anatomy books).
#    Only use materials you can legitimately obtain (publicly posted manuals,
#    library/archive lending, your own copies). Filenames are matched by glob,
#    so this list is documentation only — every *.pdf in data/pdfs/ is loaded.
# ---------------------------------------------------------------------------
PDF_DIR = "data/pdfs"
SUGGESTED_PDFS = [
    "BootyBarre-Manual-Pro-Series-5.pdf",   # publicly posted instructor manual
    "core-training-anatomy-ellsworth.pdf",  # core-muscle anatomy (own copy)
    "barre-fitness-devito.pdf",             # 100 barre exercises (own copy)
]

# ---------------------------------------------------------------------------
# 3. YouTube barre-CORE workouts, categorized (captions used when present).
# ---------------------------------------------------------------------------
BARRE_CORE_VIDEOS = {
    "barre_core_floor": [
        "https://www.youtube.com/watch?v=DZE1MH5mxnI",  # 20 min Core & Abs
        "https://www.youtube.com/watch?v=yqU0tFZgd4E",  # 15 min Barre Abs (ballet)
        "https://www.youtube.com/watch?v=WuRpt7G1vrk",  # 10 min Barre Abs (Pilates)
        "https://www.youtube.com/watch?v=JQkVss0tobs",  # 10 min Barre Abs (dancer)
    ],
    "barre_core_standing": [
        "https://www.youtube.com/watch?v=RkVn8xoBdNA",  # 10 min Standing Core (Marnie Alton)
        "https://www.youtube.com/watch?v=KcY7ITTDecs",  # 10 min Standing Barre Core
        "https://www.youtube.com/watch?v=tlZPJbgv5f0",  # 10 min Standing Core Barre
        "https://www.youtube.com/watch?v=nhavmfvB25E",  # 5 min Standing Oblique & Abs
    ],
}
