import asyncio
import sys
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "claude-sonnet-4-6"   # was claude-haiku-4-5
llm = Anthropic()            # reads ANTHROPIC_API_KEY from the environment

SYSTEM = (
    "You are a publishing assistant for a blog. To publish a post you MUST, in order: "
    "(1) call validate_post; if it is not ok, STOP and report exactly what is missing — never publish a broken post. "
    "(2) if valid, call generate_card to build the card. "
    "(3) call insert_card to add it to the index. "
    "(4) call commit_and_push to commit and push the post and index. "
    "(5) call wait_for_live to confirm the post is serving before you finish. "
    "Pass dry_run=true to BOTH insert_card and commit_and_push unless the user explicitly says to publish for real; "
    "on a dry run, do NOT call wait_for_live (nothing was pushed). "
    "If any step returns ok=false, STOP and report it. Explain each step as you go."
)

def to_anthropic(mcp_tools):
    return [{"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
            for t in mcp_tools.tools]

async def run(request):
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = to_anthropic(await session.list_tools())
            messages = [{"role": "user", "content": request}]

            while True:
                resp = llm.messages.create(
                    model=MODEL, max_tokens=1024, system=SYSTEM,
                    tools=tools, messages=messages,
                )
                for block in resp.content:
                    if block.type == "text":
                        print("\nCLAUDE:", block.text)
                if resp.stop_reason != "tool_use":
                    break
                messages.append({"role": "assistant", "content": resp.content})
                results = []
                for block in resp.content:
                    if block.type == "tool_use":
                        print(f"  → {block.name}({block.input})")
                        out = await session.call_tool(block.name, block.input)
                        text = "\n".join(b.text for b in out.content if getattr(b, "type", "") == "text")
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": text})
                messages.append({"role": "user", "content": results})

if __name__ == "__main__":
    request = sys.argv[1] if len(sys.argv) > 1 else "Publish the post at blog/squish/ as a dry run."
    asyncio.run(run(request))
