from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler

app = APIRouter()
chat_handler = ChatAgentHandler(user_id=None)


class Message(BaseModel):
    text: str


@app.post("/chat_streaming")
async def chat_streaming(message: Message):
    return StreamingResponse(
        chat_handler.handle_message_streaming(message=message.text),
        media_type="text/event-stream",
    )


@app.post("/chat")
async def chat(message: Message):
    response, fcc = await chat_handler.handle_message(message.text)
    return {"response": response, "fcc": fcc}


@app.post("/cleanup")
async def cleanup():
    await chat_handler.cleanup()
    return {"message": "Cleanup completed"}
