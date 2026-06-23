import os
import re
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rnv-publishing")

BLOG_REPO = Path(os.environ.get("BLOG_REPO", "/workspaces/rnvizion.github.io"))
SITE_URL = os.environ.get("SITE_URL", "https://rnvizion.dev")
CORPUS_REPO = Path(os.environ.get("CORPUS_REPO", "/workspaces/ask-the-corpus"))

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

def _git(*args):
    """Run a git command inside the blog repo; returns the CompletedProcess."""
    return subprocess.run(["git", *args], cwd=BLOG_REPO, capture_output=True, text=True)

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

@mcp.tool()
def commit_and_push(slug: str, message: str = "", dry_run: bool = False) -> dict:
    """Stage the post and the blog index, commit, and push to the remote.

    Stages only blog/<slug>/index.html and blog/index.html — the two files a publish
    touches — so unrelated working-tree changes are left alone. Idempotent: if those
    files have no changes, it reports nothing to commit rather than erroring.
    dry_run=True reports what would be committed without writing or pushing."""
    post = f"blog/{slug}/index.html"
    index = "blog/index.html"
    msg = message or f"Publish: {slug}"

    status = _git("status", "--porcelain", "--", post, index)
    if status.returncode != 0:
        return {"slug": slug, "ok": False, "error": status.stderr.strip() or "git status failed"}
    pending = [line[3:] for line in status.stdout.splitlines() if line.strip()]
    if not pending:
        return {"slug": slug, "ok": True, "committed": False,
                "reason": "nothing to commit (post and index already up to date)"}

    if dry_run:
        return {"slug": slug, "ok": True, "committed": False,
                "would_commit": pending, "message": msg}

    add = _git("add", "--", post, index)
    if add.returncode != 0:
        return {"slug": slug, "ok": False, "error": add.stderr.strip() or "git add failed"}
    commit = _git("commit", "-m", msg)
    if commit.returncode != 0:
        return {"slug": slug, "ok": False, "error": commit.stderr.strip() or "git commit failed"}
    push = _git("push")
    if push.returncode != 0:
        return {"slug": slug, "ok": False, "committed": True, "pushed": False,
                "error": push.stderr.strip() or "git push failed"}
    return {"slug": slug, "ok": True, "committed": True, "pushed": True,
            "message": msg, "files": pending}

@mcp.tool()
def wait_for_live(slug: str, timeout: int = 180, interval: int = 10) -> dict:
    """Poll the live post URL until it returns HTTP 200, up to `timeout` seconds.

    Run after commit_and_push and before re-ingesting, so the RAG never fetches a
    404/403 during the GitHub Pages deploy window. Returns ok=False on timeout."""
    url = f"{SITE_URL}/blog/{slug}/"
    deadline = time.monotonic() + timeout
    last = None
    while True:
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                last = r.status
                if r.status == 200:
                    return {"slug": slug, "ok": True, "live": True, "status": 200, "url": url}
        except urllib.error.HTTPError as e:
            last = e.code
        except Exception as e:  # connection errors, timeouts, DNS, etc.
            last = str(e)
        if time.monotonic() >= deadline:
            return {"slug": slug, "ok": False, "live": False, "url": url,
                    "last_status": last, "error": f"not live after {timeout}s (last seen: {last})"}
        time.sleep(interval)

@mcp.tool()
def update_corpus(slug: str, dry_run: bool = False) -> dict:
    """Register a published post with the RAG corpus and trigger a rebuild.

    Verifies the live post URL returns 200 (refuses to register a dead source),
    appends it to the corpus sources.json if not already present, then commits and
    pushes that change. A GitHub Action in the corpus repo (rebuild-corpus.yml)
    does the actual re-ingest and Hugging Face Space push on that push, so this tool
    stays light and never imports the ML stack.
    dry_run=True reports what it would add without writing or pushing."""
    url = f"{SITE_URL}/blog/{slug}/"

    # Refuse to register a source that isn't live (no broken sources).
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            if r.status != 200:
                return {"slug": slug, "ok": False,
                        "error": f"{url} returned {r.status}; not registering a dead source (run wait_for_live first)"}
    except Exception as e:
        return {"slug": slug, "ok": False,
                "error": f"{url} not reachable ({e}); run wait_for_live first"}

    sources_path = CORPUS_REPO / "sources.json"
    if not sources_path.exists():
        return {"slug": slug, "ok": False,
                "error": f"sources.json not found at {sources_path} — set CORPUS_REPO to your ask-the-corpus checkout"}

    data = json.loads(sources_path.read_text(encoding="utf-8"))
    sources = data.setdefault("sources", [])
    if any(s.get("url") == url or s.get("id") == slug for s in sources):
        return {"slug": slug, "ok": True, "added": False, "reason": "already in sources.json"}

    if dry_run:
        return {"slug": slug, "ok": True, "added": False, "would_add": {"id": slug, "url": url}}

    sources.append({"id": slug, "url": url})
    sources_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _cgit(*args):
        return subprocess.run(["git", *args], cwd=CORPUS_REPO, capture_output=True, text=True)

    add = _cgit("add", "--", "sources.json")
    if add.returncode != 0:
        return {"slug": slug, "ok": False, "added": True, "error": add.stderr.strip() or "git add failed"}
    commit = _cgit("commit", "-m", f"corpus: add {slug}")
    if commit.returncode != 0:
        return {"slug": slug, "ok": False, "added": True, "error": commit.stderr.strip() or "git commit failed"}
    push = _cgit("push")
    if push.returncode != 0:
        return {"slug": slug, "ok": False, "added": True, "pushed": False,
                "error": push.stderr.strip() or "git push failed (corpus repo write permission?)"}
    return {"slug": slug, "ok": True, "added": True, "pushed": True, "url": url,
            "note": "pushed; the rebuild-corpus Action will re-ingest and update the Space"}

@mcp.tool()
def publish_post(slug: str, for_real: bool = False) -> dict:
    """Run the entire publish chain for a post in one deterministic sequence and
    stop at the first failure, returning the full trace.

    Order: validate_post -> generate_card -> insert_card -> (if for_real)
    commit_and_push -> wait_for_live -> update_corpus.

    for_real=False (the default) is a dry run: it validates, builds the card, and
    previews the index insert without writing, then stops — nothing is pushed.
    for_real=True runs the whole thing for keeps. This is the one call the agent
    should use to publish; the individual tools remain for single-step work."""
    trace = []

    def step(name, result):
        entry = {"step": name}
        entry.update(result if isinstance(result, dict) else {"result": result})
        trace.append(entry)
        return result

    v = step("validate_post", validate_post(slug))
    if not v.get("ok"):
        return {"slug": slug, "ok": False, "stopped_at": "validate_post", "trace": trace}

    c = step("generate_card", generate_card(slug))
    if not c.get("ok"):
        return {"slug": slug, "ok": False, "stopped_at": "generate_card", "trace": trace}

    ins = step("insert_card", insert_card(slug, c.get("card_html", ""), dry_run=not for_real))
    if not ins.get("ok"):
        return {"slug": slug, "ok": False, "stopped_at": "insert_card", "trace": trace}

    if not for_real:
        return {"slug": slug, "ok": True, "dry_run": True,
                "note": "dry run — nothing written or pushed; the steps above would run for real on publish",
                "trace": trace}

    cp = step("commit_and_push", commit_and_push(slug))
    if not cp.get("ok"):
        return {"slug": slug, "ok": False, "stopped_at": "commit_and_push", "trace": trace}

    live = step("wait_for_live", wait_for_live(slug))
    if not live.get("ok"):
        return {"slug": slug, "ok": False, "stopped_at": "wait_for_live", "trace": trace}

    uc = step("update_corpus", update_corpus(slug))
    if not uc.get("ok"):
        return {"slug": slug, "ok": False, "stopped_at": "update_corpus", "trace": trace}

    return {"slug": slug, "ok": True, "published": True, "trace": trace}

if __name__ == "__main__":
    print("rnv-publishing MCP server ready", file=sys.stderr, flush=True)
    mcp.run()
