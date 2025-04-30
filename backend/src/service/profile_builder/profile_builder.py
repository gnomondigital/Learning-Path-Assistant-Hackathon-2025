

class ProfileBuilderTool():
    def __init__(self, prompt_text: str, questions=None):
        """
        Initialize the ProfileBuilderTool with the necessary instructions and questions.

        :param prompt_text: The instructions or guidelines to provide context to the model.
        :param questions: List of questions (defaults to the imported PROFILE_QUESTIONS).
        """
        self.prompt_text = prompt_text
        self.questions = questions
        self.profile = {}

    def ask_question(self, question_obj):
        """
        Method to format and present a question to the user, returning the response.

        :param question_obj: Dictionary with question and options.
        :return: User's answer (either selected or entered).
        """
        question = question_obj['question']
        options = "\n".join(question_obj['options'])

        # Construct a full prompt
        prompt = f"{self.prompt_text}\n\n{question}\n\n{options}"
        return prompt

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

    async def execute(self, user_responses):
        """
        Main execution method that calls the profile-building process.

        :param user_responses: Dictionary of user responses (answers to the questions).
        :return: Structured profile.
        """
        # Collect responses and build profile
        return self.collect_responses(user_responses)
