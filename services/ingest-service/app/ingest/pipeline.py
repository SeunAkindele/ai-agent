# ingest_pipeline.py

from app.ingest.modules.loaders.loader import Loader
from app.ingest.modules.chunking.chunk_text import Chunker
from app.ingest.modules.embeddings.embedder import EmbeddingModel
from app.infrastructure.db.vector_store import PgVectorStore
from app.infrastructure.db.postgres import PostgresManager
from app.core.config import Config

class IngestPipeline:
    def __init__(self, config: Config):
        self.config = config
        self.loader = Loader()  # Multiple loaders handled here
        self.chunker = Chunker()
        self.embedding_model = EmbeddingModel()
        self.db_manager = PostgresManager(config.POSTGRES_DSN)
        self.vector_store = PgVectorStore(self.db_manager.get_pool(), vector_dimension=self.config.PGVECTOR_DIMENSION)

    async def run(self, source: str, data_type: str) -> None:
        """Run the ingest pipeline: load, chunk, embed, store."""
        # Load data based on its type
        raw_data = self.loader.load_data(source, data_type)

        # Process each chunk (in practice, this might be done in parallel or in batches)
        for text in raw_data:
            # Chunk the text (apply only for text-based data)
            chunks = self.chunker.chunk_text(text) if isinstance(text, str) else [text]
            
            # Embed the chunks
            embeddings = [self.embedding_model.embed(chunk) for chunk in chunks]
            
            # Save each chunk with its embedding to the database
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"chunk_{idx}"
                document_id = "sample_document_id"
                tenant_id = None
                chunk_index = idx
                metadata = {"source": source}
                
                # Save to vector store (database)
                await self.vector_store.upsert_chunk(chunk_id, document_id, tenant_id, chunk_index, chunk, embedding, metadata)

        print(f"Successfully processed and stored {len(raw_data)} data items.")

# To run the service
if __name__ == "__main__":
    config = Config()
    pipeline = IngestPipeline(config)
    asyncio.run(pipeline.run("sample_audio.mp3", "audio"))  # Example with audio data