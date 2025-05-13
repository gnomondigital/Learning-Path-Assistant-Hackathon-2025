# Backend Overview

## Introduction

This document provides a comprehensive overview of the backend architecture for the **Automated Learning Paths Hackathon 2025** project. The backend is designed to handle user interactions, manage learning profiles, and retrieve educational resources from both internal knowledge (Confluence) and external sources (Web Search). The backend leverages multiple agents, each responsible for specific functionalities, ensuring an efficient and personalized learning experience.

---

## Agents and Functionalities

### 1. **Profile Builder Agent**
The **Profile Builder Agent** helps users create a personalized learning profile by asking a series of questions about their skills, goals, and preferences.

**Key Functions**:
- **Start Profile Flow**: Initiates the profile-building process.
- **Process User Response**: Handles user inputs and moves to the next question.
- **Skip Question**: Skips the current question.
- **Go Back**: Moves back to the previous question.
- **Profile Summary**: Displays a summary of the user's profile.
- **Reset Profile**: Resets the profile-building process.

---

### 2. **Web Search Agent**
The **Web Search Agent** uses **Bing Search** to find the most relevant and up-to-date educational resources on the web.

**Key Functions**:
- **Search Web**: Retrieves the most relevant search results based on the user's query.
- **Summarize and Return Links**: Provides a summary and links to the resources.

---

### 3. **Confluence Agent**
The **Confluence Agent** retrieves internal knowledge from **Confluence**, including documents, guides, and resources.

**Key Functions**:
- **Search Content**: Finds relevant content within Confluence.
- **Retrieve Page by ID**: Fetches content from a specific Confluence page.
- **Get Recent Pages**: Returns the most recent pages in a Confluence space.

---

### 4. **Semantic Kernel Agent**
The **Semantic Kernel Agent** processes natural language queries and routes them to the appropriate agent (Profile Builder, Web Search, Confluence).

**Key Functions**:
- **Process Message**: Handles the user's query and forwards it to the correct agent.
- **Integrates Agents**: Combines information from the Confluence and Web Search agents.
- **Authentication**: Manages user authentication.

---

### How They Work Together:
- **Profile Builder**: Collects and stores user data for personalized learning paths.
- **Web Search Agent**: Looks for external resources if Confluence does not provide enough information.
- **Confluence Agent**: Retrieves internal company-specific documents to answer the user's queries.

## How to Execute the Backend

### Prerequisites
- **Python** (v3.10r)

### Steps to Run
1. Clone the repository:
     ```bash
     git clone https://github.com/your-repo/automated-learning-paths-Hackathon2025.git
     cd automated-learning-paths-Hackathon2025
     ```

2. Configure environment variables:
     - Create a `.env` file in the root directory.
     - Add the required variables (Confluence URL, API keys...).

3. Start the backend server:
     ```bash
     uv run python -m backend.src.main
     ```
---
