# AI Agent

Microservices-based AI platform fronted by a single conversational endpoint. Users send natural-language messages to one API; an intent-based tool router selects the right backend capability — RAG question-answering, media description, card generation — and returns a unified response. Backend services expose their functionality as MCP (Model Context Protocol) tools, so the gateway communicates over MCP rather than bespoke HTTP contracts.

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
    └───┬───────┬───────┬───┘
        │       │       │
   ┌────▼──┐ ┌─▼────┐ ┌▼───────┐
   │ RAG   │ │Media │ │Cards   │
   │ ask   │ │describe│ │generate│
   └───────┘ └──────┘ └────────┘
     (MCP)    (MCP)     (MCP)
```

1. The user sends a message to `POST /v1/agent/ask`.
2. The **tool router** inspects the message and decides which tool to invoke (`rag`, `media`, `cards`, or `none`).
3. The gateway calls the chosen backend service over MCP and returns a unified `AgentAskResponse`.

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
  "sources": [{"title": "Doc A", "page": 4, "snippet": "…"}],
  "latency_ms": 312,
  "trace_id": "a1b2c3d4e5f6"
}
```

`tool_used` tells the caller which backend answered. `sources` and `latency_ms` are populated when the RAG tool is selected; other tools return their own relevant fields as they are implemented.

## Repository layout

| Path | Description |
|------|-------------|
| `services/gateway-api/` | FastAPI gateway — single `/v1/agent/ask` endpoint, tool router, MCP clients |
| `services/gateway-api/app/core/tool_router.py` | Intent classifier that maps a user message to a tool name |
| `services/gateway-api/app/clients/rag_client.py` | MCP client that connects to the RAG service and calls the `ask` tool |
| `services/rag-service/` | RAG pipeline service (query, retrieve, rerank, context, generate, measure/refine) |
| `services/rag-service/app/mcp/` | FastMCP server and tool registration |
| `services/rag-service/app/mcp/tools/rag.py` | MCP tool implementation — `ask(question) -> dict` |
| `services/rag-service/app/rag/pipeline.py` | Core RAG pipeline (parse → retrieve → generate) |
| `services/media-service/` | Audio transcription and image description/OCR (MCP tool: `describe`) |
| `services/cards-service/` | Card generation and validation (MCP tool: `generate`) |
| `services/ingest-service/` | Document ingestion pipeline (load → chunk → embed → upsert) |
| `shared/python/ai_shared/` | Shared Python library (schemas, core, utils) |
| `sidecars/cpp-audio/` | C++ audio preprocessing (normalize, resample, silence trim) |
| `sidecars/cpp-search/` | C++ BM25/search (index, tokenizer) |
| `infra/` | Docker Compose and dev scripts |

## Requirements

- Python 3.11+
- Docker (compose stack + sidecars)
- `mcp` and `fastmcp` Python packages (included in each service's `requirements.txt`)
- CMake (only if building the C++ sidecars)

## Quick start

1. **Environment** — copy `.env.example` to `.env` (if provided), or create one with at least:

   ```
   RAG_BASE_URL=http://localhost:8001
   ```

2. **Install dependencies**

   ```bash
   pip install -r services/gateway-api/requirements.txt
   pip install -r services/rag-service/requirements.txt
   ```

3. **Start the RAG MCP server**

   ```bash
   cd services/rag-service
   mcp dev app/mcp/server.py
   ```

   This registers the `ask` tool over stdio. The gateway's `RAGClient` connects to it automatically.

4. **Start the gateway**

   ```bash
   cd services/gateway-api
   uvicorn app.main:app --reload --port 8000
   ```

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
| `rag.ask` | Implemented | `services/rag-service` |
| `media.describe` | Placeholder — routed but not yet wired | `services/media-service` |
| `cards.generate` | Placeholder — routed but not yet wired | `services/cards-service` |
| `ingest` | Placeholder — routed but not yet wired | `services/ingest-service` |

The gateway returns a descriptive message when a placeholder tool is selected, so the single-endpoint contract is already stable.

## Adding a new tool

1. Create an MCP tool function in the target service (e.g. `services/media-service/app/mcp/tools/media.py`).
2. Register it in that service's `FastMCP` server.
3. Add a client in `services/gateway-api/app/clients/` that connects to the new MCP server and calls the tool.
4. Wire the client into `routes_chat.py` under the matching `tool ==` branch.
5. (Optional) Add new trigger keywords to `tool_router.py`.

## Development

- Each service owns its own `requirements.txt` and `Dockerfile`.
- Shared types live in `shared/python/ai_shared/` — import them to keep contracts aligned across services.
- The RAG pipeline modules live under `services/rag-service/app/rag/modules/` (query, retrieval, rerank, context, generation, measure, refine).

## License

See the repository's license file if present.
