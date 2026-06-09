import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    title: str
    language: str
    source_type: str
    original_filename: str
    storage_path: str
    file_hash: str
    file_size_bytes: int
    page_count: int
    processing_status: str
    is_approved: bool
    uploaded_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPageResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    extracted_text: str
    has_text: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeleteDocumentResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str