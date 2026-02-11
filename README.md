# AI Agent

Microservices-based AI platform that delivers Retrieval-Augmented Generation (RAG), document ingestion, media processing (audio transcription, image description/OCR), and card generation. The gateway API exposes a unified interface, and the RAG service now ships with a Model Context Protocol (MCP) tool so MCP-compatible clients (Claude Desktop, Cursor MCP, etc.) can call the same pipeline without going through HTTP.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Gateway API (entry point)                        │
│  /chat  /health  /media  /upload  →  auth, config, logging               │
└───────────────┬───────────────┬───────────────┬───────────────┬─────────┘
                │               │               │               │
        ┌───────▼───────┐ ┌─────▼─────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │ RAG Service   │ │ Ingest    │ │ Media       │ │ Cards       │
        │ /rag/ask      │ │ Service   │ │ Service     │ │ Service     │
        │ pipeline      │ │ loaders   │ │ transcribe  │ │ generate    │
        │ measure/refine│ │ chunk/embed│ │ vision/ocr  │ │ validate    │
        └───────────────┘ └───────────┘ └─────────────┘ └─────────────┘
                │               │
        ┌───────▼───────────────▼───────┐
        │  Shared: ai_shared (schemas,  │
        │  core, utils)                  │
        └───────────────────────────────┘
        ┌───────────────────────────────┐
        │ Sidecars: cpp-audio, cpp-search│
        └───────────────────────────────┘
```

- **Gateway API** — Routes chat, health, media, and upload to cards, ingest, media, and RAG clients.
- **RAG Service** — Modular RAG (query, retrieval, rerank, context, generation, measure/refine). Exposes `POST /rag/ask`.
- **RAG MCP Tool** — `FastMCP` server in `services/rag-service/app/mcp/server.py` exposing the same RAG pipeline as an MCP tool named `ask`.
- **Ingest Service** — Loaders (PDF, CSV, URL, image, audio), chunking, embeddings, upsert.
- **Media Service** — Audio preprocessing/transcription and vision (describe, OCR).
- **Cards Service** — Card generation and validation pipeline plus persistence.
- **Shared** — Python package `ai_shared` for configs, schemas, and utilities.
- **Sidecars** — C++ helpers: `cpp-audio` (normalize, resample, silence trim) and `cpp-search` (BM25 index/tokenizer).

## Repository layout

| Path | Description |
|------|-------------|
| `services/gateway-api/` | FastAPI gateway; routes and downstream clients |
| `services/rag-service/` | RAG API and pipeline (query → retrieve → rerank → context → generate → measure/refine) |
| `services/rag-service/app/mcp/` | MCP server exposing the RAG `ask` tool |
| `services/ingest-service/` | Ingest API and pipeline (load → chunk → embed → upsert) |
| `services/media-service/` | Media API; audio transcription and vision (describe, OCR) |
| `services/cards-service/` | Cards API; generate and validate |
| `shared/python/ai_shared/` | Shared Python library (schemas, core, utils) |
| `sidecars/cpp-audio/` | C++ audio preprocessing (normalize, resample, silence trim, WAV) |
| `sidecars/cpp-search/` | C++ BM25/search (index, tokenizer) |
| `docs/openapi/` | OpenAPI specs: `gateway`, `rag`, `ingest`, `media`, `cards` |
| `infra/` | Docker Compose and dev scripts |

## Requirements

- Python 3.x (service-specific dependencies live in each `requirements.txt`)
- Docker (compose stack + sidecars)
- CMake (build the C++ sidecars)
- MCP CLI/runtime (`pip install mcp` or `pip install -r services/rag-service/requirements.txt`)

## Quick start

1. **Environment**  
   Copy `.env.example` to `.env` and fill the variables required for your environment (only `.env` is ignored by Git).

2. **Run everything with Docker**  
   ```bash
   cd infra
   docker-compose up -d
   ```
   Use `infra/scripts/dev.sh` if your workflow automates per-service rebuilds.

3. **Run the RAG HTTP API locally**  
   ```bash
   cd services/rag-service
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
   Send `POST /rag/ask` with `{"question": "What is RAG?"}` to exercise the pipeline.

4. **Install the shared Python library in editable mode**  
   ```bash
   pip install -e shared/
   ```

5. **Build the C++ sidecars (optional unless you call them)**  
   ```bash
   cd sidecars/cpp-audio && mkdir build && cd build && cmake .. && make
   cd ../../cpp-search && mkdir build && cd build && cmake .. && make
   ```

6. **Run the RAG MCP tool**  
   ```bash
   cd services/rag-service
   pip install -r requirements.txt  # installs the `mcp` package
   mcp dev app/mcp/server.py
   ```
   `mcp dev` loads `app/mcp/server.py`, registers the `ask` tool, and serves it over stdio/WebSocket depending on the client. Point your MCP client at this script (see “MCP access” below).

## MCP access

- **Tooling surface** — The server exported from `services/rag-service/app/mcp/server.py` defines a single tool named `ask` that simply forwards to the existing `RAGPipeline`. The tool signature makes it ideal for Claude Desktop, Cursor MCP, or any MCP-compliant IDE/chat client.
- **Run directly** — Use `mcp dev app/mcp/server.py` (stdion) for local development or wrap it in `uv run mcp dev ...` if you prefer virtual environments. The working directory must stay inside `services/rag-service` so imports like `app.rag.container` resolve.
- **Register with clients** — Point MCP-aware clients at the command above. Example (Claude Desktop `claude_desktop_config.json` excerpt):
  ```json
  {
    "mcpServers": {
      "rag-service": {
        "command": "mcp",
        "args": ["dev", "/ABSOLUTE/PATH/TO/services/rag-service/app/mcp/server.py"],
        "cwd": "/ABSOLUTE/PATH/TO/services/rag-service"
      }
    }
  }
  ```
- **Available tool** — One tool today (`ask`) with signature `question: str -> str`. Extend `app/mcp/server.py` with additional `@mcp.tool()` definitions as more pipeline capabilities need to surface.

## API overview

| Surface | Purpose |
|---------|---------|
| **Gateway** | Chat, health, media, upload endpoints; proxies to backend services |
| **RAG HTTP API** | `POST /rag/ask` — question in, RAG-generated answer out |
| **RAG MCP Tool** | `ask(question: str)` — same RAG pipeline exposed over MCP |
| **Ingest** | Document ingestion and indexing pipeline |
| **Media** | Audio transcription and image description/OCR |
| **Cards** | Card generation and validation |

OpenAPI definitions sit under `docs/openapi/` (`gateway.openapi.json`, `rag.openapi.json`, etc.).

## Development

- Each service owns its own `requirements.txt` and `Dockerfile`; install only what you need.
- Shared types/utilities live in `shared/python/ai_shared`; import them from services to keep contracts aligned.
- RAG pipeline modules live under `services/rag-service/app/rag/modules/` (query, retrieval, rerank, context, generation, measure, refine) and are re-used by both the HTTP API and the MCP server via `app/rag/container.py`.
- Ingest pipeline pieces: loaders (`app/pipeline/loaders/`), chunking/embedding/upsert in `app/pipeline/`.

## License

See the repository’s license file if present.
