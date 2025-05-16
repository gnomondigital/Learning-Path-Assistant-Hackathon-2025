# Frontend - Automated Learning Paths Hackathon 2025

# Welcome to Chainlit! :rocket::robot_face:

This is the frontend for the Automated Learning Paths project. The frontend is built using [Chainlit](https://chainlit.io/), a framework for creating conversational AI applications.

## What does this project do?

The project aims to provide an automated and interactive learning experience by leveraging AI-driven conversational interfaces. The frontend serves as the user interface for interacting with the system.

## How to run the project

Before running this, follow these steps to enable the chat history feature:

1. uv add asyncpg
2. Copy environment variables:
```
cp .env.example .env
```
-> Get your own PROJECT_CONNECTION_STRING from azure 
-> Generate your own CHAINLIT_AUTH_SECRET by running this : uv run chainlit create-secret 
2. We now "imprint" our Prisma schema to the fresh PostgreSQL:
```
npx prisma migrate deploy
```

To view your data, use `npx prisma studio`.


For more detailed information, refer to the `READMEhistory.md` file.

To run the **frontend**, execute the following command from the frontend directory of the project

```bash
uv run python -m chainlit run demo_app/app.py
```

Make sure you have all the necessary dependencies installed before running the command.

## Prerequisites

- Python 3.10
- Chainlit installed (`uv add chainlit`)

## Useful Links :link:

- **Documentation:** Get started with our comprehensive [Chainlit Documentation](https://docs.chainlit.io) :books:
- **Discord Community:** Join our friendly [Chainlit Discord](https://discord.gg/k73SQ3FyUh) to ask questions, share your projects, and connect with other developers! :speech_balloon:

We can't wait to see what you create with Chainlit! Happy coding! :computer::blush:

## Welcome screen

To modify the welcome screen, edit the `chainlit.md` file at the root of your project. If you do not want a welcome screen, just leave this file empty.