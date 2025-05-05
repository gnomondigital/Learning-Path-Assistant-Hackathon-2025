from semantic_kernel.functions import kernel_function
from backend.src.agents.profile_builder.profile_questions import PROFILE_QUESTIONS


class ProfileBuilderAgent:
    def __init__(self, questions=PROFILE_QUESTIONS):
        self.questions = questions
        self.profile = {}
        self.current_index = 0
        self.last_response = None
        self.is_finished = False

    @kernel_function(
        name="start_profile_flow",
        description="Start the profile-building process with a welcoming message and first question."
    )
    def start_profile_flow(self) -> str:
        """
        Start the profile-building process with the first question.
        """
        self.current_index = 0
        self.profile = {}
        self.last_response = None
        self.is_finished = False

        intro = "👋 Welcome! Let's build your personalized learning profile step by step.\n"
        return intro + "\n" + self._format_current_question()

    @kernel_function(
        name="continue_profile_flow",
        description="Continue the flow based on user's last answer, return next question or final profile."
    )
    def continue_profile_flow(self, user_input: str) -> str:
        """
        Process the user’s response and return the next question or final profile summary.
        """
        if self.is_finished:
            return "✅ Your profile is already complete. Type `get_final_profile` to review it."

        # Save last response
        current_question = self.questions[self.current_index]
        self.profile[current_question["key"]] = user_input.strip()
        self.last_response = user_input.strip()
        self.current_index += 1

        # If we're done
        if self.current_index >= len(self.questions):
            self.is_finished = True
            return "🎉 All questions completed! Type `get_final_profile` to see your results."

        # Otherwise, ask next question with context
        return self._build_contextual_prompt()

    @kernel_function(
        name="get_final_profile",
        description="Return the structured summary of the user's answers."
    )
    def get_final_profile(self) -> dict:
        """
        Return the completed profile dictionary.
        """
        return self.profile

    def _format_current_question(self) -> str:
        """
        Format current question with options if they exist.
        """
        question_obj = self.questions[self.current_index]
        question = question_obj["question"]
        options = question_obj.get("options")

        if options:
            options_text = "\n".join(f"- {opt}" for opt in options)
            return f"{question}\n\n{options_text}"
        return question

    def _build_contextual_prompt(self) -> str:
        """
        Provide next question along with context from previous answer.
        """
        confirmation = f"✅ Got it! You answered: '{self.last_response}'.\n"
        transition = "Let's move to the next question:\n"
        next_question = self._format_current_question()

        return f"{confirmation}\n{transition}\n{next_question}"