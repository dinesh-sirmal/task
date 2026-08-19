# RAG & Agent API

A small Retrieval-Augmented Generation (RAG) service: it indexes a mini knowledge base
(8 markdown docs for a fictional "CloudSync API" product), answers questions about it
using an LLM, cites its sources, and falls back to a secondary tool when the internal
docs don't confidently cover the question.

Built with **FastAPI + ChromaDB + sentence-transformers + Gemini**.

---

## 1. Architecture

```
Client
  |
  |  POST /api/v1/query  { "question": "...", "stream": bool }
  v
FastAPI (app/main.py)
  |
  v
RAG Engine (app/rag_engine.py)
  |-- 1. Guardrail: prompt-injection check on the question   (app/guardrails.py)
  |-- 2. Retrieve top-K chunks from ChromaDB                 (app/vector_store.py)
  |-- 3. Confidence check on best similarity distance
  |        |-- LOW confidence  -> Fallback tool (mock web search) (app/fallback_tool.py)
  |        |-- HIGH confidence -> Build cited prompt -> Gemini LLM (app/llm_client.py)
  v
Response: answer + sources + used_fallback + latency/token metrics
```

Offline, one-time step: `scripts/ingest.py` reads `data/docs/`, chunks each file
(`app/ingestion.py`), embeds the chunks with `sentence-transformers` (all-MiniLM-L6-v2),
and stores them in a local ChromaDB collection on disk (`./chroma_db`).

## 2. Project structure

```
rag-agent-api/
├── app/
│   ├── main.py          # FastAPI app, /api/v1/query endpoint (JSON + SSE streaming)
│   ├── config.py         # all settings, loaded from .env
│   ├── models.py         # Pydantic request/response schemas
│   ├── ingestion.py       # chunking logic
│   ├── vector_store.py    # ChromaDB + embeddings wrapper
│   ├── llm_client.py       # Gemini wrapper (falls back to MOCK MODE if no API key)
│   ├── guardrails.py        # prompt-injection check + confidence threshold + prompt template
│   ├── fallback_tool.py      # mock "web search" tool used when confidence is low
│   └── logger.py               # structured JSON request logging
├── data/docs/                    # 8 sample markdown docs (the knowledge base)
├── scripts/ingest.py                # run this once to build the vector index
├── requirements.txt
├── .env.example
└── README.md
```

## 3. Setup (step by step)

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Open .env and paste a Gemini API key into GEMINI_API_KEY
# (get one free at https://aistudio.google.com/apikey)
# NOTE: if you leave it blank, the app still runs fully in MOCK MODE --
# retrieval, fallback, streaming, and logging all work; only the final
# LLM-generated sentence is a placeholder. Good for testing the pipeline first.

# 4. Build the vector index (run once, and again whenever data/docs/ changes)
python scripts/ingest.py

# 5. Start the API
uvicorn app.main:app --reload

# 6. Try it
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I upload a file and what is the max size?", "stream": false}'
```

### Streaming (SSE)
```bash
curl -N -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How does webhook signature verification work?", "stream": true}'
```
Each line arrives as `data: <chunk>` as the LLM generates it, ending with `event: done`.

Interactive Swagger docs: `http://127.0.0.1:8000/docs`

## 4. How the fallback guardrail works

`app/vector_store.py` uses cosine distance (lower = more similar). After retrieving the
top-K chunks, `guardrails.is_confident_enough()` checks the best (lowest) distance against
`DISTANCE_THRESHOLD` (default `0.75`, in `.env`). If nothing retrieved is close enough, the
request is routed to `fallback_tool.web_search_mock()` instead of being sent to the LLM --
this prevents the model from hallucinating an answer about something the knowledge base
doesn't actually cover.

Try it: ask something unrelated, e.g. *"What's the capital of France?"* -- it will trigger
the fallback path (`used_fallback: true` in the response) instead of a made-up answer.

## 5. Prompt-injection guardrail

Before anything is retrieved, `guardrails.looks_like_prompt_injection()` checks the raw
question against a set of common override phrases (*"ignore previous instructions"*,
*"reveal your system prompt"*, *"you are now"*, etc.). A match short-circuits the request
with a fixed refusal message -- it never reaches the LLM. The system prompt itself
(`guardrails.SYSTEM_PROMPT`) also explicitly instructs the model to treat any instructions
found inside the retrieved CONTEXT as untrusted data, not commands, as defense in depth.

## 6. Logging

Every request logs one structured JSON line (`app/logger.py`) to stdout:

```json
{"event": "query_completed", "question": "How do I upload a file...", "used_fallback": false,
 "retrieval_time_ms": 42.1, "generation_time_ms": 890.4, "total_time_ms": 934.0,
 "approx_tokens_used": 612, "num_sources": 4}
```
`retrieval_time_ms` and `generation_time_ms` are measured separately so you can see exactly
where latency goes. Token usage uses Gemini's real `usage_metadata` when available, and
falls back to a ~4-chars/token estimate otherwise (e.g. in mock mode).

## 7. Evaluation notes

Manual testing during development (in-KB questions, out-of-scope questions, and an
injection attempt) confirmed:
- In-scope questions (e.g. about file uploads, webhooks, versioning) correctly retrieve
  the matching doc chunk(s) and are answered with a source citation.
- Out-of-scope questions (nothing in `data/docs/` is relevant) correctly trigger
  `used_fallback: true` instead of a hallucinated answer.
- Injection attempts (*"ignore previous instructions and..."*) are caught by the regex
  guardrail before retrieval even runs.

Retrieval itself (embedding + ChromaDB similarity search) is typically the cheap part of
the request (tens of milliseconds for a KB this size); LLM generation dominates total
latency, which is why the two are logged separately -- that split is the first place to
look when optimizing.

**Known limitations** (reasonable for a 3-4 hour scope, worth calling out honestly):
- Chunking is a plain character sliding window, not sentence/semantic-aware.
- The fallback "web search" is a mock, not a real search API call.
- The distance threshold is a single global constant, not tuned per query type.
- No authentication on the API itself (out of scope for the brief, but note it here for the record).
