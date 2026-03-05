from __future__ import annotations

import json
from typing import Any, Dict, List

import asyncpg

from app.domain.models.rag_models import RAGSource


def to_pgvector_literal(values: List[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in values) + "]"


class PgVectorStore:
    def __init__(self, pool: asyncpg.Pool, vector_dimension: int) -> None:
        self.pool = pool
        self.vector_dimension = vector_dimension

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        tenant_id: str | None = None,
    ) -> List[RAGSource]:
        if len(query_embedding) != self.vector_dimension:
            raise ValueError(
                f"Query embedding dimension mismatch. expected={self.vector_dimension}, got={len(query_embedding)}"
            )

        vector_literal = to_pgvector_literal(query_embedding)

        if tenant_id:
            sql = """
                SELECT
                    c.id::text AS chunk_id,
                    c.document_id::text AS document_id,
                    d.title AS title,
                    c.content AS snippet,
                    1 - (c.embedding <=> $1::vector) AS score,
                    c.metadata AS chunk_metadata
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.tenant_id = $2::uuid
                ORDER BY c.embedding <=> $1::vector
                LIMIT $3
            """
            rows = await self.pool.fetch(sql, vector_literal, tenant_id, top_k)
        else:
            sql = """
                SELECT
                    c.id::text AS chunk_id,
                    c.document_id::text AS document_id,
                    d.title AS title,
                    c.content AS snippet,
                    1 - (c.embedding <=> $1::vector) AS score,
                    c.metadata AS chunk_metadata
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY c.embedding <=> $1::vector
                LIMIT $2
            """
            rows = await self.pool.fetch(sql, vector_literal, top_k)

        result: List[RAGSource] = []
        for row in rows:
            metadata_raw = row["chunk_metadata"]
            metadata: Dict[str, Any]
            if isinstance(metadata_raw, str):
                metadata = json.loads(metadata_raw)
            else:
                metadata = dict(metadata_raw or {})

            result.append(
                RAGSource(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    title=row["title"],
                    snippet=row["snippet"],
                    score=float(row["score"]),
                    metadata=metadata,
                )
            )

        return result

   