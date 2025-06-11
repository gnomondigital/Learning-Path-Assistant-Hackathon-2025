import hashlib
import json
import logging

import chainlit as cl

from frontend.apis.routes import chat

logging.basicConfig(level=logging.INFO)


def load_users_from_file() -> list:
    logging.info("Loading users from file")
    with open("../../data/users.json", "r") as f:
        users = json.load(f)
    logging.info("Loaded users")
    return users


def verify_password(stored_hash: str, password: str) -> bool:
    logging.info("Verifying password for hash")
    result = stored_hash == hashlib.md5(password.encode()).hexdigest()
    return result


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    logging.info(f"Authenticating user: {username}")
    users = load_users_from_file()
    for user in users:
        if user["username"] == username and verify_password(
            user["password_hash"], password
        ):
            logging.info(f"User authenticated successfully: {username}")
            return cl.User(
                identifier=username,
                metadata={"role": "user", "provider": "credentials"},
            )
    logging.warning(f"Authentication failed for user: {username}")
    return None


@cl.on_chat_resume
async def on_chat_resume(thread):
    pass


@cl.step(type="tool", show_input=True)
async def tool():
    await cl.sleep(2)
    return cl.user_session.get("fcc")


@cl.on_chat_start
async def on_chat_start() -> None:
    logging.info("Chat session started.")
    cl.user_session.set("fcc", "")


@cl.on_message
async def main(message: cl.Message):
    logging.info(f"Received message: {message.content}")
    thinking = await cl.Message("Thinking...", author="agent").send()
    logging.info("Sent 'Thinking...' message to user.")
    logging.info(f"Received message: {message.content}")

    response = chat(message.content)
    logging.info(f"fcc : {response.get("fcc")}")
    fcc = response.get("fcc")
    cl.user_session.set("fcc", fcc)
    response_text = response.get(
        "response", "Sorry, No response from agent handler.")

    thinking.content = response_text
    await thinking.update()
    tool_res = await tool()

    await cl.Message(content=tool_res).send()
