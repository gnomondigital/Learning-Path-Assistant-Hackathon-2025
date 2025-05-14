import hashlib
import json
import logging
import os
import sys

import chainlit as cl

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler
from frontend.apis.routes import chat, cleanup, root

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../", "backend/", "src/")
)

logging.basicConfig(level=logging.INFO)
config = {
    "AZURE_API_KEY": os.getenv("AZURE_AI_INFERENCE_API_KEY"),
    "DEPLOYMENT_NAME": os.getenv("API_DEPLOYMENT_NAME"),
    "AZURE_ENDPOINT": os.getenv("AZURE_AI_INFERENCE_ENDPOINT"),
    "PROMPT": "You are GD Academy's AI assistant. Answer questions or delegate to other agents.",
}
test = root()


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
            user_id = f"{username}_{user['password_hash']}"
            logging.info(f"User authenticated successfully: {username}")
            global agent_handler
            agent_handler = ChatAgentHandler(user_id=user_id)
            return cl.User(
                identifier=username,
                metadata={"role": "user", "provider": "credentials"},
            )
    logging.warning(f"Authentication failed for user: {username}")
    return None


@cl.step(type="tool", show_input=True)
async def tool(msg: str):
    await cl.sleep(2)

    return cl.user_session.get("fcc")


@cl.on_chat_start
async def on_chat_start() -> None:
    logging.info("Chat session started.")
    elements = [
        cl.Text(
            content="Sorry, I couldn't find your profile.",
            name="profile_summary",
        ),
    ]
    await cl.ElementSidebar.set_elements(elements)
    await cl.Message(
        content="Hi! I'm your GD assistant. Ask me anything."
    ).send()
    cl.user_session.set("fcc", "")


@cl.on_message
async def on_message(message: cl.Message) -> None:
    logging.info(f"Received message: {message.content}")
    try:
        tool_res = await tool(message.content)

        thinking = await cl.Message("Thinking...", author="agent").send()
        logging.info("Sent 'Thinking...' message to user.")
        logging.info(f"Received message: {message.content}")
        response = chat(message.content)
        print(f"fcc : {response.get("fcc")}")
        fcc = response.get("fcc")
        cl.user_session.set("fcc", fcc)
        logging.info(
            f"Response from agent handler: {response.get('response')}"
        )
        response_text = response.get(
            "response", "Sorry, No response from agent handler."
        )
        with open("data/profiles.json", "r") as f:
            profile_data = json.load(f)
        logging.info(f"Loaded profile data: {profile_data}")

        if profile_data:
            latest_profile = next(
                (
                    profile
                    for profile in profile_data
                    if profile.get("user_id") == agent_handler.user_id
                ),
                None,
            )

            if not latest_profile:
                latest_profile = profile_data[-1] if profile_data else None

            if latest_profile:
                profile_summary_content = f"""
                Name: {latest_profile.get("name", "N/A")}
                Current Domain: {latest_profile.get("current_domain", "N/A")}
                Current Position: {latest_profile.get("current_postion", "N/A")}
                Target Role: {latest_profile.get("target_role", "N/A")}
                Tech Experience Level: {latest_profile.get("tech_experience_level", "N/A")}
                Learning Obstacles: {latest_profile.get("learning_obstacles", "N/A")}
                Time Limit: {latest_profile.get("time_limit", "N/A")}
                Preferred Learning Style: {', '.join(latest_profile.get("preferred_learning_style", []))}
                Learning Resources: {', '.join(latest_profile.get("learning_resources", []))}
                Additional Info: {latest_profile.get("additional_info", "N/A")}
                """
                logging.info(
                    f"Profile summary content: {profile_summary_content}"
                )
            else:
                profile_summary_content = (
                    "No profile found for the current user."
                )
                logging.info("No profile found for the current user.")
        else:
            profile_summary_content = "No profiles available."
            logging.info("No profiles available in the data.")

        await cl.ElementSidebar.set_elements(
            [cl.Text(content=profile_summary_content, name="profile_summary")]
        )
        await cl.ElementSidebar.set_title("Your Profile Summary")
        logging.info(f"Response from agent: {response_text}")

        thinking.content = response_text
        await thinking.update()

    except Exception as e:
        logging.error(f"Exception encountered: {e}")
        await cl.Message(f"Error: {e}").send()


@cl.on_chat_end
async def on_chat_end() -> None:
    logging.info("Chat session ended.")
    await cl.Message(content="Goodbye!").send()
    cleanup()
    logging.info("Cleaned up agent handler thread.")
