import os
import re
import sys
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rnv-publishing")

BLOG_REPO = Path(os.environ.get("BLOG_REPO", "/workspaces/rnvizion.github.io"))

def _strip_comments(html: str) -> str:
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)

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
        html = _strip_comments(index.read_text(encoding="utf-8"))
        slug = index.parent.name
        title = _meta(html, "property", "og:title") or slug
        date = _meta(html, "property", "article:published_time")
        posts.append({"slug": slug, "title": title, "published": date})
    return posts

@mcp.tool()
def validate_post(slug: str) -> dict:
    """Check a post has everything the feed needs before publishing.
    Returns ok=False with the missing items if anything required is absent."""
    path = BLOG_REPO / "blog" / slug / "index.html"
    if not path.exists():
        return {"slug": slug, "ok": False, "error": f"no index.html at blog/{slug}/"}
    body = _strip_comments(path.read_text(encoding="utf-8"))
    required = {
        "<article> block": bool(re.search(r"<article[^>]*>.*?</article>", body, flags=re.S)),
        "og:url": bool(_meta(body, "property", "og:url")),
        "article:published_time": bool(_meta(body, "property", "article:published_time")),
    }
    recommended = {
        "og:title": bool(_meta(body, "property", "og:title")),
        "og:description": bool(_meta(body, "property", "og:description")),
        "card:summary": bool(_meta(body, "name", "card:summary")),
        "article:author": bool(_meta(body, "property", "article:author")),
    }
    missing_required = [k for k, ok in required.items() if not ok]
    missing_recommended = [k for k, ok in recommended.items() if not ok]
    return {
        "slug": slug,
        "ok": not missing_required,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
    }

@mcp.tool()
def generate_card(slug: str, summary: str = "") -> dict:
    """Generate the blog-index card HTML for a post by calling generate_card.py.
    Pass `summary` to override the card teaser line."""
    cmd = [sys.executable, "scripts/generate_card.py", f"blog/{slug}/index.html"]
    if summary:
        cmd += ["--summary", summary]
    result = subprocess.run(cmd, cwd=BLOG_REPO, capture_output=True, text=True)
    if result.returncode != 0:
        return {"slug": slug, "ok": False,
                "error": result.stderr.strip() or "generate_card.py failed"}
    return {"slug": slug, "ok": True,
            "card_html": result.stdout.strip(),
            "warnings": result.stderr.strip() or None}

@mcp.tool()
def insert_card(slug: str, card_html: str, dry_run: bool = False) -> dict:
    """Insert a post card at the top of the blog index (newest-first).
    Idempotent: does nothing if a card for this slug is already present.
    dry_run=True reports what would happen without writing."""
    index_path = BLOG_REPO / "blog" / "index.html"
    if not index_path.exists():
        return {"slug": slug, "ok": False, "error": "blog/index.html not found"}
    html = index_path.read_text(encoding="utf-8")

    if f'/blog/{slug}/"' in html:
        return {"slug": slug, "ok": True, "inserted": False, "reason": "already in index"}

    card = card_html.strip()
    marker = "<!-- post-cards -->"
    if marker in html:
        new_html = html.replace(marker, marker + "\n" + card, 1)
        anchor = "marker"
    else:
        m = re.search(r'<article class="post-card">', html)
        if not m:
            return {"slug": slug, "ok": False,
                    "error": "no insertion point: add a '<!-- post-cards -->' marker or a first card to blog/index.html"}
        new_html = html[:m.start()] + card + "\n" + html[m.start():]
        anchor = "before first card"

    if dry_run:
        return {"slug": slug, "ok": True, "inserted": False, "would_insert": True, "anchor": anchor}

    index_path.write_text(new_html, encoding="utf-8")
    return {"slug": slug, "ok": True, "inserted": True, "anchor": anchor}

if __name__ == "__main__":
    import sys
    print("SERVER STARTING", file=sys.stderr)
    mcp.run()
