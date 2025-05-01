# Automated Learning Paths - Hackathon 2025

Project submission for participation in the **Microsoft Hackathon 2025**.

## AI-Powered Upskilling Chatbot

### Overview
This project implements an AI-powered chatbot designed to assist users in skill development across various domains. By leveraging specialized agents, the chatbot efficiently manages personalized learning paths, profile building, and content discovery from both internal and external resources.

The system integrates **Azure** tools like **File Search** and **RAG (Retrieval-Augmented Generation)**, along with **Bing Search** to expand learning opportunities. Additionally, **Confluence** serves as an internal knowledge base for curated learning content.

---

## System Architecture

### Multi-Agent Functionality
The chatbot operates through several specialized agents, ensuring an efficient learning process:

#### **User Interaction**
- The **Basic Chat Agent** serves as the first point of contact, handling general inquiries and guiding users.

#### **Profile Collection**
- The **Profile Builder Agent** gathers user information to create a personalized learning profile.

#### **Learning Path Generation**
- The **Learning Path Agent** generates customized curricula based on user profiles and adapts to progress.

#### **Knowledge Retrieval**
- The **Confluence Agent** accesses GD Academy's internal knowledge base.
- The **Bing Search Agent** finds relevant external learning resources.

#### **Orchestration**
- The **Semantic Kernel Agent** manages the flow of information, ensuring queries are routed to the appropriate agent.

---

## Key Features

- **Personalized Learning Paths**: Curriculum recommendations based on user profiles.
- **Comprehensive Knowledge Access**: Internal (Confluence) and external (Bing Search) resource retrieval.
- **Multi-Agent System**: Specialization ensures high-quality responses.
- **Azure Integration**: Efficient data processing with **File Search** and other tools.

---

## Installation

To set up the project, follow these steps:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables: Make sure you have a .env file in the backend with the following variables configured:**:

```bash
CONFLUENCE_URL = ""
CONFLUENCE_USERNAME = ""
CONFLUENCE_API_KEY = ""
CONFLUENCE_SPACE_KEY = ""
HOMEPAGE_ID = ""
OPENAI_API_KEY = ""
DATA_DIRECTORY = "backend/data/confluence_markdown"
OUTPUT_DIRECTORY = "backend/data/confluence_markdown_metadata"
MODEL_DEPLOYMENT_NAME= ""
BING_CONNECTION_NAME= ""
PROJECT_CONNECTION_STRING= ""
```

3. **Run the Backend: To run the backend, use the following command with uv**:

```bash
uv run python -m backend.src.main
```

1. **Run the Frontend: To run the frontend with Chainlit, use the following command:**:

```bash
uv run chainlit run frontend/test.py -w
```

## Example Interactions:

CAPTURE

## Conclusion

This project leverages a combination of specialized agents, Azure tools, and Bing Search to provide a comprehensive, personalized upskilling experience for users. The chatbot is designed to guide users in enhancing their skills across a range of domains, offering both internal content and external learning resources to foster continuous learning.