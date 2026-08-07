# DocTalk

**Upload a PDF and chat with it.** DocTalk is a RAG + agentic-AI assistant: you drop in a document, and an agent answers questions about it with page-cited answers — deciding on its own whether to search the document, summarize it, look up a GitHub repo, or search the web.

🔗 **Live demo:** [doctalk-param-dufngphraqdvh8hm.austriaeast-01.azurewebsites.net](https://doctalk-param-dufngphraqdvh8hm.austriaeast-01.azurewebsites.net)


---

## Why I built this

I wanted a project that went past "RAG in a notebook" and actually demonstrated **agentic** behavior — a system that makes real routing decisions instead of always doing the same thing — and that I could take all the way to a live, deployed URL. DocTalk is the result: a working product where an LLM agent genuinely chooses between four tools per question, grounded in a document the user uploads, running end-to-end at **$0** on free tiers.

The build taught me the parts of ML engineering that don't show up in tutorials: session isolation, containerization, handling rate limits, chasing down deprecated APIs, and the reality that "free" cloud hosting is a maze of tradeoffs.

---

## What it does

- **Upload any PDF** → it's chunked, embedded, and stored in a session-isolated vector store.
- **Ask questions** → a LangGraph agent routes each one to the right tool:
  - `retrieve_document` — semantic search over the uploaded PDF (the default for document questions)
  - `summarize_document` — a map-reduce summary over the whole document
  - `github_repo_info` — live GitHub repo lookups via the REST API
  - `tavily_search` — web search for facts outside the document
- **Cited answers** — document answers come back with `[page N]` citations.
- **Conversational memory** — follow-ups work naturally ("what about the decoder?" after asking about the encoder).

---

## Architecture

```
                        ┌─────────────────────────────────────────┐
   Browser ──────────▶  │  Streamlit UI  (chat + file upload)    │
                        └───────────────────┬─────────────────────┘
                                            │ HTTP (127.0.0.1)
                        ┌───────────────────▼─────────────────────┐
                        │  FastAPI backend                        │
                        │    POST /upload   POST /chat            │
                        └───────────────────┬─────────────────────┘
                                            │
                     ┌──────────────────────┼──────────────────────┐
                     ▼                      ▼                       ▼
              ┌────────────┐        ┌──────────────┐        ┌──────────────┐
              │ Ingestion  │        │ Session-     │        │  LangGraph   │
              │ pypdf →    │        │ scoped Chroma│        │  agent       │
              │ chunk      │        │ vector store │        │  (router)    │
              └────────────┘        └──────────────┘        └──────┬───────┘
                                                                   │ picks one:
                                        ┌──────────────┬───────────┼───────────┐
                                        ▼              ▼           ▼           ▼
                                   retrieve      summarize      github      web search
                                   (Chroma)     (map-reduce)   (REST API)   (Tavily)
```

Both servers run inside **one Docker container** (Streamlit on the public port, FastAPI internal on 8000) — deployed to Azure App Service via Docker Hub.

**Stack:** Python 3.11 · FastAPI · Streamlit · LangGraph · LangChain Core · Chroma · Google Gemini (embeddings + chat) · Docker · Azure App Service

---

## Design decisions

I made a few deliberate choices worth calling out — including the tradeoffs, because the tradeoffs are the interesting part.

**Session-isolated vector stores.** Each upload gets its own Chroma collection keyed by a `session_id`, so one user's document can never leak into another's answers. The store's `build()` is idempotent (it clears any existing collection first), so re-uploading never silently duplicates chunks.

**Built directly on `pypdf` + `langchain-core`, not `langchain-community`.** The community package was archived (sunset) in mid-2026, so I load PDFs with `pypdf` directly and hand-construct `langchain-core` Document objects. Fewer dependencies, and I actually understand what a Document is.

**Google Gemini on the free tier.** `gemini-embedding-001` for embeddings, `gemini-3.1-flash-lite` for chat — chosen for a genuinely usable free tier (no credit card, function calling, 1M context). I pin a *specific* model rather than an alias like `-latest`, after an alias silently drifted to a lower-quota model and cost me a day of debugging. Because the model name lives in `params.yaml`, swapping it is a one-line change. (Note: free-tier prompts may be used by Google for training — fine for a public-document demo.)

**One container, two processes.** The Docker purist rule is one process per container, but Azure App Service gives me a single container, so I run Streamlit + FastAPI together via a startup script. It's a deliberate, documented compromise — at real scale I'd split them into separate services.

**Hardening for a public app.** Since it's live, I added: a per-document chunk cap (rejects oversized PDFs *before* spending any embedding calls — this is what maps to the real rate limit, not file size), exponential-backoff retry on Gemini 429s, and a per-session question cap so no single session can drain the shared daily quota.

---

## Evaluation

I hand-wrote a 15-question eval set against a fixed document ("Attention Is All You Need"), covering all the routing paths (retrieval, summarize, GitHub), and a scorer that checks two things independently: did the retriever surface the right page, and did the final answer contain the correct fact.

| Metric | Score |
|---|---|
| Retrieval hit-rate | **92%** (12/13) |
| Answer accuracy | **100%** (15/15) |

Run it yourself with `python eval/run_eval.py`.

---

## Running it locally

**1. Clone and install:**

```bash
git clone https://github.com/ParamMalviya/doctalk.git
cd doctalk
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

**2. Add your API keys** — copy `.env.example` to `.env` and fill in:

```
GOOGLE_API_KEY=your_key      # required (Gemini)
TAVILY_API_KEY=your_key      # required (web search)
GITHUB_TOKEN=your_token      # optional (raises GitHub rate limit)
```

**3. Get the test document** (gitignored, not committed):

```bash
# PowerShell:
Invoke-WebRequest -Uri "https://arxiv.org/pdf/1706.03762v7" -OutFile "eval/test_document.pdf"
```

**4. Run both servers** (two terminals):

```bash
uvicorn main:app --reload                 # FastAPI backend :8000
streamlit run ui/streamlit_app.py         # Streamlit UI :8501
```

Then open the Streamlit URL, upload a PDF, and start chatting.

### Or run the container

```bash
docker build -t doctalk .
docker run --rm -p 8080:8080 --env-file .env doctalk
# open http://localhost:8080
```

---

## Deployment

DocTalk is containerized and deployed to **Azure App Service** (free F1 tier) with the image hosted on Docker Hub. API keys are injected at runtime as Application settings — never baked into the image. Total hosting cost: **$0** (Azure F1 is always-free; Gemini and Tavily run on free tiers).

---

## Config

Non-secret settings live in `config.yaml` and `params.yaml` so they're tunable without touching code:

| Setting | Value |
|---|---|
| Chunk size / overlap | 1000 / 200 |
| Retriever `k` | 5 |
| Embeddings | `gemini-embedding-001` (3072-dim) |
| Chat model | `gemini-3.1-flash-lite` |
| Temperature | 0.0 (grounded, focused answers) |

---

## Project structure

```
src/doctalk/
├── api/            FastAPI routes + schemas
├── components/     ingestion, vector store, retriever, tools, agent, session store
├── pipelines/      stage_01_ingestion, stage_02_chat
├── config/         ConfigurationManager
├── logger/         shared logging
└── exception/      shared error handling
eval/               eval set + scoring script
ui/                 Streamlit app
research/           development notebooks
```
