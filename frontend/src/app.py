import hashlib
import json
import logging
from PyPDF2 import PdfReader

import chainlit as cl
import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.apis.routes import chat

logging.basicConfig(level=logging.INFO)


def load_users_from_file() -> list:
    logging.info("Loading users from file")
    with open("data/users.json", "r") as f:
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
async def on_chat_start():
    cl.user_session.set("fcc", "")

    # Ask for PDF upload
    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="📄 Please upload a **PDF file** to begin!",
            accept=["application/pdf"],
            max_size_mb=10
        ).send()

    pdf_file = files[0]

    # ✅ Extract text from PDF
    reader = PdfReader(pdf_file.path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    cl.user_session.set("uploaded_file_content", text)

    await cl.Message(content=f"`{pdf_file.name}` uploaded. Ready to chat!").send()


@cl.on_message
async def main(message: cl.Message):
    logging.info(f"Received message: {message.content}")
    thinking = await cl.Message("Thinking...", author="agent").send()

    # Combine user message with uploaded file content
    uploaded_content = cl.user_session.get("uploaded_file_content") or ""
    combined_prompt = f"{message.content}\n\n[File Content]:\n{uploaded_content}"

    response = chat(combined_prompt)
    fcc = response.get("fcc")
    cl.user_session.set("fcc", fcc)

    response_text = response.get("response", "Sorry, no response from agent.")
    thinking.content = response_text
    await thinking.update()

    # Show FCC result
    tool_result = await tool()
    await cl.Message(content=tool_result).send()
