import os
import sys

import chainlit as cl

sys.path.append(os.path.join(os.path.dirname(__file__), "../", "backend/", "src/"))

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
    # cl.user_session.set("user_id", cl.user_session)
    await cl.Message(content="Hi! I'm your GD assistant. Ask me anything.").send()


@cl.on_chat_end
async def on_chat_end():
    await cl.Message(content="Goodbye!").send()
    agent_handler.clean_up_thread()
    # cl.user_session.clear()


@cl.on_message
async def on_message(message: cl.Message):
    # user_id = cl.user_session.get("user_id")
    try:
        thinking = await cl.Message("Thinking...", author="agent").send()

        response = await agent_handler.process_message(user_message=message.content)

        if hasattr(response, "content"):
            response_text = str(response.content)
        else:
            response_text = "Sorry, I couldn't understand the response format."

        # Set the response content in the thinking message
        thinking.content = response_text
        await thinking.update()

    except Exception as e:
        await cl.Message(f"Error: {e}").send()
