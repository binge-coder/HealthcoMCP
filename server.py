from mcp.server.fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("healthco-mcp")

@mcp.tool()
async def ping() -> str:
    return "pong"

app = mcp.sse_app()