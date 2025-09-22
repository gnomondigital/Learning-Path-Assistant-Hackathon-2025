# Learning Path Assistant - Hackathon 2025

Project submission for participation in the **Microsoft Hackathon 2025**.

### Read On Medium 

Read the full series on Medium to learn more about the journey and technical implementation of the Learning Path Assistant:
- [Building a Learning Path Assistant for the Microsoft Hackathon 2025](https://medium.com/gnomondigital/building-a-learning-path-assistant-for-the-microsoft-hackathon-2025-edd7a09bdaaf)
- [Part 1/3: Designing a Multi-Agent System for the Learning Path Assistant](https://medium.com/gnomondigital/part-1-3-designing-a-multi-agent-system-for-the-learning-path-assistant-5328b0b61b6a)
- [Part 2/3: From Architecture to Production with Azure AI Foundry](https://medium.com/gnomondigital/part-2-3-from-architecture-to-production-with-azure-ai-foundry-4d07d726996d)
- [Part 3/3: From Backend Intelligence to Interactive Learning Experience](https://medium.com/gnomondigital/part-3-3-from-backend-intelligence-to-interactive-learning-experience-a353a167a9d8)

## AI-Powered Upskilling Chatbot

### Overview
This project implements an **AI-powered chatbot** designed to assist users in skill development across various domains. The system uses a multi-agent architecture, integrating specialized agents to manage personalized learning paths, profile building, and content discovery from both **internal** and **external** resources.

The chatbot leverages **Azure** tools such as **RAG (Retrieval-Augmented Generation)**, **File Search**, and **Bing Search** to provide users with relevant educational content. **Confluence** serves as the internal knowledge base, offering curated learning materials. With this, the chatbot creates a dynamic learning experience by combining internal and external sources to offer tailored educational journeys.


### Project Image

![AI-Powered Upskilling Chatbot](./images/image.png)

---

## System Architecture

### Multi-Agent Functionality
The chatbot operates through several specialized agents, ensuring an efficient and personalized learning process:

#### **Profile Collection**
- **Profile Builder Agent**: Collects user information to build a personalized learning profile, which serves as the foundation for the learning path.

#### **Learning Path Generation**
- **Learning Path Agent**: Generates customized curricula based on the user's profile and adapts the learning journey as the user progresses.

#### **Knowledge Retrieval**
- **Confluence Agent**: Accesses GD Academy's internal knowledge base, providing users with detailed content on various topics.
- **Bing Search Agent**: Searches external resources like online courses, tutorials, and articles to enhance the learning experience with the latest external knowledge.

#### **Orchestration**
- **Semantic Kernel Agent**: Orchestrates the process by managing the flow of information between the agents, ensuring that user queries are routed to the appropriate agent for the best possible response.

---

## Key Features

- **Personalized Learning Paths**: Curriculum recommendations based on user profiles and preferences.
- **Comprehensive Knowledge Access**: Seamless integration of internal (Confluence) and external (Bing Search) resources to provide diverse learning materials.
- **Multi-Agent System**: Specialized agents ensure high-quality, domain-specific responses tailored to the user’s needs.
- **Azure Integration**: Efficient data processing with **File Search** and other Azure tools, improving system performance and scalability.

---

## Installation

### 1. **Install Dependencies**

To set up the project, run the following command to install the required packages:

```bash
uv sync
```

### 2. **Set up Environment Variables**
Ensure you have a .env file in the backend with the variables as configured in the example.env file

### 3. **Run the Backend**
 
```bash
uv run python -m backend.src.main
```

### 3. **Run the Frontend**
To run the frontend with Chainlit, use this command:
 
```bash
uv run python -m chainlit run frontend/app.py
```

### Conclusion
The AI-Powered Upskilling Chatbot leverages the power of Azure tools, Confluence, and Bing Search to offer a comprehensive and personalized learning experience. The system is designed to guide users through building their profiles and generating custom learning paths that include both internal and external resources. By leveraging specialized agents, the chatbot ensures that each user receives the most relevant and up-to-date content for their educational journey.
