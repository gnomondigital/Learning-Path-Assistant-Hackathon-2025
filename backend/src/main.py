import asyncio
import logging
import os
from typing import List, Dict, Any

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    AsyncFunctionTool,
    AsyncToolSet,
    FileSearchTool,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from utils.config import Settings
from utils.utilities import Utilities
from utils.terminal_colors import TerminalColors as tc
from ingestion import ConfluenceIngestion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGAgent:
    def __init__(self):
        load_dotenv()
        self.settings = Settings()
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=self.settings.PROJECT_CONNECTION_STRING,
        )
        self.toolset = AsyncToolSet()
        self.confluence_ingestion = ConfluenceIngestion()
        self.utilities = Utilities()
        
    async def setup_tools(self):
        """Setup the tools for the RAG agent."""
        # Create async function tools for Confluence operations
        confluence_functions = AsyncFunctionTool({
            self.confluence_ingestion.extract_confluence_data,
            self.confluence_ingestion.fetch_page_details,
            self.confluence_ingestion.extract_and_process_confluence_data
        })
        self.toolset.add(confluence_functions)
        
        # Add file search tool for the ingested data
        vector_store = await self.utilities.create_vector_store(
            project_client=self.project_client,
            files=[os.path.join(self.settings.DATA_DIRECTORY, "confluence_data.json")],
            vector_store_name="Confluence Knowledge Base"
        )
        if vector_store:
            file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])
            self.toolset.add(file_search_tool)
        else:
            logger.error("Failed to create vector store")
        
    async def initialize_agent(self) -> tuple[Agent, AgentThread]:
        """Initialize the RAG agent with tools and instructions."""
        await self.setup_tools()
        
        instructions = open("./instructions/agent_instructions.txt", "r").read()
        
        agent = await self.project_client.agents.create_agent(
            model=self.settings.MODEL_DEPLOYMENT_NAME,
            name="Confluence RAG Agent",
            instructions=instructions,
            toolset=self.toolset,
            temperature=0.1,
            headers={"x-ms-enable-preview": "true"},
        )
        
        thread = await self.project_client.agents.create_thread()
        
        return agent, thread
        
    async def process_query(self, query: str, agent: Agent, thread: AgentThread):
        """Process a user query using the RAG agent."""
        try:
            self.confluence_ingestion.extract_and_process_confluence_data()
            
            # Post the query to the agent
            await self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            stream = await self.project_client.agents.create_stream(
                thread_id=thread.id,
                agent_id=agent.id,
                max_completion_tokens=10240,
                max_prompt_tokens=20480,
                temperature=0.1,
                top_p=0.1
            )
            
            full_response = ""
            async with stream as s:
                async for event in s:
                    if hasattr(event, "content") and event.content:
                        full_response += event.content  

            logger.info(f"Agent Response: {full_response}")
            return full_response  
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise


async def main():
    print(f"{tc.BLUE}Starting Confluence RAG Agent...{tc.RESET}")
    
    try:
        # Initialize the agent
        rag_agent = RAGAgent()
        print(f"{tc.GREEN}Initializing agent...{tc.RESET}")
        
        agent, thread = await rag_agent.initialize_agent()
        print(f"{tc.GREEN}Agent created successfully!{tc.RESET}")
        print(f"{tc.CYAN}Agent ID: {agent.id}{tc.RESET}")
        print(f"{tc.CYAN}Thread ID: {thread.id}{tc.RESET}")
        print(f"\n{tc.YELLOW}You can view your agent in Azure AI Foundry at:{tc.RESET}")
        print(f"{tc.BLUE}https://ai.azure.com/playground/agents/{agent.id}{tc.RESET}")
        
        # Start interactive session
        print(f"\n{tc.GREEN}Starting interactive session...{tc.RESET}")
        print(f"{tc.YELLOW}Type 'exit' to quit{tc.RESET}")
        
        while True:
            query = input(f"\n{tc.PURPLE}Enter your query: {tc.RESET}").strip()
            if query.lower() == 'exit':
                break
            response = await rag_agent.process_query(query, agent, thread)
            print(f"\n{tc.GREEN}Agent Response: {response}{tc.RESET}")
            #await rag_agent.process_query(query, agent, thread)
            
    except Exception as e:
        print(f"{tc.RED}Error: {str(e)}{tc.RESET}")
        raise
    finally:
        if 'agent' in locals() and 'thread' in locals():
            print(f"{tc.YELLOW}Cleaning up resources...{tc.RESET}")
            await rag_agent.project_client.agents.delete_thread(thread.id)
            await rag_agent.project_client.agents.delete_agent(agent.id)
            print(f"{tc.GREEN}Cleanup complete!{tc.RESET}")

if __name__ == "__main__":
    asyncio.run(main())