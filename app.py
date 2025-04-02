import google.generativeai as genai
import asyncio
import os
from dotenv import load_dotenv
#from gemini.converse_agent import ConverseAgent
from converse_agent import ConverseAgent
from converse_tools import ConverseToolManager
from mcp_client import MCPClient
from mcp import StdioServerParameters

# Load environment variables
load_dotenv("config.env")

print("[DEBUG] DB_PATH:", os.getenv("DB_PATH"))

async def main():
    """
    Main function that sets up and runs an interactive AI agent with tool integration.
    The agent can process user prompts and utilize registered tools to perform tasks.
    """
    # Load API key & model name from environment variables
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))#"AIzaSyDkd6hHfJAH20QAtUSppFRc48clSFmdfm0"))
    model_id = os.getenv("MODEL_NAME", "gemini-pro")

    # Set up the agent and tool manager
    agent = ConverseAgent()
    agent.tools = ConverseToolManager()

    # Define the agent's behavior through system prompt
    agent.system_prompt = """You are a helpful assistant that can use tools to help you answer 
    questions and perform tasks."""

    # Create server parameters for SQLite configuration
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-sqlite", "--db-path", os.getenv("DB_PATH", "C:/Users/Matta.Lakshmi/Desktop/MCPmikegc/Gemini/test.db")],
        env=None
    )

    async with MCPClient(server_params) as mcp_client:
        # Fetch available tools from the MCP client
        tools = await mcp_client.get_available_tools()
        #print("DEBUG: tools =", tools)

        # Register each available tool with the agent
        for tool in tools:
            agent.tools.register_tool(
                name=tool.name,
                func=mcp_client.call_tool,
                description=tool.description,
                input_schema={'json': tool.inputSchema}
            )

        # Start interactive prompt loop
        while True:
            try:
                # Get user input and check for exit commands
                user_prompt = input("\nEnter your prompt (or 'quit' to exit): ")
                if user_prompt.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Process the prompt using Google Gemini API
                response = await agent.invoke_with_gemini(user_prompt)  # Use Gemini instead
                print("\nResponse:", response)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError occurred: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
