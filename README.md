# AI Agent

Microservices-based AI platform fronted by a single conversational endpoint. Users send natural-language messages to one API; an intent-based tool router selects the right backend capability — RAG question-answering, media description, card generation — and returns a unified response. Backend services expose their functionality as MCP (Model Context Protocol) tools over Streamable HTTP, so the gateway communicates over MCP rather than bespoke HTTP contracts.

## Architecture

```
        User
         │
         ▼
  POST /v1/agent/ask
         │
    ┌────▼─────────────────┐
    │   Gateway API         │
    │   (tool router)       │
    │                       │
    │   intent ──► tool     │
    │                       │
    │   MCPServiceClient    │
    │   (Streamable HTTP)   │
    └───┬───────┬───────┬───┘
        │       │       │
   ┌────▼──┐ ┌─▼────┐ ┌▼───────┐
   │ RAG   │ │Media │ │Cards   │
   │ ask   │ │describe│ │generate│
   └───────┘ └──────┘ └────────┘
   FastMCP   FastMCP   FastMCP
   /mcp      /mcp      /mcp
```

1. The user sends a message to `POST /v1/agent/ask`.
2. The **tool router** inspects the message and decides which tool to invoke (`rag`, `media`, `cards`, `ingest`, or `none`).
3. The gateway calls the chosen backend service over MCP Streamable HTTP and returns a unified `AgentAskResponse`.

## MCP transport

Each backend service runs a **FastMCP** server mounted at `/mcp` inside a standard FastAPI app. The gateway holds a persistent `MCPServiceClient` session per service that:

- Opens a Streamable HTTP connection at startup
- Serializes tool calls through a single `ClientSession` (with async lock)
- Auto-reconnects once on failure before raising
- Sends `Origin` and `Bearer` headers for MCP security

This means services are reachable over plain HTTP in both local dev and Docker Compose — no stdio transport required.

## MCP security

MCP endpoints are protected with two layers:

| Layer | Header | Purpose |
|-------|--------|---------|
| Origin validation | `Origin` | Only allows requests from configured origins (default: `http://gateway-api.internal`) |
| Bearer token | `Authorization: Bearer <token>` | Internal service-to-service auth (default dev token: `dev-internal-token`) |

Configure via env vars `ALLOWED_MCP_ORIGINS` and `INTERNAL_MCP_TOKEN` on each MCP service.

## How the tool router works

The router lives in `services/gateway-api/app/core/tool_router.py`. It uses simple keyword/pattern rules to classify intent:

| Intent | Triggers | Tool |
|--------|----------|------|
| Image/audio description | `"describe this image"`, media attachment flag | `media` |
| Flashcards / quiz | `"make flashcards"`, `"quiz me"` | `cards` |
| Document ingestion | `"upload"`, `"ingest"`, `"add to knowledge base"` | `ingest` |
| Knowledge Q&A | Contains `?`, starts with question word | `rag` |
| Fallback | Everything else | `rag` |

Set the env var `FORCE_TOOL=rag` (or `media`, `cards`) to bypass classification during development.

## Request / Response

**Request** — `POST /v1/agent/ask`

```json
{
  "message": "What is Retrieval-Augmented Generation?",
  "has_media": false,
  "meta": {}
}
```

**Response**

```json
{
  "tool_used": "rag",
  "answer": "RAG is a technique that …",
  "sources": [{"document": "policy.pdf", "page": 4, "score": 0.92}],
  "latency_ms": 312,
  "trace_id": "a1b2c3d4e5f6"
}
```

`tool_used` tells the caller which backend answered. `sources` and `latency_ms` are populated when the RAG tool is selected; other tools return their own relevant fields as they are implemented.

## Repository layout

```
ai-agent/
├── services/
│   ├── gateway-api/              # FastAPI gateway — single /v1/agent/ask endpoint
│   │   ├── app/
│   │   │   ├── api/v1/
│   │   │   │   ├── routes_chat.py      # POST /v1/agent/ask handler
│   │   │   │   └── routes_health.py    # Health check endpoint
│   │   │   ├── clients/
│   │   │   │   ├── mcp_service_client.py  # Generic MCP Streamable HTTP client
│   │   │   │   ├── rag_client.py          # RAG service wrapper
│   │   │   │   ├── media_client.py        # Media service wrapper
│   │   │   │   ├── cards_client.py        # Cards service wrapper
│   │   │   │   └── ingest_client.py       # Ingest service wrapper
│   │   │   └── core/
│   │   │       ├── config.py           # Env-based configuration
│   │   │       ├── tool_router.py      # Intent classifier → tool name
│   │   │       ├── auth.py             # Authentication utilities
│   │   │       └── logging.py          # Logging setup
│   │   ├── docs/                       # API documentation (OpenAPI)
│   │   └── requirements.txt
│   │
│   ├── rag-service/              # RAG pipeline + MCP server
│   │   ├── app/
│   │   │   ├── api/v1/routes_rag.py    # Optional HTTP compatibility endpoint
│   │   │   ├── mcp/
│   │   │   │   ├── server.py           # FastMCP server setup
│   │   │   │   └── tools/rag.py        # MCP tool: ask(question) → dict
│   │   │   ├── rag/
│   │   │   │   ├── container.py        # Pipeline singleton and runner
│   │   │   │   ├── pipeline.py         # Core RAG pipeline (parse → retrieve → generate)
│   │   │   │   └── modules/            # Pipeline stages
│   │   │   │       ├── query/          # parse, rewrite
│   │   │   │       ├── retrieval/      # vector_search, hybrid_search, filters
│   │   │   │       ├── rerank/         # score_reranker, llm_reranker
│   │   │   │       ├── context/        # assemble, compress
│   │   │   │       ├── generation/     # answer, citations
│   │   │   │       ├── measure/        # answer_metrics, retrieval_metrics, latency
│   │   │   │       └── refine/         # retry, strategy
│   │   │   ├── repositories/           # doc_store, vector_store
│   │   │   ├── schemas/                # rag_request, rag_response, metrics
│   │   │   └── core/                   # config, logging
│   │   └── requirements.txt
│   │
│   ├── media-service/            # Audio transcription + image description/OCR
│   │   ├── app/
│   │   │   ├── api/v1/routes_media.py
│   │   │   ├── audio/                  # preprocess, transcribe
│   │   │   ├── vision/                 # describe_image, ocr
│   │   │   └── repositories/           # file_store
│   │   └── requirements.txt
│   │
│   ├── cards-service/            # Card generation and validation
│   │   ├── app/
│   │   │   ├── api/v1/routes_cards.py
│   │   │   ├── cards/                  # generate, validate
│   │   │   └── repositories/           # cards_store
│   │   └── requirements.txt
│   │
│   └── ingest-service/           # Document ingestion pipeline
│       ├── app/
│       │   ├── api/v1/routes_ingest.py
│       │   ├── pipeline/
│       │   │   ├── loaders/            # pdf, csv, image, audio, url
│       │   │   ├── chunking/           # chunk_text
│       │   │   ├── embeddings/         # embedder
│       │   │   └── upsert.py
│       │   ├── models/                 # chunk, document
│       │   └── repositories/           # doc_store, file_store, vector_store
│       └── requirements.txt
│
├── shared/python/ai_shared/      # Shared Python library
│   ├── core/                     # config, errors
│   ├── schemas/                  # rag, cards, chunk, document
│   └── utils/                    # ids, text
│
├── sidecars/
│   ├── cpp-audio/                # C++ audio preprocessing (normalize, resample, silence trim)
│   └── cpp-search/               # C++ BM25/search (index, tokenizer)
│
├── docs/openapi/                 # OpenAPI specs for all services
└── infra/                        # Docker Compose and dev scripts
```

## Requirements

- Python 3.11+
- Docker (compose stack + sidecars)
- `mcp[cli]` and `fastmcp` Python packages (included in each service's `requirements.txt`)
- CMake (only if building the C++ sidecars)

## Quick start

1. **Environment** — copy `.env.example` to `.env` (if provided), or create one with at least:

   ```
   RAG_MCP_URL=http://127.0.0.1:8001/mcp
   INTERNAL_MCP_TOKEN=dev-internal-token
   INTERNAL_MCP_ORIGIN=http://gateway-api.internal
   ```

2. **Install dependencies**

   ```bash
   pip install -r services/gateway-api/requirements.txt
   pip install -r services/rag-service/requirements.txt
   ```

3. **Start the RAG service** (serves both MCP and HTTP)

   ```bash
   cd services/rag-service
   uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

   This exposes the `ask` MCP tool at `http://127.0.0.1:8001/mcp` and an optional HTTP endpoint at `POST /ask`.

4. **Start the gateway**

   ```bash
   cd services/gateway-api
   uvicorn app.main:app --reload --port 8000
   ```

   On startup the gateway opens a persistent MCP session to the RAG service and logs the discovered tools.

5. **Ask a question**

   ```bash
   curl -X POST http://localhost:8000/v1/agent/ask \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Retrieval-Augmented Generation?"}'
   ```

6. **Run everything with Docker** (alternative)

   ```bash
   cd infra
   docker-compose up -d
   ```

## Current tool status

| Tool | Status | Backend service |
|------|--------|-----------------|
| `rag.ask` | Implemented (MCP + HTTP) | `services/rag-service` |
| `media.describe` | Placeholder — routed but not yet wired | `services/media-service` |
| `cards.generate` | Placeholder — routed but not yet wired | `services/cards-service` |
| `ingest` | Placeholder — routed but not yet wired | `services/ingest-service` |

The gateway returns a descriptive message when a placeholder tool is selected, so the single-endpoint contract is already stable.

## Adding a new tool

1. Create a FastMCP server in the target service (see `services/rag-service/app/mcp/server.py` for reference).
2. Register MCP tool functions and mount the MCP app at `/mcp` in the service's FastAPI app.
3. Add a client in `services/gateway-api/app/clients/` that wraps `MCPServiceClient` for the new service.
4. Initialize the client in the gateway's `lifespan` (see `services/gateway-api/app/main.py`).
5. Wire the client into `routes_chat.py` under the matching `tool ==` branch.
6. (Optional) Add new trigger keywords to `tool_router.py`.

## Development

- Each service owns its own `requirements.txt` and `Dockerfile`.
- Shared types live in `shared/python/ai_shared/` — import them to keep contracts aligned across services.
- The RAG pipeline modules live under `services/rag-service/app/rag/modules/` (query, retrieval, rerank, context, generation, measure, refine).
- OpenAPI specs for each service are stored in `docs/openapi/`.

## License

See the repository's license file if present.
