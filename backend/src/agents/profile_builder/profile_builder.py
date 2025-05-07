
from semantic_kernel.functions import kernel_function

from backend.src.agents.profile_builder.profile_questions import \
    PROFILE_QUESTIONS


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

        intro = "👋 Hello! I'm your Learning Path Assistant. I'll help build a personalized learning journey for you.\n"
        intro += "Let's start by getting to know a bit about you and your goals.\n"
        return intro + "\n" + self._format_current_question()

    @kernel_function(
        name="process_user_response",
        description="Process the user's response to the current question and provide the next question."
    )
    def process_user_response(self, user_input: str) -> str:
        """
        Process the user's response and return the next question.
        """
        if self.is_finished:
            return "✅ Your profile is already complete. Use 'generate_learning_path' to see your personalized plan."

        # Save last response
        current_question = self.questions[self.current_index]

        # Handle multi-select responses
        if current_question.get("input_type") == "multi_select":
            # Convert comma-separated values to a list
            self.profile[current_question["key"]] = [item.strip()
                                                     for item in user_input.split(',')]
        else:
            self.profile[current_question["key"]] = user_input.strip()

        self.last_response = user_input.strip()
        self.current_index += 1

        # If we're done
        if self.current_index >= len(self.questions):
            self.is_finished = True
            return "🎉 Great! I have all the information I need.\n\nUse 'generate_learning_path' to create your personalized learning journey based on your profile."

        # Otherwise, ask next question with context
        return self._build_contextual_prompt()

    @kernel_function(
        name="get_current_question",
        description="Get the current question without advancing the flow."
    )
    def get_current_question(self) -> str:
        """
        Return the current question without changing the state.
        """
        if self.is_finished:
            return "All questions have been answered. Use 'generate_learning_path' to see your personalized plan."

        return self._format_current_question()

    @kernel_function(
        name="skip_question",
        description="Skip the current question and move to the next one."
    )
    def skip_question(self) -> str:
        """
        Skip the current question and proceed to the next one.
        """
        if self.is_finished:
            return "✅ Your profile is already complete. Use 'generate_learning_path' to see your personalized plan."

        current_question = self.questions[self.current_index]
        self.profile[current_question["key"]] = "Skipped"
        self.last_response = "Skipped"
        self.current_index += 1

        if self.current_index >= len(self.questions):
            self.is_finished = True
            return "🎉 All questions completed! Use 'generate_learning_path' to see your personalized plan."

        return f"Question skipped. Let's move on:\n\n{self._format_current_question()}"

    @kernel_function(
        name="go_back",
        description="Go back to the previous question."
    )
    def go_back(self) -> str:
        """
        Go back to the previous question.
        """
        if self.current_index > 0:
            self.current_index -= 1
            self.is_finished = False
            return f"Let's go back to:\n\n{self._format_current_question()}"
        else:
            return "You're already at the first question."

    @kernel_function(
        name="get_profile_summary",
        description="Get a summary of the user's profile information collected so far."
    )
    def get_profile_summary(self) -> str:
        """
        Return a formatted summary of the user's answers.
        """
        if not self.profile:
            return "No profile information has been collected yet."

        summary = "📋 Your Profile Summary:\n\n"

        for i, q in enumerate(self.questions):
            key = q["key"]
            if key in self.profile:
                # Handle multi-select responses
                if isinstance(self.profile[key], list):
                    value = ", ".join(self.profile[key])
                else:
                    value = self.profile[key]

                summary += f"• {q['question']}\n   {value}\n\n"

            # Only show questions that have been answered
            if i >= self.current_index:
                break

        return summary

    @kernel_function(
        name="get_profile_data",
        description="Return the raw profile data dictionary."
    )
    def get_profile_data(self) -> dict:
        """
        Return the complete profile dictionary.
        """
        return self.profile

    @kernel_function(
        name="reset_profile",
        description="Reset the profile and start over."
    )
    def reset_profile(self) -> str:
        """
        Reset the profile and start the process again.
        """
        self.profile = {}
        self.current_index = 0
        self.last_response = None
        self.is_finished = False

        return "Profile has been reset. Let's start again:\n\n" + self._format_current_question()

    def _format_current_question(self) -> str:
        """
        Format current question based on its input type.
        """
        question_obj = self.questions[self.current_index]
        question = question_obj["question"]
        input_type = question_obj.get("input_type", "text")
        options = question_obj.get("options")
        placeholder = question_obj.get("placeholder", "")

        formatted_question = f"{question}"

        if input_type == "select" and options:
            formatted_question += "\n\nOptions:"
            for i, opt in enumerate(options):
                formatted_question += f"\n{i+1}. {opt}"

        elif input_type == "multi_select" and options:
            formatted_question += "\n\nSelect one or more (separate with commas):"
            for i, opt in enumerate(options):
                formatted_question += f"\n{i+1}. {opt}"

        if placeholder:
            formatted_question += f"\n\n(Hint: {placeholder})"

        return formatted_question

    def _build_contextual_prompt(self) -> str:
        """
        Provide next question along with context from previous answer.
        """
        confirmation = f"✅ Response saved: '{self.last_response}'.\n"

        # Show progress
        progress = f"Question {self.current_index}/{len(self.questions)}"

        next_question = self._format_current_question()

        return f"{confirmation}\n{progress}\n\n{next_question}"
