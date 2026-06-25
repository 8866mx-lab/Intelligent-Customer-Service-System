"""RAG pipeline for retrieval-augmented generation."""

import asyncio
import json
import struct
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.core import get_logger
from src.core.config import settings
from src.db.models import KbFile, KbKeyword, KbQA, KbVector

logger = get_logger()

EMBEDDING_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
)
MAX_HTTP_RETRIES = 3
QA_MATCH_THRESHOLD = 0.8
RRF_K = 60
# 向量相似度分档：<0.75 未命中；[0.75,0.85) 相似问题；>=0.85 高置信直答
VECTOR_SIMILARITY_MIN = 0.75
VECTOR_SIMILARITY_HIGH = 0.85


def _format_error(exc: BaseException) -> str:
    """Format exception for logs."""
    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return f"{type(exc).__name__}: 外部服务调用失败，请检查网络或 DashScope API 配置"


class RagPipeline:
    """RAG pipeline for retrieval-augmented generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(
        self,
        query: str,
        user_id: int,
        short_term_memory: list[dict],
        long_term_memory: dict,
    ) -> dict:
        """执行完整的 RAG 链路.

        Args:
            query: 用户输入
            user_id: 用户 ID
            short_term_memory: 短期记忆（最近 3 轮对话）
            long_term_memory: 长期记忆（用户画像）

        Returns:
            response_type: qa_match | clarify | rag | mock
            content: 回复内容
            citations: 引用来源（仅 rag 模式）
            intent: 意图识别结果
        """
        try:
            # Step 1: Query 改写
            rewritten_query = await self._rewrite_query(query, short_term_memory)
            logger.info("Query rewritten", original=query, rewritten=rewritten_query)

            # Step 2: QA 直答（阈值 0.8）
            qa_match = await self._qa_direct_match(rewritten_query)
            if qa_match:
                logger.info("QA direct match found", question=qa_match["question"])
                return {
                    "response_type": "qa_match",
                    "content": qa_match["answer"],
                    "citations": [],
                    "intent": "clear_query",
                }

            # Step 3: 意图识别
            intent_result = await self._identify_intent(rewritten_query, short_term_memory)
            logger.info("Intent identified", intent=intent_result.get("intent"))

            if intent_result.get("intent") == "vague_query":
                clarify_text = intent_result.get("clarification", "请提供更多细节。")
                return {
                    "response_type": "clarify",
                    "content": clarify_text,
                    "citations": [],
                    "intent": "vague_query",
                }

            # Step 4: 槽位填充（结合长短期记忆改写 Query）
            filled_query = await self._fill_slots(
                rewritten_query, short_term_memory, long_term_memory
            )
            logger.info("Query filled with memory", filled=filled_query)

            # Step 5: 向量相似度分档（以 Top1 向量相似度为准）
            vector_results = await self._vector_search(filled_query, top_k=20)
            if not vector_results:
                return self._no_knowledge_response(intent_result)

            best_vector_sim = float(vector_results[0]["similarity"])
            if best_vector_sim < VECTOR_SIMILARITY_MIN:
                return self._no_knowledge_response(intent_result)

            match_label = (
                "相似问题" if best_vector_sim < VECTOR_SIMILARITY_HIGH else None
            )

            # Step 6: RRF 混合检索 + Rerank + 生成回答
            retrieved_chunks = await self._hybrid_retrieval(
                filled_query, top_k=20, vector_results=vector_results
            )
            if not retrieved_chunks:
                return self._no_knowledge_response(intent_result)

            reranked_chunks = await self._rerank(filled_query, retrieved_chunks, top_k=5)
            self._attach_vector_similarity(vector_results, reranked_chunks)
            answer, citations = await self._generate_answer(filled_query, reranked_chunks)

            return {
                "response_type": "rag",
                "content": answer,
                "citations": citations,
                "intent": intent_result.get("intent", "clear_query"),
                "match_label": match_label,
                "vector_similarity": best_vector_sim,
            }

        except Exception as e:
            logger.error("RAG pipeline failed", error=_format_error(e))
            return {
                "response_type": "mock",
                "content": "抱歉，系统暂时无法处理您的请求，请稍后再试。",
                "citations": [],
                "intent": "error",
            }

    async def _rewrite_query(self, query: str, memory: list[dict]) -> str:
        """Query 改写（LLM）."""
        context = "\n".join([f"{m['role']}: {m['content']}" for m in memory[-4:]])
        prompt = f"""根据对话上下文，将用户最新问题改写为更清晰、完整的问题。

对话上下文：
{context}

用户问题：{query}

改写后的问题（只输出问题本身，不要解释）："""

        url = f"{settings.llm_base_url}/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }

        data = await self._post_json_with_retry(url, payload)
        rewritten = data["choices"][0]["message"]["content"].strip()
        return rewritten if rewritten else query

    async def _qa_direct_match(self, query: str) -> dict | None:
        """QA 库直答（向量相似度 ≥ 0.8）."""
        q_embedding_bytes = await self._get_embedding(query, text_type="query")
        q_vector = struct.unpack(f"{len(q_embedding_bytes) // 4}f", q_embedding_bytes)

        result = await self.db.execute(select(KbQA))
        qa_list = result.scalars().all()

        best_similarity = 0.0
        best_qa = None

        for qa in qa_list:
            qa_vector = struct.unpack(f"{len(qa.q_embedding) // 4}f", qa.q_embedding)
            similarity = self._cosine_similarity(q_vector, qa_vector)
            if similarity > best_similarity:
                best_similarity = similarity
                best_qa = qa

        if best_similarity >= QA_MATCH_THRESHOLD and best_qa is not None:
            return {
                "question": best_qa.question,
                "answer": best_qa.answer,
                "similarity": best_similarity,
            }

        return None

    async def _identify_intent(self, query: str, memory: list[dict]) -> dict:
        """意图识别（LLM 返回 JSON）."""
        context = "\n".join([f"{m['role']}: {m['content']}" for m in memory[-2:]])
        prompt = f"""分析用户问题的意图，判断是否包含足够信息来检索知识库。

对话上下文：
{context}

用户问题：{query}

如果问题意图清晰、信息充足，返回：{{"intent": "clear_query"}}
如果问题模糊、信息不足（如"怎么办"、"有什么"等），返回：{{"intent": "vague_query", "clarification": "请问您具体想了解..."}}

输出（JSON 格式）："""

        url = f"{settings.llm_base_url}/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }

        data = await self._post_json_with_retry(url, payload)
        content = data["choices"][0]["message"]["content"]

        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                intent: dict = json.loads(content[start:end])
                return intent
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse intent JSON")

        return {"intent": "clear_query"}

    async def _fill_slots(
        self, query: str, short_term: list[dict], long_term: dict
    ) -> str:
        """槽位填充（结合长短期记忆）."""
        department = long_term.get("department")
        topics = long_term.get("common_topics", {})
        recent_context = "\n".join([f"{m['role']}: {m['content']}" for m in short_term[-2:]])

        prompt_parts = [f"用户问题：{query}"]
        if department:
            prompt_parts.append(f"用户部门：{department}")
        if topics:
            top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]
            prompt_parts.append(f"常问话题：{', '.join([t[0] for t in top_topics])}")
        if recent_context:
            prompt_parts.append(f"最近对话：\n{recent_context}")

        filled = " | ".join(prompt_parts)
        return filled

    @staticmethod
    def _no_knowledge_response(intent_result: dict) -> dict:
        """未命中知识库时的统一回复."""
        return {
            "response_type": "rag",
            "content": "抱歉，我未能找到相关知识。建议您转接人工客服获取帮助。",
            "citations": [],
            "intent": intent_result.get("intent", "clear_query"),
            "match_label": None,
            "vector_similarity": None,
        }

    async def _hybrid_retrieval(
        self,
        query: str,
        top_k: int = 20,
        *,
        vector_results: list[dict] | None = None,
    ) -> list[dict]:
        """RRF 混合检索（向量 + 关键词）."""
        if vector_results is None:
            vector_results = await self._vector_search(query, top_k=top_k)
        keyword_results = await self._keyword_search(query, top_k=top_k)

        if not vector_results and not keyword_results:
            return []

        # RRF 按 (file_id, chunk_index) 融合，避免向量表/关键词表主键冲突
        rrf_scores: dict[tuple[int, int], float] = {}

        for rank, item in enumerate(vector_results, start=1):
            key = (item["file_id"], item["chunk_index"])
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (RRF_K + rank)

        for rank, item in enumerate(keyword_results, start=1):
            key = (item["file_id"], item["chunk_index"])
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (RRF_K + rank)

        all_chunks = {
            (item["file_id"], item["chunk_index"]): item
            for item in vector_results + keyword_results
        }
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        return [all_chunks[key] for key in sorted_keys[:top_k]]

    async def _vector_search(self, query: str, top_k: int) -> list[dict]:
        """向量检索."""
        q_embedding_bytes = await self._get_embedding(query, text_type="query")
        q_vector = struct.unpack(f"{len(q_embedding_bytes) // 4}f", q_embedding_bytes)

        result = await self.db.execute(select(KbVector))
        vectors = result.scalars().all()

        scored = []
        for vec in vectors:
            vec_embedding = struct.unpack(f"{len(vec.embedding) // 4}f", vec.embedding)
            similarity = self._cosine_similarity(q_vector, vec_embedding)
            scored.append(
                {
                    "id": vec.id,
                    "file_id": vec.file_id,
                    "chunk_index": vec.chunk_index,
                    "content": vec.content,
                    "similarity": similarity,
                    "source": "vector",
                }
            )

        scored.sort(key=lambda x: float(x["similarity"]), reverse=True)  # type: ignore[arg-type]
        return scored[:top_k]

    async def _keyword_search(self, query: str, top_k: int) -> list[dict]:
        """关键词检索（简单文本匹配）."""
        keywords = query.split()
        if not keywords:
            return []

        result = await self.db.execute(select(KbKeyword))
        kws = result.scalars().all()

        scored = []
        for kw in kws:
            score = sum(1 for k in keywords if k in kw.content)
            if score > 0:
                scored.append(
                    {
                        "id": kw.id,
                        "file_id": kw.file_id,
                        "chunk_index": kw.chunk_index,
                        "content": kw.content,
                        "similarity": score / len(keywords),
                        "source": "keyword",
                    }
                )

        scored.sort(key=lambda x: float(x["similarity"]), reverse=True)  # type: ignore[arg-type]
        return scored[:top_k]

    async def _rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        """重排（百炼 Rerank API），失败时降级返回原顺序."""
        if not chunks:
            return []

        try:
            url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
            payload = {
                "model": settings.rerank_model,
                "input": {
                    "query": query,
                    "documents": [c["content"] for c in chunks],
                },
            }

            data = await self._post_json_with_retry(url, payload)
            results = data.get("output", {}).get("results", [])

            if results:
                reranked = []
                for item in results[:top_k]:
                    index = item.get("index", 0)
                    if index < len(chunks):
                        chunk = chunks[index].copy()
                        chunk["rerank_score"] = item.get("relevance_score", 0.0)
                        reranked.append(chunk)
                return reranked

        except Exception as e:
            logger.warning("Rerank failed, using original order", error=_format_error(e))

        return chunks[:top_k]

    async def _generate_answer(self, query: str, chunks: list[dict]) -> tuple[str, list[dict]]:
        """生成回答（LLM）并提取引用来源."""
        context = "\n\n---\n\n".join(
            [f"[文档{i+1}] {c['content']}" for i, c in enumerate(chunks)]
        )

        prompt = f"""根据以下知识库片段回答用户问题。
如果知识库中没有相关信息，请明确告知用户并建议转人工。

知识库内容：
{context}

用户问题：{query}

请用简洁、友好的语言回答："""

        url = f"{settings.llm_base_url}/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        data = await self._post_json_with_retry(url, payload)
        answer = data["choices"][0]["message"]["content"].strip()

        citations = []
        for chunk in chunks[:3]:
            filename = await self._resolve_filename(chunk["file_id"])
            content = chunk["content"]
            preview = content if len(content) <= 120 else f"{content[:120]}..."
            citations.append(
                {
                    "file_id": chunk["file_id"],
                    "filename": filename,
                    "chunk_index": chunk["chunk_index"],
                    "preview": preview,
                    "similarity": chunk.get(
                        "vector_similarity", chunk.get("similarity", 0.0)
                    ),
                }
            )

        return answer, citations

    @staticmethod
    def _attach_vector_similarity(
        vector_results: list[dict], chunks: list[dict]
    ) -> None:
        """为切块附加向量相似度（用于引用展示）."""
        sim_map = {
            (item["file_id"], item["chunk_index"]): float(item["similarity"])
            for item in vector_results
        }
        for chunk in chunks:
            key = (chunk["file_id"], chunk["chunk_index"])
            chunk["vector_similarity"] = sim_map.get(key, 0.0)

    async def _resolve_filename(self, file_id: int) -> str:
        """解析知识库文件名."""
        result = await self.db.execute(select(KbFile).where(KbFile.id == file_id))
        kb_file = result.scalar_one_or_none()
        return kb_file.filename if kb_file is not None else f"知识库文档 {file_id}"

    async def _get_embedding(self, text: str, *, text_type: str = "document") -> bytes:
        """单条文本 Embedding."""
        payload = {
            "model": settings.embedding_model,
            "input": {"texts": [text]},
            "parameters": {"text_type": text_type},
        }
        data = await self._post_json_with_retry(EMBEDDING_URL, payload)
        embeddings = data.get("output", {}).get("embeddings", [])
        if not embeddings:
            raise ValueError("Embedding API 返回为空")

        vector = embeddings[0]["embedding"]
        return struct.pack(f"{len(vector)}f", *vector)

    async def _post_json_with_retry(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON with retry."""
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
                    return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPStatusError as exc:
                last_error = exc
                # 4xx（除 429）不可重试，避免 rerank 403 等拖慢响应
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

    async def suggest_agent_replies(
        self,
        *,
        messages: list[dict],
        user_id: int,
        long_term_memory: dict | None = None,
    ) -> list[dict[str, str | int]]:
        """基于对话上下文与 RAG，生成 3 条坐席回复候选."""
        short_term = [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-6:]
            if m.get("role") in ("user", "assistant", "agent")
        ]

        last_user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and str(msg.get("content", "")).strip():
                last_user_query = str(msg["content"]).strip()
                break
        if not last_user_query:
            last_user_query = "请根据对话上下文为坐席生成回复建议"

        rag_result = await self.run(
            query=last_user_query,
            user_id=user_id,
            short_term_memory=short_term,
            long_term_memory=long_term_memory or {},
        )

        history_text = "\n".join(
            f"[{m.get('role', '')}] {m.get('content', '')}" for m in messages[-10:]
        )
        prompt = f"""你是企业智能客服系统的坐席助手。根据对话历史和知识库参考，生成 3 条不同侧重点的坐席人工回复候选。
要求：专业、友好、简洁；3 条互不重复；可直接发送给员工。

对话历史：
{history_text}

知识库参考（RAG）：
{rag_result.get("content", "")}

仅输出 JSON 数组：
[{{"content": "候选1"}}, {{"content": "候选2"}}, {{"content": "候选3"}}]"""

        try:
            url = f"{settings.llm_base_url}/chat/completions"
            payload = {
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
            data = await self._post_json_with_retry(url, payload)
            content_str = data["choices"][0]["message"]["content"]
            start = content_str.find("[")
            end = content_str.rfind("]") + 1
            if start >= 0 and end > start:
                parsed = json.loads(content_str[start:end])
                if isinstance(parsed, list):
                    suggestions: list[dict[str, str | int]] = []
                    for i, item in enumerate(parsed[:3]):
                        if isinstance(item, dict) and item.get("content"):
                            suggestions.append(
                                {"index": i + 1, "content": str(item["content"]).strip()}
                            )
                    if len(suggestions) >= 3:
                        return suggestions[:3]
        except Exception as e:
            logger.warning("Suggest replies parse failed", error=_format_error(e))

        base = rag_result.get("content", "您好，我来协助您处理这个问题。")
        return [
            {"index": 1, "content": base},
            {
                "index": 2,
                "content": f"{base} 如需进一步协助，请补充具体报错信息或截图。",
            },
            {
                "index": 3,
                "content": "如问题仍未解决，我可以为您转接相关同事或记录工单跟进。",
            },
        ]

    @staticmethod
    def _cosine_similarity(vec1: tuple[float, ...], vec2: tuple[float, ...]) -> float:
        """余弦相似度."""
        if len(vec1) != len(vec2):
            return 0.0

        dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return float(dot / (norm1 * norm2))
