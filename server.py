from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rnv-publishing")

@mcp.tool()
def ping(name: str) -> str:
    """Smoke-test tool — echoes a greeting."""
    return f"pong: {name}"

if __name__ == "__main__":
    mcp.run()
