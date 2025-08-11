# Basic smoke tests for the MCP server interfaces (no host needed)

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Assumes FastAPI server mounts MCP at /mcp on localhost:3000

async def main():
    async with streamablehttp_client("http://localhost:3000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # Call list_databases tool
            await session.call_tool("list_databases", {})

if __name__ == "__main__":
    asyncio.run(main())
