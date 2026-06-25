"""Knowledge base service for file management and ingestion orchestration."""

import asyncio
from pathlib import Path

from pycore.core import get_logger
from src.core.config import settings
from src.repositories.kb_repository import KbRepository
from src.services.kb_ingest import KbIngestService, _format_error

logger = get_logger()


async def _run_background_ingest(file_id: int, file_path: str, filename: str) -> None:
    """Run ingest in an independent DB session to avoid SQLite lock conflicts."""
    from src.db.session import async_session_maker

    async with async_session_maker() as session:
        try:
            repo = KbRepository(session)
            ingest = KbIngestService(repo)
            await ingest.ingest_file(file_id, file_path, filename)
            await session.commit()
        except Exception as e:
            await session.rollback()
            error_message = _format_error(e)
            logger.error("Background ingest failed", file_id=file_id, error=error_message)
            try:
                repo = KbRepository(session)
                await repo.update_file_status(
                    file_id=file_id,
                    status="failed",
                    error_message=error_message,
                )
                await session.commit()
            except Exception as persist_error:
                await session.rollback()
                logger.error(
                    "Failed to persist ingest error",
                    file_id=file_id,
                    error=_format_error(persist_error),
                )


class KbService:
    """知识库服务."""

    def __init__(self, repo: KbRepository):
        self.repo = repo

    async def upload_file(
        self,
        filename: str,
        file_content: bytes,
        uploaded_by: int,
    ) -> dict:
        """上传文件并触发异步入库."""
        # 验证文件格式
        if not filename.lower().endswith(".md"):
            raise ValueError("仅支持 .md 格式文件")

        # 保存文件到本地
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / filename
        file_path.write_bytes(file_content)

        logger.info("File saved", filename=filename, path=str(file_path))

        # 创建文件记录
        kb_file = await self.repo.create_file(
            filename=filename,
            file_path=str(file_path),
            uploaded_by=uploaded_by,
        )

        # 触发异步入库（独立 DB 会话，不阻塞当前请求）
        asyncio.create_task(
            _run_background_ingest(
                file_id=kb_file.id,
                file_path=str(file_path),
                filename=filename,
            )
        )

        return {
            "id": kb_file.id,
            "filename": kb_file.filename,
            "status": kb_file.status,
            "created_at": kb_file.created_at,
        }

    async def list_files(self, page: int = 1, page_size: int = 20) -> dict:
        """获取文件列表."""
        files, total = await self.repo.list_files(page=page, page_size=page_size)

        items = []
        for f in files:
            items.append({
                "id": f.id,
                "filename": f.filename,
                "status": f.status,
                "chunk_count": f.chunk_count,
                "qa_count": f.qa_count,
                "stores": self._get_stores_status(f),
                "error_message": f.error_message,
                "uploaded_by": f.uploaded_by,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_file(self, file_id: int) -> dict | None:
        """获取文件详情."""
        kb_file = await self.repo.get_file_by_id(file_id)
        if kb_file is None:
            return None

        return {
            "id": kb_file.id,
            "filename": kb_file.filename,
            "status": kb_file.status,
            "chunk_count": kb_file.chunk_count,
            "qa_count": kb_file.qa_count,
            "stores": self._get_stores_status(kb_file),
            "error_message": kb_file.error_message,
            "uploaded_by": kb_file.uploaded_by,
            "created_at": kb_file.created_at,
            "updated_at": kb_file.updated_at,
        }

    async def get_chunk(self, file_id: int, chunk_index: int) -> dict | None:
        """获取指定文件的切块原文."""
        kb_file = await self.repo.get_file_by_id(file_id)
        if kb_file is None:
            return None

        vector = await self.repo.get_vector_chunk(file_id, chunk_index)
        if vector is None:
            return None

        return {
            "file_id": file_id,
            "filename": kb_file.filename,
            "chunk_index": chunk_index,
            "content": vector.content,
        }

    async def delete_file(self, file_id: int) -> bool:
        """删除文件及四库索引数据."""
        kb_file = await self.repo.get_file_by_id(file_id)
        if kb_file is None:
            return False

        # 删除本地文件
        try:
            file_path = Path(kb_file.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning("Failed to delete local file", file_path=kb_file.file_path, error=str(e))

        # 删除数据库记录（外键 CASCADE 会自动删除四库数据）
        return await self.repo.delete_file(file_id)

    async def retry_file(self, file_id: int) -> dict | None:
        """重试失败的入库."""
        kb_file = await self.repo.get_file_by_id(file_id)
        if kb_file is None:
            return None

        # 只允许重试失败的文件
        if kb_file.status != "failed":
            raise ValueError("只能重试失败的文件")

        # 清空四库数据
        await self.repo.delete_vectors(file_id)
        await self.repo.delete_keywords(file_id)
        await self.repo.delete_metadata(file_id)
        await self.repo.delete_qa(file_id)

        # 重置状态为 processing
        kb_file = await self.repo.update_file_status(
            file_id=file_id,
            status="processing",
            error_message=None,
        )
        if kb_file is None:
            return None

        # 触发异步入库
        asyncio.create_task(
            _run_background_ingest(
                file_id=kb_file.id,
                file_path=kb_file.file_path,
                filename=kb_file.filename,
            )
        )

        return {
            "id": kb_file.id,
            "filename": kb_file.filename,
            "status": kb_file.status,
            "updated_at": kb_file.updated_at,
        }

    def _get_stores_status(self, kb_file) -> dict:
        """根据文件状态推断四库状态."""
        if kb_file.status == "pending":
            return {
                "vector": "pending",
                "keyword": "pending",
                "metadata": "pending",
                "qa": "pending",
            }
        elif kb_file.status == "processing":
            return {
                "vector": "processing",
                "keyword": "processing",
                "metadata": "processing",
                "qa": "processing",
            }
        elif kb_file.status == "completed":
            return {
                "vector": "completed",
                "keyword": "completed",
                "metadata": "completed",
                "qa": "completed",
            }
        else:  # failed
            return {
                "vector": "failed",
                "keyword": "failed",
                "metadata": "failed",
                "qa": "failed",
            }
