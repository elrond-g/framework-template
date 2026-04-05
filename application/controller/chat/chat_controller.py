"""Chat controller: only calls ChatService, never domain/manager layers directly."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from library.base.api_response import ApiResponse
from library.models.base import get_db
from library.services.chat_service import ChatService

from .chat_vo import (
    ChatRequest,
    ConversationVO,
    CreateConversationRequest,
    MessageVO,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _get_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.post("/conversations", response_model=ApiResponse[ConversationVO])
def create_conversation(
    req: CreateConversationRequest = CreateConversationRequest(),
    service: ChatService = Depends(_get_service),
):
    data = service.create_conversation(title=req.title)
    return ApiResponse.success(data=data)


@router.get("/conversations", response_model=ApiResponse[list[ConversationVO]])
def list_conversations(service: ChatService = Depends(_get_service)):
    data = service.list_conversations()
    return ApiResponse.success(data=data)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[list[MessageVO]],
)
def get_messages(
    conversation_id: str,
    service: ChatService = Depends(_get_service),
):
    data = service.get_conversation_messages(conversation_id)
    return ApiResponse.success(data=data)


@router.delete("/conversations/{conversation_id}", response_model=ApiResponse)
def delete_conversation(
    conversation_id: str,
    service: ChatService = Depends(_get_service),
):
    service.delete_conversation(conversation_id)
    return ApiResponse.success(message="Conversation deleted")


@router.post(
    "/conversations/{conversation_id}/chat",
    response_model=ApiResponse[MessageVO],
)
async def chat(
    conversation_id: str,
    req: ChatRequest,
    service: ChatService = Depends(_get_service),
):
    data = await service.chat(conversation_id, req.message)
    return ApiResponse.success(data=data)
