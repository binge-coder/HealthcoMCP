from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import os

# Initialize FastMCP server
# Host 0.0.0.0 makes it accessible externally (Render / Cloud)
port = int(os.environ.get("PORT", 8000))
mcp = FastMCP("healthco-mcp", host="0.0.0.0", port=port)

@mcp.tool()
async def create_patient(
    name: str,
    phone: str,
    secretKey: str,
    email: str = None,
    dateOfBirth: str = None
) -> str:
    """
    Create a new patient in the clinic system.

    secretKey usage:
    - Passed as MCP parameter
    - Sent in request BODY (backward compatibility)
    - Sent in request HEADER (preferred)
    """

    url = "http://49.50.66.74:5003/api/mcp/tools/create-patient"

    # ✅ Request Body (secretKey kept here)
    payload = {
        "name": name,
        "phone": phone,
        "secretKey": secretKey
    }

    if email:
        payload["email"] = email

    if dateOfBirth:
        payload["dateOfBirth"] = dateOfBirth

    # ✅ Request Headers (secretKey ALSO here)
    headers = {
        "X-Secret-Key": secretKey,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            return f"Successfully created patient: {response.text}"

        except httpx.HTTPStatusError as e:
            return (
                f"Failed to create patient. "
                f"Status: {e.response.status_code}, "
                f"Error: {e.response.text}"
            )
        except Exception as e:
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        # Run MCP in stdio mode (local / dev)
        mcp.run(transport="stdio")
    else:
        # Run MCP using SSE transport (Retell / Cloud)
        print(f"Starting MCP server on http://0.0.0.0:{port}")

        # Get underlying Starlette app
        app = mcp.sse_app()

        # Enable CORS (Retell AI / browser-safe)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        uvicorn.run(app, host="0.0.0.0", port=port)