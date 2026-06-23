import asyncio
import sys
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "claude-sonnet-4-6"   # the publish chain is short but multi-step; Sonnet keeps the one decision reliable
llm = Anthropic()             # reads ANTHROPIC_API_KEY from the environment

SYSTEM = (
    "You are a publishing assistant for a blog. To publish a post, call "
    "publish_post(slug, for_real). Use for_real=false (a dry run) by default; use "
    "for_real=true ONLY when the user explicitly says to publish for real. "
    "publish_post runs the full chain itself (validate, card, insert, and on a real "
    "run: commit and push, wait for live, update the RAG corpus) and stops at the "
    "first failure — read back its result and trace in plain language. The individual "
    "tools (validate_post, generate_card, insert_card, commit_and_push, wait_for_live, "
    "update_corpus, list_posts) remain available if the user asks for a single step."
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
