"""Knowledge base routes for file upload, list, detail, delete, and retry."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.repositories.kb_repository import KbRepository
from src.services.kb_service import KbService

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])


@router.post("/upload")
async def upload_file(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File(...)],
) -> dict:
    """上传 .md 知识库文件并触发入库."""
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 4001, "message": "文件名不能为空", "data": None},
        )

    if not file.filename.lower().endswith(".md"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 4001, "message": "仅支持 .md 格式文件", "data": None},
        )

    file_content = await file.read()
    repo = KbRepository(db)
    service = KbService(repo)

    try:
        result = await service.upload_file(
            filename=file.filename,
            file_content=file_content,
            uploaded_by=current_user.id,
        )
        return {"code": 200, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 4001, "message": str(e), "data": None},
        ) from e


@router.get("/files")
async def list_files(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """获取知识库文件列表."""
    repo = KbRepository(db)
    service = KbService(repo)
    result = await service.list_files(page=page, page_size=page_size)
    return {"code": 200, "message": "success", "data": result}


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
) -> dict:
    """获取知识库文件详情."""
    repo = KbRepository(db)
    service = KbService(repo)
    result = await service.get_file(file_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "文件不存在", "data": None},
        )

    return {"code": 200, "message": "success", "data": result}


@router.get("/files/{file_id}/chunks/{chunk_index}")
async def get_file_chunk(
    file_id: int,
    chunk_index: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
) -> dict:
    """获取知识库切块原文（用于引用「查看原文」）."""
    repo = KbRepository(db)
    service = KbService(repo)
    result = await service.get_chunk(file_id, chunk_index)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "切块不存在", "data": None},
        )

    return {"code": 200, "message": "success", "data": result}


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
) -> dict:
    """删除知识库文件及四库索引数据."""
    repo = KbRepository(db)
    service = KbService(repo)
    success = await service.delete_file(file_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": "文件不存在", "data": None},
        )

    return {"code": 200, "message": "success", "data": None}


@router.post("/files/{file_id}/retry")
async def retry_file(
    file_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
) -> dict:
    """入库失败后重试."""
    repo = KbRepository(db)
    service = KbService(repo)

    try:
        result = await service.retry_file(file_id)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 404, "message": "文件不存在", "data": None},
            )

        return {"code": 200, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 4002, "message": str(e), "data": None},
        ) from e
