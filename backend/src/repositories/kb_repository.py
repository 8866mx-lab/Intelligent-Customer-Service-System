"""Knowledge base repository for database access."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import KbFile, KbFileStatus, KbKeyword, KbMetadata, KbQA, KbVector


class KbRepository:
    """Knowledge base repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_file(
        self,
        filename: str,
        file_path: str,
        uploaded_by: int,
    ) -> KbFile:
        """创建知识库文件记录."""
        kb_file = KbFile(
            filename=filename,
            file_path=file_path,
            uploaded_by=uploaded_by,
            status="processing",
        )
        self.db.add(kb_file)
        await self.db.flush()
        await self.db.refresh(kb_file)
        return kb_file

    async def get_file_by_id(self, file_id: int) -> KbFile | None:
        """根据 ID 获取文件."""
        result = await self.db.execute(select(KbFile).where(KbFile.id == file_id))
        return result.scalar_one_or_none()

    async def get_vector_chunk(self, file_id: int, chunk_index: int) -> KbVector | None:
        """根据文件 ID 与切块序号获取向量切块."""
        result = await self.db.execute(
            select(KbVector).where(
                KbVector.file_id == file_id,
                KbVector.chunk_index == chunk_index,
            )
        )
        return result.scalar_one_or_none()

    async def list_files(self, page: int = 1, page_size: int = 20) -> tuple[list[KbFile], int]:
        """获取文件列表（分页）."""
        # Get total count
        count_result = await self.db.execute(select(KbFile))
        total = len(count_result.scalars().all())

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(KbFile).order_by(KbFile.created_at.desc()).offset(offset).limit(page_size)
        )
        files = result.scalars().all()

        return list(files), total

    async def update_file_status(
        self,
        file_id: int,
        status: str,
        chunk_count: int | None = None,
        qa_count: int | None = None,
        error_message: str | None = None,
    ) -> KbFile | None:
        """更新文件状态."""
        kb_file = await self.get_file_by_id(file_id)
        if kb_file is None:
            return None

        kb_file.status = KbFileStatus(status)
        if chunk_count is not None:
            kb_file.chunk_count = chunk_count
        if qa_count is not None:
            kb_file.qa_count = qa_count
        if error_message is not None:
            kb_file.error_message = error_message

        await self.db.flush()
        await self.db.refresh(kb_file)
        return kb_file

    async def delete_file(self, file_id: int) -> bool:
        """删除文件及相关索引数据."""
        kb_file = await self.get_file_by_id(file_id)
        if kb_file is None:
            return False

        # 删除四库数据（外键 CASCADE 会自动删除）
        await self.db.delete(kb_file)
        await self.db.flush()
        return True

    async def add_vector(
        self,
        file_id: int,
        chunk_index: int,
        content: str,
        embedding: bytes,
        metadata: dict | None = None,
    ) -> KbVector:
        """添加向量记录."""
        vector = KbVector(
            file_id=file_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            meta_data=metadata,
        )
        self.db.add(vector)
        await self.db.flush()
        return vector

    async def add_keyword(
        self,
        file_id: int,
        chunk_index: int,
        content: str,
    ) -> KbKeyword:
        """添加关键词记录."""
        keyword = KbKeyword(
            file_id=file_id,
            chunk_index=chunk_index,
            content=content,
        )
        self.db.add(keyword)
        await self.db.flush()
        return keyword

    async def add_metadata(
        self,
        file_id: int,
        chunk_index: int,
        source_file: str,
        chunk_position: int,
        char_count: int,
    ) -> KbMetadata:
        """添加元数据记录."""
        meta = KbMetadata(
            file_id=file_id,
            chunk_index=chunk_index,
            source_file=source_file,
            chunk_position=chunk_position,
            char_count=char_count,
        )
        self.db.add(meta)
        await self.db.flush()
        return meta

    async def add_qa(
        self,
        file_id: int,
        question: str,
        answer: str,
        q_embedding: bytes,
    ) -> KbQA:
        """添加 QA 记录."""
        qa = KbQA(
            file_id=file_id,
            question=question,
            answer=answer,
            q_embedding=q_embedding,
        )
        self.db.add(qa)
        await self.db.flush()
        return qa

    async def delete_vectors(self, file_id: int) -> None:
        """删除文件的所有向量记录."""
        await self.db.execute(delete(KbVector).where(KbVector.file_id == file_id))
        await self.db.flush()

    async def delete_keywords(self, file_id: int) -> None:
        """删除文件的所有关键词记录."""
        await self.db.execute(delete(KbKeyword).where(KbKeyword.file_id == file_id))
        await self.db.flush()

    async def delete_metadata(self, file_id: int) -> None:
        """删除文件的所有元数据记录."""
        await self.db.execute(delete(KbMetadata).where(KbMetadata.file_id == file_id))
        await self.db.flush()

    async def delete_qa(self, file_id: int) -> None:
        """删除文件的所有 QA 记录."""
        await self.db.execute(delete(KbQA).where(KbQA.file_id == file_id))
        await self.db.flush()
