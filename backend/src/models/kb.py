"""Knowledge base request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KbStores(BaseModel):
    """四库入库状态."""

    vector: str
    keyword: str
    metadata: str
    qa: str


class KbFileUploadResponse(BaseModel):
    """上传文件响应."""

    id: int
    filename: str
    status: str
    created_at: datetime


class KbFileListItem(BaseModel):
    """知识库文件列表项."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    chunk_count: int | None
    qa_count: int | None
    stores: KbStores
    uploaded_by: int
    created_at: datetime
    updated_at: datetime


class KbFileDetail(BaseModel):
    """知识库文件详情."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    chunk_count: int | None
    qa_count: int | None
    stores: KbStores
    error_message: str | None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime


class KbFileRetryResponse(BaseModel):
    """重试入库响应."""

    id: int
    filename: str
    status: str
    updated_at: datetime
