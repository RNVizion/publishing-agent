import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CARD = '<article class="post-card">test</article>'

async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("tools:", [t.name for t in tools.tools])
            # already-present slug → idempotency guard fires
            r = await s.call_tool("insert_card", {"slug": "squish", "card_html": CARD, "dry_run": True})
            print("EXISTING:", r.content[0].text)
            # fake slug → shows it WOULD insert (no write, dry_run)
            r = await s.call_tool("insert_card", {"slug": "brand-new-post", "card_html": CARD, "dry_run": True})
            print("NEW:", r.content[0].text)

asyncio.run(main())
