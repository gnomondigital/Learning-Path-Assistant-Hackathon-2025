import hashlib
import json
import logging
import os
import sys

import chainlit as cl


from frontend.apis.routes import chat, chat_streaming, cleanup, root


logging.basicConfig(level=logging.INFO)
config = {
    "AZURE_API_KEY": os.getenv("AZURE_AI_INFERENCE_API_KEY"),
    "DEPLOYMENT_NAME": os.getenv("API_DEPLOYMENT_NAME"),
    "AZURE_ENDPOINT": os.getenv("AZURE_AI_INFERENCE_ENDPOINT"),
    "PROMPT": "You are GD Academy's AI assistant. Answer questions or delegate to other agents.",
}


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


@cl.on_chat_resume
async def on_chat_resume(thread):
    pass


@cl.step(type="tool")
async def tool():
    await cl.sleep(2)

    # fcc_value = cl.user_session.get("fcc")
    return "Response from the tool!"


@cl.on_message
async def main(message: cl.Message):
    logging.info(f"Received message: {message.content}")
    thinking = await cl.Message("Thinking...", author="agent").send()
    logging.info("Sent 'Thinking...' message to user.")
    logging.info(f"Received message: {message.content}")

    response = chat(message.content)

    logging.info(f"Response from agent handler: {response.get('response')}")
    response_text = response.get("response", "Sorry, No response from agent handler.")

    thinking.content = response_text
    await thinking.update()
    tool_res = await tool()

    await cl.Message(content=tool_res).send()
