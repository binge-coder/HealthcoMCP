from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.routing import Mount, Route
import uvicorn
import httpx
import os

# Initialize FastMCP server
# Render/Cloud Run set the PORT environment variable.
port = int(os.environ.get("PORT", 8000))
mcp = FastMCP("healthco-mcp")

@mcp.tool()
async def create_patient(name: str, phone: str, secretKey: str, email: str = None, dateOfBirth: str = None) -> str:
    """Create a new patient in the clinic system.

    Args:
        name: The name of the patient.
        phone: The phone number of the patient.
        secretKey: The secret key for authentication.
        email: The email of the patient.
        dateOfBirth: The date of birth of the patient.
    """
    url = "http://49.50.66.74:5003/api/mcp/tools/create-patient"
    
    payload = {
        "name": name,
        "phone": phone,
        "secretKey": secretKey
    }
    if email:
        payload["email"] = email
    if dateOfBirth:
        payload["dateOfBirth"] = dateOfBirth

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return f"Successfully created patient: {response.text}"
        except httpx.HTTPStatusError as e:
            return f"Failed to create patient. Status: {e.response.status_code}, Error: {e.response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    import sys
    arg_transport = sys.argv[1].lower() if len(sys.argv) > 1 else None

    # Modes:
    # - stdio: local VS Code MCP (spawned process)
    # - sse: legacy HTTP+SSE (endpoint at /sse)
    # - streamable-http: recommended for remote deployments (endpoint at /mcp)
    if arg_transport == "stdio":
        mcp.run(transport="stdio")
        raise SystemExit(0)

    transport = (arg_transport or os.environ.get("MCP_TRANSPORT") or "streamable-http").lower()
    if transport in {"http", "streamable", "streamablehttp"}:
        transport = "streamable-http"

    if transport not in {"sse", "streamable-http"}:
        raise SystemExit(
            "Invalid transport. Use one of: stdio | sse | streamable-http (default)."
        )

    # Build the MCP ASGI app and mount it at a stable path.
    # VS Code 'type: http' works best with streamable-http at /mcp.
    if transport == "streamable-http":
        mcp_asgi = mcp.streamable_http_app()
        mount_path = os.environ.get("MCP_MOUNT_PATH", "/mcp")
    else:
        mcp_asgi = mcp.sse_app()
        mount_path = os.environ.get("MCP_MOUNT_PATH", "/")

    if not mount_path.startswith("/"):
        mount_path = f"/{mount_path}"

    async def health(_: object) -> JSONResponse:
        return JSONResponse({"status": "ok", "transport": transport, "mount": mount_path})

    async def index(_: object):
        if transport == "streamable-http":
            return RedirectResponse(url=f"{mount_path}")
        return PlainTextResponse("MCP server is running. SSE endpoint is at /sse")

    app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/", index, methods=["GET"]),
            Mount(mount_path, app=mcp_asgi),
        ]
    )

    # CORS is mainly relevant for browser-based clients.
    # If you truly need credentialed requests, set MCP_CORS_ORIGINS to a comma-separated allowlist.
    cors_origins = os.environ.get("MCP_CORS_ORIGINS", "*")
    allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    allow_credentials = os.environ.get("MCP_CORS_ALLOW_CREDENTIALS", "false").lower() == "true"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

    print(f"Starting MCP server on http://0.0.0.0:{port} ({transport} at {mount_path})")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
