import logging

import chainlit as cl

from frontend.apis.routes import chat, chat_streaming


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
    # Fake tool
    await cl.sleep(2)
    return "Response from the tool!"


@cl.on_message
async def main(message: cl.Message):
    logging.info(f"Received message: {message.content}")
    thinking = await cl.Message("Thinking...", author="agent").send()
    logging.info("Sent 'Thinking...' message to user.")
    logging.info(f"Received message: {message.content}")

    response = chat(message.content)

    logging.info(f"Response from agent handler: {response.get('response')}")
    response_text = response.get(
        "response", "Sorry, No response from agent handler.")

    thinking.content = response_text
    await thinking.update()
    tool_res = await tool()

    await cl.Message(content=tool_res).send()
