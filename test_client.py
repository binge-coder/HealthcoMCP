import asyncio
import sys
import traceback
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

# URL of your MCP server
SERVER_URL = "http://localhost:8000/sse" 
# SERVER_URL = "https://healthcomcp.onrender.com/sse"

async def main():
    print(f"Connecting to {SERVER_URL}...")
    
    try:
        async with sse_client(SERVER_URL) as streams:
            print("Connected to SSE endpoint.")
            
            async with ClientSession(streams[0], streams[1]) as session:
                print("Initializing session...")
                await session.initialize()
                print("Session initialized.")
                
                print("Listing tools...")
                result = await session.list_tools()
                
                print(f"\nFound {len(result.tools)} tools:")
                for tool in result.tools:
                    print(f"- {tool.name}: {tool.description}")
                    print(f"  Schema: {tool.inputSchema}")

                # Optional: Call the tool to test it
                # print("\nTesting create_patient tool...")
                # call_result = await session.call_tool(
                #     "create_patient",
                #     arguments={
                #         "name": "Test User",
                #         "phone": "1234567890"
                #     }
                # )
                # print(f"Result: {call_result}")

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        print("Make sure the server is running and the URL is correct.")

if __name__ == "__main__":
    # Fix for Windows asyncio loop policy if needed
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
