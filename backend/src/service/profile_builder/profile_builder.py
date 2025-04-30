
from semantic_kernel.functions import kernel_function

from backend.src.service.profile_builder.profile_questions import \
    PROFILE_QUESTIONS


class ProfileBuilderAgent():
    def __init__(self, questions=PROFILE_QUESTIONS):
        """
        Initialize the ProfileBuilderTool with the necessary instructions and questions.

        :param prompt_text: The instructions or guidelines to provide context to the model.
        :param questions: List of questions (defaults to the imported PROFILE_QUESTIONS).
        """
        self.questions = questions
        self.profile = {}

    @kernel_function(
        description="Format a question with context and options for the user.",
        name="ask_question"
    )
    def ask_question(self, question_obj):
        """
        Method to format and present a question to the user, returning the response.

        :param question_obj: Dictionary with question and options.
        :return: User's answer (either selected or entered).
        """
        question = question_obj['question']
        options = "\n".join(question_obj['options'])

        # Construct a full prompt
        prompt = f"{question}\n\n{options}"
        return prompt

    @kernel_function(
        description="Collect structured responses from the user.",
        name="collect_responses"
    )
    def collect_responses(self, user_responses):
        """
        Process user responses and build a structured profile.

        :param user_responses: Dictionary with the user responses.
        :return: The final user profile as a dictionary.
        """
        for question in self.questions:
            answer = user_responses.get(question['key'])
            if answer:
                self.profile[question['key']] = answer
            else:
                # or handle as incomplete if required
                self.profile[question['key']] = None

        return self.profile

    @kernel_function(
        description="Execute the profile builder and return a completed profile.",
        name="execute"
    )
    async def execute(self, user_responses):
        """
        Main execution method that calls the profile-building process.

        :param user_responses: Dictionary of user responses (answers to the questions).
        :return: Structured profile.
        """
        # Collect responses and build profile
        return self.collect_responses(user_responses)
