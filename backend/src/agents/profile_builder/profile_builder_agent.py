import json
import logging
import os

from semantic_kernel.functions import kernel_function

from backend.src.agents.profile_builder.profile_questions import \
    PROFILE_QUESTIONS

PROFILE_FILE = "data/profiles.json"
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ProfileBuilderAgent:
    def __init__(
        self, questions: list = PROFILE_QUESTIONS, user_id: str = None
    ):
        self.user_id = user_id
        self.questions = questions
        self.profiles = self._load_profiles()
        self.current_profile = {}
        self.current_index = 0
        self.last_response = None
        self.is_finished = False
        logger.debug(
            f"Initialized ProfileBuilderAgent with user_id={self.user_id}"
        )

    def _load_profiles(self) -> list:
        logger.debug("Loading profiles...")
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r") as f:
                all_profiles = json.load(f)
                logger.debug(f"Loaded profiles: {all_profiles}")
                if self.user_id:
                    filtered_profiles = [
                        profile
                        for profile in all_profiles
                        if profile.get("user_id") == self.user_id
                    ]
                    logger.debug(
                        f"Filtered profiles for user_id={self.user_id}: {filtered_profiles}"
                    )
                    return filtered_profiles
        return []

    def _save_profiles(self) -> None:
        logger.debug("Saving profiles...")
        with open(PROFILE_FILE, "r") as f:
            all_profiles = json.load(f)
        all_profiles.append({"user_id": self.user_id, **self.current_profile})

        with open(PROFILE_FILE, "w") as f:
            json.dump(all_profiles, f, indent=2)

        logger.info(f"Saved profile: {self.current_profile}")

    @kernel_function(
        name="start_profile_flow",
        description="Start the profile-building process.",
    )
    def start_profile_flow(self) -> str:
        logger.debug("Starting profile flow...")
        self.current_profile = {}
        self.current_index = 0
        self.last_response = None
        self.is_finished = False

        intro = "👋 Hello! I'm your Learning Path Assistant.\nLet's start by getting to know you."
        logger.debug("Profile flow started.")
        return intro + "\n\n" + self._format_current_question()

    @kernel_function(
        name="process_user_response", description="Process the user's answer."
    )
    def process_user_response(self, user_input: str) -> str:
        logger.debug(f"Processing user response: {user_input}")
        if self.is_finished:
            logger.debug("Profile already complete.")
            return "✅ Profile already complete. Use 'generate_learning_path' to continue."

        current_question = self.questions[self.current_index]
        key = current_question["key"]

        if current_question.get("input_type") == "multi_select":
            self.current_profile[key] = [
                item.strip() for item in user_input.split(",")
            ]
        else:
            self.current_profile[key] = user_input.strip()

        self.last_response = user_input.strip()
        logger.debug(
            f"Saved response for key '{key}': {self.current_profile[key]}"
        )
        self.current_index += 1

        if self.current_index >= len(self.questions):
            self.is_finished = True
            self.profiles.append(self.current_profile)
            self._save_profiles()
            logger.info("Profile complete.")
            return "🎉 Profile complete! Use 'generate_learning_path' to see your plan."

        return self._build_contextual_prompt()

    @kernel_function(
        name="get_current_question", description="Get the current question."
    )
    def get_current_question(self) -> str:
        logger.debug("Getting current question...")
        if self.is_finished:
            logger.debug("All questions answered.")
            return "All questions answered. Use 'generate_learning_path' to continue."
        return self._format_current_question()

    @kernel_function(
        name="skip_question", description="Skip the current question."
    )
    def skip_question(self) -> str:
        logger.debug("Skipping current question...")
        if self.is_finished:
            logger.debug("Profile already complete.")
            return "✅ Profile complete. Use 'generate_learning_path'."

        current_question = self.questions[self.current_index]
        self.current_profile[current_question["key"]] = "Skipped"
        self.last_response = "Skipped"
        logger.debug(f"Skipped question: {current_question['key']}")
        self.current_index += 1

        if self.current_index >= len(self.questions):
            self.is_finished = True
            self.profiles.append(self.current_profile)
            self._save_profiles()
            logger.info("Profile complete after skipping.")
            return "🎉 Profile complete! Use 'generate_learning_path'."

        return f"Skipped. Next:\n\n{self._format_current_question()}"

    @kernel_function(
        name="go_back", description="Go back to the previous question."
    )
    def go_back(self) -> str:
        logger.debug("Going back to the previous question...")
        if self.current_index > 0:
            self.current_index -= 1
            self.is_finished = False
            logger.debug(f"Moved back to question index: {self.current_index}")
            return f"Back to:\n\n{self._format_current_question()}"
        logger.debug("Already at the first question.")
        return "You're at the first question."

    @kernel_function(
        name="get_profile_summary",
        description="Show summary of current profile.",
    )
    def get_profile_summary(self) -> str:
        logger.debug("Getting profile summary...")
        if not self.current_profile:
            logger.debug("No profile information yet.")
            return "No info yet."

        summary = "📋 Profile Summary:\n\n"
        for i, q in enumerate(self.questions):
            key = q["key"]
            if key in self.current_profile:
                value = self.current_profile[key]
                if isinstance(value, list):
                    value = ", ".join(value)
                summary += f"• {q['question']}\n   {value}\n\n"
            if i >= self.current_index:
                break
        logger.debug(f"Profile summary: {summary}")
        return summary

    @kernel_function(
        name="get_all_profiles", description="Get all saved profiles."
    )
    def get_all_profiles(self) -> list:
        logger.debug("Getting all profiles...")
        return self.profiles

    @kernel_function(
        name="reset_profile", description="Reset current profile flow."
    )
    def reset_profile(self) -> str:
        logger.debug("Resetting profile...")
        self.current_profile = {}
        self.current_index = 0
        self.last_response = None
        self.is_finished = False
        logger.debug("Profile reset.")
        return (
            "Profile reset. Let's start:\n\n" + self._format_current_question()
        )

    def _format_current_question(self) -> str:
        q = self.questions[self.current_index]
        prompt = f"{q['question']}"

        if q.get("input_type") in ["select", "multi_select"] and q.get(
            "options"
        ):
            prompt += "\n\nOptions:"
            for i, opt in enumerate(q["options"]):
                prompt += f"\n{i + 1}. {opt}"
        if q.get("placeholder"):
            prompt += f"\n\n(Hint: {q['placeholder']})"
        logger.debug(f"Formatted current question: {prompt}")
        return prompt

    def _build_contextual_prompt(self) -> str:
        confirmation = f"✅ Saved: '{self.last_response}'"
        progress = f"Question {self.current_index + 1}/{len(self.questions)}"
        logger.debug(f"Building contextual prompt: {confirmation}, {progress}")
        return (
            f"{confirmation}\n{progress}\n\n{self._format_current_question()}"
        )
