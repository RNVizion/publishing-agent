import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("tools:", [t.name for t in tools.tools])
            r = await s.call_tool("validate_post", {"slug": "i-lacked-the-tools"})
            print("REAL:", r.content[0].text)
            r = await s.call_tool("validate_post", {"slug": "not-a-real-post"})
            print("FAKE:", r.content[0].text)

asyncio.run(main())
