from fastapi import APIRouter
from pydantic import BaseModel

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler

app = APIRouter()
chat_handler = ChatAgentHandler()


class Message(BaseModel):
    text: str


@app.post("/chat")
async def chat(message: Message):
    response = await chat_handler.handle_message(message.text)
    return {"response": response}


@app.post("/cleanup")
async def cleanup():
    await chat_handler.cleanup()
    return {"message": "Cleanup completed"}
