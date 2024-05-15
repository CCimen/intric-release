import json

from tenacity import retry, stop_after_attempt, wait_random_exponential

from instorage.ai_models.embedding_models.embedding_model_adapters.base import (
    EmbeddingModelAdapter,
)
from instorage.info_blobs.file.chunk_embedding_list import ChunkEmbeddingList
from instorage.info_blobs.info_blob import InfoBlobChunk
from instorage.main.aiohttp_client import aiohttp_client
from instorage.main.config import get_settings
from instorage.main.logging import get_logger

logger = get_logger(__name__)

MULTILINGUAL_API_KEY = "9978450b-b0e5-4dd8-8eeb-a6beafddfaee"


class MultilingualE5LargeAdapter(EmbeddingModelAdapter):
    async def get_embedding_for_query(self, query: str):
        truncated_query = query[: self.model.max_input]
        query_prepended = [f"query: {truncated_query}"]

        embeddings = await self._get_embeddings(query_prepended)
        return embeddings[0]

    # Copied from text_embedding
    # TODO: Refactor this later
    def _chunk_chunks(self, chunks: list[InfoBlobChunk]):
        cum_len = 0
        prev_i = 0
        for i, chunk in enumerate(chunks):
            cum_len += len(chunk.text)

            if cum_len > self.model.max_input:
                yield chunks[prev_i:i]
                prev_i = i
                cum_len = 0

        yield chunks[prev_i:]

    async def get_embeddings(self, chunks: list[InfoBlobChunk]):
        chunk_embedding_list = ChunkEmbeddingList()
        for chunked_chunks in self._chunk_chunks(chunks):
            texts_prepended = [f"passage: {chunk.text}" for chunk in chunked_chunks]

            logger.debug(f"Embedding a chunk of {len(chunked_chunks)} chunks")

            embeddings_for_chunks = await self._get_embeddings(texts_prepended)
            chunk_embedding_list.add(chunked_chunks, embeddings_for_chunks)

        return chunk_embedding_list

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    async def _get_embeddings(self, texts: list[str]) -> list[list[float]]:

        payload = json.dumps({"texts": texts})

        url = get_settings().multilingual_e5_large_url
        headers = {
            "access-token": MULTILINGUAL_API_KEY,
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        async with aiohttp_client().post(url, data=payload, headers=headers) as resp:
            data = await resp.json()

        return data["embeddings"]