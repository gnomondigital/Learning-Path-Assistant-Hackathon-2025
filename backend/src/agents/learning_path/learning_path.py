class LearningPath:
    def __init__(self, path: str):
        self.path = path

    def get_path(self):
        return self.path

    def set_path(self, new_path: str):
        self.path = new_path

    def _format_base_learning_path(self, path: dict) -> str:
        """
        Format the base learning path as a nice text output (fallback method).
        """
        output = f"# 🚀 Personalized Learning Path for {path['name']}\n\n"

        output += f"## Target Role: {path['target_role']}\n"
        output += f"## Timeline: {path['timeline']}\n\n"

        output += "### 📅 Daily Schedule Recommendation\n"
        output += f"{path['daily_schedule']}\n\n"

        output += "### 🎯 Recommended Skills to Focus On\n"
        for skill in path['recommended_skills']:
            output += f"- {skill}\n"
        output += "\n"

        output += "### 📚 Recommended Learning Resources\n"
        for resource in path['learning_resources']:
            output += f"- {resource}\n"
        output += "\n"

        output += "### 🏆 Key Milestones\n"
        for milestone in path['milestones']:
            output += f"- {milestone}\n"
        output += "\n"

        output += "### 📝 Next Steps\n"
        for step in path['next_steps']:
            output += f"- {step}\n"

        return output
