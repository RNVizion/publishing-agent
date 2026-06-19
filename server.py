import os
import re
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rnv-publishing")

# Blog repo path. Defaults to the sibling clone in the codespace;
# override with the BLOG_REPO env var anywhere else.
BLOG_REPO = Path(os.environ.get("BLOG_REPO", "/workspaces/rnvizion.github.io"))

def _meta(html: str, attr: str, value: str) -> str:
    """Pull a <meta {attr}="{value}" content="..."> field; '' if absent.
    Backreference on the quote handles apostrophes inside the content."""
    m = re.search(
        rf'<meta\s+{attr}=["\']{re.escape(value)}["\']\s+content=(["\'])(.*?)\1',
        html, flags=re.I | re.S,
    )
    return m.group(2).strip() if m else ""

@mcp.tool()
def list_posts() -> list[dict]:
    """List every published post in the blog with its slug, title, and date."""
    blog_dir = BLOG_REPO / "blog"
    if not blog_dir.exists():
        raise ValueError(f"blog dir not found at {blog_dir} — set BLOG_REPO to your blog repo path")
    posts = []
    for index in sorted(blog_dir.glob("*/index.html")):
        html = index.read_text(encoding="utf-8")
        slug = index.parent.name
        title = _meta(html, "property", "og:title") or slug
        date = _meta(html, "property", "article:published_time")
        posts.append({"slug": slug, "title": title, "published": date})
    return posts

if __name__ == "__main__":
    mcp.run()
