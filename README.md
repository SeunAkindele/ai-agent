# AI Agent

A microservices-based AI platform providing RAG (Retrieval-Augmented Generation), document ingestion, media processing (audio transcription, image description/OCR), and card generation. The gateway API exposes a unified interface and delegates to backend services.

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
        │  Sidecars: cpp-audio, cpp-search│
        └───────────────────────────────┘
```

- **Gateway API** — Single entry point; routes chat, health, media, and upload; calls cards, ingest, media, and RAG clients.
- **RAG Service** — Modular RAG: query (parse, rewrite), retrieval (vector + hybrid), rerank, context (assemble, compress), generation (answer, citations), measure (latency, retrieval/answer metrics), refine (retry, strategy). Exposes `POST /rag/ask`.
- **Ingest Service** — Document pipeline: loaders (PDF, CSV, URL, image, audio), chunking, embeddings, upsert to doc/file/vector stores.
- **Media Service** — Audio (preprocess, transcribe) and vision (image description, OCR); file store.
- **Cards Service** — Card generation and validation; cards store.
- **Shared** — Python package `ai_shared`: core (config, errors), schemas (cards, chunk, document, rag), utils (ids, text).
- **Sidecars** — C++ components: **cpp-audio** (normalize, resample, silence trim, WAV reader), **cpp-search** (BM25, index, tokenizer).

## Repository layout

| Path | Description |
|------|-------------|
| `services/gateway-api/` | FastAPI gateway; routes and clients for downstream services |
| `services/rag-service/` | RAG API and pipeline (query → retrieve → rerank → context → generate → measure/refine) |
| `services/ingest-service/` | Ingest API and pipeline (load → chunk → embed → upsert) |
| `services/media-service/` | Media API; audio transcription and vision (describe, OCR) |
| `services/cards-service/` | Cards API; generate and validate |
| `shared/python/ai_shared/` | Shared Python library (schemas, core, utils) |
| `sidecars/cpp-audio/` | C++ audio preprocessing (normalize, resample, silence trim, WAV) |
| `sidecars/cpp-search/` | C++ BM25/search (index, tokenizer) |
| `docs/openapi/` | OpenAPI specs: `gateway`, `rag`, `ingest`, `media`, `cards` |
| `infra/` | Docker Compose and dev scripts |

## Requirements

- Python 3.x (see each service’s `requirements.txt`)
- Docker (for running services and sidecars)
- CMake (for building C++ sidecars)

## Quick start

1. **Environment**  
   Copy `.env.example` to `.env` and set any required variables (the repo only ignores `.env`; no example is committed).

2. **Run with Docker**  
   From the repo root:
   ```bash
   cd infra
   docker-compose up -d
   ```
   Use `infra/scripts/dev.sh` if you have a local dev workflow defined there.

3. **Run a single service (e.g. RAG)**  
   ```bash
   cd services/rag-service
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
   Then call `POST /rag/ask` with a JSON body: `{"question": "What is RAG?"}`.

4. **Shared Python library**  
   Install in editable mode for local development:
   ```bash
   pip install -e shared/
   ```

5. **C++ sidecars**  
   Build from each sidecar directory:
   ```bash
   cd sidecars/cpp-audio && mkdir build && cd build && cmake .. && make
   cd sidecars/cpp-search && mkdir build && cd build && cmake .. && make
   ```

## API overview

| Service | Purpose |
|---------|---------|
| **Gateway** | Chat, health, media, upload endpoints; proxies to backend services |
| **RAG** | `POST /rag/ask` — question in, RAG-generated answer out |
| **Ingest** | Document ingestion and indexing pipeline |
| **Media** | Audio transcription and image description/OCR |
| **Cards** | Card generation and validation |

OpenAPI definitions are under `docs/openapi/` (`gateway.openapi.json`, `rag.openapi.json`, etc.).

## Development

- Each service has its own `requirements.txt` and `Dockerfile`.
- Shared types and utilities live in `shared/python/ai_shared`; use them from services to keep contracts consistent.
- RAG pipeline modules live under `services/rag-service/app/rag/modules/` (query, retrieval, rerank, context, generation, measure, refine).
- Ingest pipeline: loaders in `app/pipeline/loaders/`, chunking, embeddings, and upsert in `app/pipeline/`.

## License

See repository license file if present.
