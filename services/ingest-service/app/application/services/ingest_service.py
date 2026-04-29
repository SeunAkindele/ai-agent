from app.ingest.pipeline import IngestPipeline

class IngestService:
    def __init__(self, pipeline: IngestPipeline) -> None:
        self.pipeline = pipeline

    async def ingest(self, source: str, data_type: str) -> None:
        return await self.pipeline.run(source, data_type)