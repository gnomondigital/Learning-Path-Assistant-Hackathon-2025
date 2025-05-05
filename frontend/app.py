# frontend/app.py
import os

import chainlit as cl

from backend.src.main import SemanticKernelAgentHandler

config = {
    "AZURE_API_KEY": os.getenv("AZURE_AI_INFERENCE_API_KEY"),
    "DEPLOYMENT_NAME": os.getenv("API_DEPLOYMENT_NAME"),
    "AZURE_ENDPOINT": os.getenv("AZURE_AI_INFERENCE_ENDPOINT"),
    "PROMPT": "You are GD Academy's AI assistant. Answer questions or delegate to other agents.",
}

agent_handler = SemanticKernelAgentHandler()


@cl.on_chat_start
async def on_chat_start():
    # Set a unique user_id for the session (can be based on user info)
    cl.user_session.set("user_id", cl.user_session.id)
    await cl.Message(content="Hi! I'm your assistant. Ask me anything.").send()


@cl.on_message
async def on_message(message: cl.Message):
    user_id = cl.user_session.get("user_id")
    try:
        thinking = await cl.Message("Thinking...", author="agent").send()

        # Send message to backend Semantic Kernel agent
        response = await agent_handler.send_message(user_id=user_id, message=message.content)

        thinking.content = response
        await thinking.update()
    except Exception as e:
        await cl.Message(f"Error: {e}").send()
