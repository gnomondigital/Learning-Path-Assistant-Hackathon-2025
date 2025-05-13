import hashlib
import json
import os
import sys

import chainlit as cl

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../", "backend/", "src/")
)

import logging

from backend.src.main import SemanticKernelAgentHandler

logging.basicConfig(level=logging.DEBUG)

config = {
    "AZURE_API_KEY": os.getenv("AZURE_AI_INFERENCE_API_KEY"),
    "DEPLOYMENT_NAME": os.getenv("API_DEPLOYMENT_NAME"),
    "AZURE_ENDPOINT": os.getenv("AZURE_AI_INFERENCE_ENDPOINT"),
    "PROMPT": "You are GD Academy's AI assistant. Answer questions or delegate to other agents.",
}


def load_users_from_file() -> list:
    logging.debug("Loading users from file")
    with open("frontend/users.json", "r") as f:
        users = json.load(f)
    logging.debug(f"Loaded users")
    return users


def verify_password(stored_hash: str, password: str) -> bool:
    logging.debug(f"Verifying password for hash")
    result = stored_hash == hashlib.md5(password.encode()).hexdigest()
    return result


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    logging.debug(f"Authenticating user: {username}")
    users = load_users_from_file()
    for user in users:
        if user["username"] == username and verify_password(
            user["password_hash"], password
        ):
            user_id = f"{username}_{user['password_hash']}"
            logging.info(f"User authenticated successfully: {username}")
            global agent_handler
            agent_handler = SemanticKernelAgentHandler(user_id=user_id)
            return cl.User(
                identifier=username,
                metadata={"role": "user", "provider": "credentials"},
            )
    logging.warning(f"Authentication failed for user: {username}")
    return None


@cl.on_chat_start
async def on_chat_start() -> None:
    logging.debug("Chat session started.")
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


@cl.on_message
async def on_message(message: cl.Message) -> None:
    logging.debug(f"Received message: {message.content}")
    try:
        thinking = await cl.Message("Thinking...", author="agent").send()
        logging.debug("Sent 'Thinking...' message to user.")
        response = await agent_handler.process_message(
            user_message=message.content
        )
        logging.debug(f"Response from agent handler: {response}")

        response_text = getattr(
            response,
            "content",
            "Sorry, I couldn't understand the response format.",
        )

        with open("frontend/profiles.json", "r") as f:
            profile_data = json.load(f)
        logging.debug(f"Loaded profile data: {profile_data}")

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
                logging.debug(
                    f"Profile summary content: {profile_summary_content}"
                )
            else:
                profile_summary_content = (
                    "No profile found for the current user."
                )
                logging.debug("No profile found for the current user.")
        else:
            profile_summary_content = "No profiles available."
            logging.debug("No profiles available in the data.")

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
    logging.debug("Chat session ended.")
    await cl.Message(content="Goodbye!").send()
    await agent_handler.clean_up_thread()
    logging.debug("Cleaned up agent handler thread.")
