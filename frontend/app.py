import hashlib
import json
import os
import sys

import chainlit as cl

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../", "backend/", "src/")
)

from backend.src.main import SemanticKernelAgentHandler

config = {
    "AZURE_API_KEY": os.getenv("AZURE_AI_INFERENCE_API_KEY"),
    "DEPLOYMENT_NAME": os.getenv("API_DEPLOYMENT_NAME"),
    "AZURE_ENDPOINT": os.getenv("AZURE_AI_INFERENCE_ENDPOINT"),
    "PROMPT": "You are GD Academy's AI assistant. Answer questions or delegate to other agents.",
}

agent_handler = SemanticKernelAgentHandler()


# Function to read user data from a file
def load_users_from_file():
    with open("frontend/users.json", "r") as f:
        return json.load(f)


# Function to hash the password and compare it to the stored hash
def verify_password(stored_hash, password):
    return stored_hash == hashlib.md5(password.encode()).hexdigest()


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Load users from the file
    users = load_users_from_file()

    # Iterate through the users and verify the username and password
    for user in users:
        if user["username"] == username and verify_password(
            user["password_hash"], password
        ):
            return cl.User(
                identifier=username,
                metadata={"role": "user", "provider": "credentials"},
            )

    # If no match is found, return None to indicate authentication failure
    return None


@cl.on_chat_start
async def on_chat_start():
    elements = [
        cl.Text(
            content="Sorry, I couldn't find your profile.",
            name="profile_summary",
        ),
    ]

    # Setting elements will open the sidebar
    await cl.ElementSidebar.set_elements(elements)
    await cl.Message(
        content="Hi! I'm your GD assistant. Ask me anything."
    ).send()


@cl.on_chat_end
async def on_chat_end():
    await cl.Message(content="Goodbye!").send()
    agent_handler.clean_up_thread()
    # cl.user_session.clear()


@cl.on_message
async def on_message(message: cl.Message):
    try:
        thinking = await cl.Message("Thinking...", author="agent").send()
        response = await agent_handler.process_message(
            user_message=message.content
        )

        show_profile = await agent_handler.process_message(
            user_message="show_profile"
        )

        print(f"Response from agent: {response}")
        print(f"Show profile response: {show_profile}")

        response_text = getattr(
            response,
            "content",
            "Sorry, I couldn't understand the response format.",
        )

        if hasattr(show_profile, "content") and show_profile.content:
            response_text_show_profile = str(show_profile.content)
        else:
            response_text_show_profile = "Sorry, I couldn't find your profile."
        await cl.ElementSidebar.set_elements(
            [cl.Text(content=response_text_show_profile, name="profile_summary")]
        )
        await cl.ElementSidebar.set_title("Your Profile Summary")
        print(f"Response from agent: {response_text}")
        print(f"Show profile response: {response_text_show_profile}")
        await cl.sleep(2)

        await cl.ElementSidebar.set_elements([])

        # Step 7: Update main response
        thinking.content = response_text
        await thinking.update()

    except Exception as e:
        await cl.Message(f"Error: {e}").send()
        print(f"Exception encountered: {e}")
