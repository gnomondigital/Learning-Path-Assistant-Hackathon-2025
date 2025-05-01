import os

import chainlit as cl
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.core_skills import MathSkill, TimeSkill

# Initialize Semantic Kernel
kernel = sk.Kernel()

# Configure API keys from environment variables
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# Add OpenAI chat completion service to the kernel
kernel.add_chat_service(
    "chat_completion", OpenAIChatCompletion("gpt-3.5-turbo", api_key))

# Register built-in skills
kernel.import_skill(TimeSkill(), "time")
kernel.import_skill(MathSkill(), "math")

# Create a custom semantic function using a prompt template
weather_prompt = """
You are an expert weather forecaster. 
Based on the location provided, give a hypothetical weather forecast.
Location: {{$location}}

Return your response as a concise weather report.
"""


@cl.on_chat_start
async def start():
    """
    Initializes the chat session and registers skills.
    """
    # Register the semantic function
    weather_skill = kernel.create_semantic_function(
        prompt_template=weather_prompt,
        function_name="get_weather",
        skill_name="weather",
        description="Get weather forecast for a location"
    )

    # Store the kernel in the user session
    cl.user_session.set("kernel", kernel)
    cl.user_session.set("chat_history", [])

    # Send welcome message
    await cl.Message(
        content="Welcome to the Semantic Kernel + Chainlit chat with plugins! Try asking about the weather, time, or math calculations."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Handles incoming user messages and routes to appropriate skills.
    """
    kernel = cl.user_session.get("kernel")
    chat_history = cl.user_session.get("chat_history", [])
    user_input = message.content

    # Add a thinking message
    thinking_msg = cl.Message(content="Thinking...")
    await thinking_msg.send()

    try:
        # Check if this is a weather query (simple keyword detection)
        if "weather" in user_input.lower() and "in" in user_input.lower():
            # Extract location (this is a simple approach - in production, use NER)
            parts = user_input.lower().split("in")
            if len(parts) > 1:
                location = parts[1].strip()

                # Call the weather skill
                context = kernel.create_new_context()
                context.variables["location"] = location
                weather_function = kernel.skills.get(
                    "weather").get("get_weather")
                response = await weather_function.invoke_async(context=context)
                response_text = str(response)

                # Update thinking message
                await thinking_msg.update(content=f"Processing weather request for {location}...")

            else:
                response_text = "I need a location to check the weather. Please specify a place."

        # Check if it's a math query
        elif any(term in user_input.lower() for term in ["calculate", "math", "plus", "minus", "multiply", "divide"]):
            # For simplicity, we'll just forward to the general chat function
            # In a real app, you'd parse the math operation and use the math skill directly
            chat_function = kernel.create_semantic_function(
                """
                You are a helpful AI assistant specializing in math.
                {{$user_input}}
                Solve the math problem step by step.
                """,
                function_name="math_chat",
                description="Solve math problems",
            )

            context = kernel.create_new_context()
            context.variables["user_input"] = user_input
            response = await chat_function.invoke_async(context=context)
            response_text = str(response)

            # Update thinking message
            await thinking_msg.update(content="Calculating...")

        # Default to general chat
        else:
            chat_function = kernel.create_semantic_function(
                """
                You are a helpful AI assistant.
                
                {{$chat_history}}
                
                Human: {{$user_input}}
                AI: 
                """,
                function_name="chat",
                description="Chat with the user",
            )

            context = kernel.create_new_context()
            context.variables["user_input"] = user_input
            context.variables["chat_history"] = "\n".join(chat_history)
            response = await chat_function.invoke_async(context=context)
            response_text = str(response)

            # Update thinking message
            await thinking_msg.update(content="Processing your request...")

        # Update chat history
        chat_history.append(f"Human: {user_input}")
        chat_history.append(f"AI: {response_text}")
        cl.user_session.set("chat_history", chat_history)

        # Remove the thinking message
        await thinking_msg.remove()

        # Send the response
        await cl.Message(content=response_text).send()

    except Exception as e:
        # Update thinking message with error
        await thinking_msg.update(content=f"Error occurred: {str(e)}")
