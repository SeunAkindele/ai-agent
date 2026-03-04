from __future__ import annotations

import json
from typing import Any, Dict, List

import asyncpg


def to_pgvector_literal(values: List[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in values) + "]"


class PgVectorStore:
    def __init__(self, pool: asyncpg.Pool, vector_dimension: int) -> None:
        self.pool = pool
        self.vector_dimension = vector_dimension

    async def upsert_chunk(
        self,
        chunk_id: str,
        document_id: str,
        tenant_id: str | None,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        if len(embedding) != self.vector_dimension:
            raise ValueError(
                f"Document embedding dimension mismatch. expected={self.vector_dimension}, got={len(embedding)}"
            )

        vector_literal = to_pgvector_literal(embedding)

        sql = """
            INSERT INTO document_chunks (
                id,
                document_id,
                tenant_id,
                chunk_index,
                content,
                embedding,
                metadata
            )
            VALUES (
                $1::uuid,
                $2::uuid,
                $3::uuid,
                $4,
                $5,
                $6::vector,
                $7::jsonb
            )
            ON CONFLICT (id)
            DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
                chunk_index = EXCLUDED.chunk_index
        """
        await self.pool.execute(
            sql,
            chunk_id,
            document_id,
            tenant_id,
            chunk_index,
            content,
            vector_literal,
            json.dumps(metadata or {}),
        )