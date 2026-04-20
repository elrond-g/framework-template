from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New Conversation", max_length=255)
    system_prompt: Optional[str] = Field(default=None, max_length=10000)


class UpdateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class MessageVO(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    thinking: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    thinking_duration_ms: Optional[int] = None
    total_duration_ms: Optional[int] = None


class ConversationVO(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: Optional[str] = None
    system_prompt: Optional[str] = None


class ConversationDetailVO(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[MessageVO] = []
