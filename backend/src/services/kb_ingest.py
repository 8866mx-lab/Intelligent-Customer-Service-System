"""Knowledge base ingestion service for async document processing."""

import asyncio
import json
import struct
from pathlib import Path
from typing import Any

import httpx

from pycore.core import get_logger
from src.core.config import settings
from src.repositories.kb_repository import KbRepository

logger = get_logger()

EMBEDDING_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
)
# DashScope text-embedding-v3 同步接口：字符串列表单次最多 10 条
EMBEDDING_BATCH_SIZE = 10
MAX_HTTP_RETRIES = 3


def _format_error(exc: BaseException) -> str:
    """Format exception for logs and API error_message."""
    if isinstance(exc, httpx.HTTPStatusError):
        body = exc.response.text.strip()
        if body:
            return f"{type(exc).__name__}: {body[:800]}"
    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return f"{type(exc).__name__}: 外部服务调用失败，请检查网络或 DashScope API 配置"


class KbIngestService:
    """知识库入库服务，处理切块、Embedding、QA抽取."""

    def __init__(self, repo: KbRepository):
        self.repo = repo

    async def ingest_file(self, file_id: int, file_path: str, filename: str) -> None:
        """异步入库流程：切块 → 四库顺序入库."""
        try:
            logger.info("Starting ingest", file_id=file_id, filename=filename)

            content = Path(file_path).read_text(encoding="utf-8")
            chunks = self._split_chunks(content)
            logger.info("Chunks created", file_id=file_id, chunk_count=len(chunks))

            await self._ingest_keyword_store(file_id, chunks)
            await self._ingest_metadata_store(file_id, chunks, filename)
            await self._ingest_vector_store(file_id, chunks)
            qa_count = await self._ingest_qa_store(file_id, content)

            await self.repo.update_file_status(
                file_id=file_id,
                status="completed",
                chunk_count=len(chunks),
                qa_count=qa_count,
            )

            logger.info("Ingest completed", file_id=file_id, qa_count=qa_count)

        except Exception as e:
            error_message = _format_error(e)
            logger.error("Ingest failed", file_id=file_id, error=error_message)
            await self.repo.update_file_status(
                file_id=file_id,
                status="failed",
                error_message=error_message,
            )

    def _split_chunks(self, content: str, chunk_size: int = 512) -> list[str]:
        """按段落切块，并限制单块最大字符数（避免超长段落触发 Embedding 400）."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current_chunk = ""

        for para in paragraphs:
            for piece in self._split_text_by_size(para, chunk_size):
                if current_chunk and len(current_chunk) + len(piece) + 2 > chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = piece
                elif current_chunk:
                    current_chunk += "\n\n" + piece
                else:
                    current_chunk = piece

        if current_chunk:
            chunks.append(current_chunk)

        return [c for c in chunks if c.strip()]

    @staticmethod
    def _split_text_by_size(text: str, chunk_size: int) -> list[str]:
        """将超长文本按固定字符窗口切分."""
        if len(text) <= chunk_size:
            return [text]

        pieces: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            pieces.append(text[start:end])
            start = end
        return pieces

    async def _ingest_vector_store(self, file_id: int, chunks: list[str]) -> None:
        """向量库入库（批量 Embedding，减少 API 调用次数）."""
        logger.info("Vector store ingest start", file_id=file_id)
        if not chunks:
            logger.info("Vector store ingest skipped (no chunks)", file_id=file_id)
            return

        embeddings = await self._get_embeddings_batch(chunks)
        for i, (chunk, embedding_bytes) in enumerate(zip(chunks, embeddings, strict=True)):
            await self.repo.add_vector(
                file_id=file_id,
                chunk_index=i,
                content=chunk,
                embedding=embedding_bytes,
                metadata={"chunk_length": len(chunk)},
            )

        logger.info("Vector store ingest done", file_id=file_id)

    async def _ingest_keyword_store(self, file_id: int, chunks: list[str]) -> None:
        """关键词库入库."""
        logger.info("Keyword store ingest start", file_id=file_id)

        for i, chunk in enumerate(chunks):
            await self.repo.add_keyword(
                file_id=file_id,
                chunk_index=i,
                content=chunk,
            )

        logger.info("Keyword store ingest done", file_id=file_id)

    async def _ingest_metadata_store(
        self, file_id: int, chunks: list[str], filename: str
    ) -> None:
        """元数据库入库."""
        logger.info("Metadata store ingest start", file_id=file_id)

        for i, chunk in enumerate(chunks):
            await self.repo.add_metadata(
                file_id=file_id,
                chunk_index=i,
                source_file=filename,
                chunk_position=i,
                char_count=len(chunk),
            )

        logger.info("Metadata store ingest done", file_id=file_id)

    async def _ingest_qa_store(self, file_id: int, content: str) -> int:
        """QA 库入库，使用 LLM 抽取 QA 对."""
        logger.info("QA store ingest start", file_id=file_id)

        qa_pairs = await self._extract_qa_pairs(content)
        if not qa_pairs:
            logger.info("QA store ingest done (no pairs)", file_id=file_id, qa_count=0)
            return 0

        questions = [str(qa["question"]) for qa in qa_pairs]
        q_embeddings = await self._get_embeddings_batch(questions, text_type="query")

        for qa, q_embedding in zip(qa_pairs, q_embeddings, strict=True):
            await self.repo.add_qa(
                file_id=file_id,
                question=str(qa["question"]),
                answer=str(qa["answer"]),
                q_embedding=q_embedding,
            )

        logger.info("QA store ingest done", file_id=file_id, qa_count=len(qa_pairs))
        return len(qa_pairs)

    async def _get_embeddings_batch(
        self, texts: list[str], *, text_type: str = "document"
    ) -> list[bytes]:
        """批量调用 DashScope Embedding API."""
        if not texts:
            return []

        results: list[bytes] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[start : start + EMBEDDING_BATCH_SIZE]
            payload = {
                "model": settings.embedding_model,
                "input": {"texts": batch},
                "parameters": {
                    "text_type": text_type,
                    "dimension": 1024,
                },
            }
            data = await self._post_json_with_retry(EMBEDDING_URL, payload)
            embeddings = data.get("output", {}).get("embeddings", [])
            if len(embeddings) != len(batch):
                raise ValueError(
                    f"Embedding API 返回数量不匹配：期望 {len(batch)}，实际 {len(embeddings)}"
                )

            for item in embeddings:
                vector = item["embedding"]
                results.append(struct.pack(f"{len(vector)}f", *vector))

        return results

    async def _post_json_with_retry(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON with retry for transient network failures."""
        headers = {
            "Authorization": f"Bearer {settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }
        last_error: BaseException | None = None

        for attempt in range(1, MAX_HTTP_RETRIES + 1):
            try:
                async with httpx.AsyncClient(trust_env=False, timeout=60.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code != 429 and exc.response.status_code < 500:
                    raise
                logger.warning(
                    "HTTP request failed",
                    url=url,
                    attempt=attempt,
                    error=_format_error(exc),
                )
                if attempt < MAX_HTTP_RETRIES:
                    await asyncio.sleep(attempt)
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "HTTP request failed",
                    url=url,
                    attempt=attempt,
                    error=_format_error(exc),
                )
                if attempt < MAX_HTTP_RETRIES:
                    await asyncio.sleep(attempt)

        assert last_error is not None
        raise last_error

    async def _extract_qa_pairs(self, content: str) -> list[dict[str, str]]:
        """使用 LLM 从内容中抽取 QA 对."""
        prompt = f"""请从以下文档中抽取 1-3 个有价值的问答对（QA）。
每个问答对应该是文档中明确回答的问题。

文档内容：
{content[:1000]}

输出格式（JSON 数组）：
[{{"question": "问题1", "answer": "答案1"}}, ...]
"""

        url = f"{settings.llm_base_url}/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }

        data = await self._post_json_with_retry(url, payload)
        content_str = data["choices"][0]["message"]["content"]

        try:
            start = content_str.find("[")
            end = content_str.rfind("]") + 1
            if start >= 0 and end > start:
                qa_pairs = json.loads(content_str[start:end])
                if not isinstance(qa_pairs, list):
                    return []

                normalized: list[dict[str, str]] = []
                for item in qa_pairs:
                    if not isinstance(item, dict):
                        continue
                    question = item.get("question")
                    answer = item.get("answer")
                    if question and answer:
                        normalized.append(
                            {"question": str(question), "answer": str(answer)}
                        )
                return normalized
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            logger.warning("Failed to parse QA pairs from LLM response")

        return []
