# Frontend - Learning Path Assistant Hackathon 2025

## Project Overview
The Learning Path project is designed to build personalized learning journeys by integrating AI-driven assistance. It provides users with tailored recommendations, helping them progress in their fields efficiently. The frontend plays a crucial role in delivering an intuitive experience, making interactions smooth and visually engaging.

![Learning Path Frontend](./images/1.png "Screenshot of the Learning Path Frontend")

## 1. Initializing Chainlit: [Chainlit Documentation](https://docs.chainlit.io/get-started/overview)

The first steps in setting up the frontend with chainlit, a framework that facilitates AI-driven conversational interfaces, is initializing Chainlit then running the following command:

```bash
uv run chainlit run app.py
```
At this point, seeing the application start up felt like unlocking the first piece of the puzzle. The interface loaded, and I could begin interacting with the AI, but it was still disconnected from the backend.

## 2. Connecting to the Backend:
To ensure the frontend could effectively communicate with the backend, I had to modify my code and configure my .env file properly. This involved:

```bash
PROJECT_CONNECTION_STRING="get your project connection string from AZURE AI FOUNDRY"
AZURE_API_KEY="get your api_key"
DEPLOYMENT_NAME="get your deployment name"
AZURE_ENDPOINT="get your azure endpoint"
PROMPT: "You are GD Academy's AI assistant. Answer questions or delegate to other agents.",
```
  1. Setting environment variables for seamless integration.
  2. Adjusting the backend for smooth data exchange.
  3. Debugging connection issues to ensure real-time interaction.

These early steps laid the foundation for a fully functioning frontend, bridging the gap between user inputs and intelligent responses from the backend.

## 3. Cleaning Up the Code & Structuring Endpoints
As the project evolved, I realized that a cleaner codebase was essential for scalability and maintainability. I restructured the backend, creating dedicated endpoints to improve separation of concerns. Once the backend is done and working , i created the API calls in the frontend in order to retreive the responses.

## 4. Displaying the Tools Used by the Agent
I wanted users to see which tools the agent was calling when answering queries. Initially, this posed a challenge. How could I extract this information while ensuring a smooth response generation process?

After some debugging, I managed to:
1. Track the functions/tools invoked by the agent dynamically.
2. Integrate the tool display alongside responses in the frontend using the tool calling of chainlit : [Chainlit Step Documentation](https://docs.chainlit.io/concepts/step#step)

```bash
@cl.step(type="tool")
```

3. Ensure a seamless experience where users receive both the answer and insight into how the agent reached it.

![Learning Path Frontend - Alternate View](images/2.png "Alternate screenshot of the Learning Path Frontend")

This added transparency enhances trust in the system, showing users not only what the agent says but also how it arrives at its conclusions.

## 5. Adding Conversation History to the Frontend Chatbot

As I continued refining the chatbot experience, I wanted to add chat history so users could see previous conversations seamlessly. Initially, I struggled with documentation on how to implement this in Chainlit, until I discovered [Chainlit Datalayer (GitHub Repo)](https://github.com/Chainlit/chainlit-datalayer), a valuable resource that outlined the process of creating conversation history in a Chainlit app.

![Learning Path Frontend - Conversation History](images/3.png "Screenshot showcasing conversation history in the Learning Path Frontend")

## 6. Using Chainlit Datalayer & PostgreSQL

This GitHub repository utilizes a PostgreSQL database running inside a Docker container, making data handling efficient. The setup allowed me to visualize users, conversations, and threads directly in a structured database.

#### Docker Configuration

To integrate this feature, I had to set up the following services in Docker:

```yaml
services:
  postgres:
    image: postgres:16
    volumes:
      - ./.data/postgres:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-root}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-root}
      - POSTGRES_DB=${POSTGRES_DB:-postgres}
    ports:
      - ${POSTGRES_PORT:-5432}:5432

  localstack:
    image: localstack/localstack:latest
    environment:
      SERVICES: s3
    ports:
      - 4566:4566
    volumes:
      - ./localstack-script.sh:/etc/localstack/init/ready.d/script.sh
      - "/var/run/docker.sock:/var/run/docker.sock"
```

Once the Docker container was running, I configured Chainlit to connect to the PostgreSQL database by updating the `.env` file with the appropriate database credentials:

```bash
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/chainlit_db
```

This setup enabled seamless storage and retrieval of conversation data, enhancing the chatbot's functionality and user experience.

### Understanding the Docker Compose Configuration

The Docker Compose file you provided sets up multiple services inside Docker containers, making it easier to manage dependencies and environments. Let’s break it down:

#### 📌 What This Docker File Does

The Docker Compose configuration defines services that your Chainlit Datalayer uses to store and retrieve conversation history. The key parts are:

- **PostgreSQL (postgres service)** → Stores all data related to users, chat conversations, and threads.
- **LocalStack (localstack service)** → Simulates AWS S3 for potential file storage.

Each of these services runs in its own isolated container, ensuring that they don’t interfere with your local system setup.

#### 🚀 Why PostgreSQL Is Useful

PostgreSQL is a powerful relational database known for handling structured queries efficiently. In my case, it helped by:

- **Using Docker to avoid local installation issues** → Running it in a container means you don’t need to manually install PostgreSQL on your system; it’s isolated.
- **Persisting chat history** → Every conversation is stored as a thread inside the database.
- **Keeping track of user interactions** → So you can retrieve messages later.
- **Making data visualization easier** → You could query the database to inspect users and messages directly.

![Learning Path Frontend - Enhanced View](images/4.png "Enhanced screenshot of the Learning Path Frontend")

## 7. Overcoming Execution Issues

At first, I faced a major challenge when trying to integrate the database layer. I was executing my code from the project root, which didn’t work for this setup. Instead, I realized that I needed to execute the code from the frontend directory for the conversation elements to appear correctly on the right-hand side of the UI.

After troubleshooting and adjusting my execution flow, I successfully integrated the Chainlit Datalayer into my project! The final step was refining the frontend logic to ensure the conversation history appeared smoothly alongside new responses.

![Learning Path Frontend - Final View](images/5.png "Final screenshot of the Learning Path Frontend")

## Conclusion

The journey of building the Learning Path AI Assistant has been one of constant iteration, refinement, and problem-solving. From the initial steps of setting up Chainlit, linking it to the backend, ensuring transparency in tool usage, and handling conversation history with Chainlit Datalayer, every challenge led to a more structured and scalable solution.

Integrating PostgreSQL via Docker allowed seamless conversation tracking and data management, while debugging execution contexts helped optimize how the frontend interacted with stored chat history. Through each phase, the focus remained on enhancing user experience, ensuring conversations felt dynamic, informative, and well-organized.

With clean code, structured components, and a fully operational Chainlit app, the project is now ready to empower learners with AI-driven guidance. The challenges faced and solutions discovered serve as a testament to the value of iteration and deep debugging in AI applications.

This documentation not only outlines the technical steps but also reflects the real-world problem-solving that shaped the project. Now, with a structured and scalable frontend, the foundation is set for future improvements and expansions in intelligent learning path recommendations.

![Learning Path Frontend - Additional View](images/6.png "Additional screenshot of the Learning Path Frontend")