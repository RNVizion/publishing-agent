# Publishing Agent (MCP)

An AI agent that publishes blog posts by orchestrating a set of [MCP](https://modelcontextprotocol.io) tools — and refuses to publish a post that isn't ready.

It wraps the real publishing pipeline for [rnvizion.dev](https://rnvizion.dev): generating the index card, validating a post's metadata, and inserting the card into the blog index. A Claude agent decides the order, runs the steps, and stops if anything is wrong.

## Why

Publishing a post by hand is a chore of small, repeatable steps: generate the card, check the post has the metadata the feed needs, insert the card newest-first, push. None of it is hard; all of it is easy to fat-finger. This automates the chore once so it never has to be done by hand again, and it runs the validation more reliably than a tired human would.

## How it works

Two pieces:

- **An MCP server** (`server.py`) exposes the publishing pipeline as four tools. The tools do the deterministic file work; they don't make decisions.
- **A Claude agent** (`agent.py`) connects to the server and, given a request like *"publish the post at blog/squish/"*, orchestrates the tools in order and reports what it did in plain language.

The design principle is **deterministic tools, agentic reasoning.** The agent never reimplements logic that already lives in a script; it calls the canonical tool and decides what to do with the result.

### The tools

| Tool | What it does |
|------|--------------|
| `list_posts` | Lists every published post with its slug, title, and date |
| `validate_post` | Checks a post has everything the feed requires; returns exactly what is missing |
| `generate_card` | Builds the blog-index card by calling the existing `generate_card.py` |
| `insert_card` | Inserts the card at the top of the index; idempotent, with a `dry_run` mode |

### Safety

- **The gatekeeper.** `validate_post` separates *required* fields (missing ones break the feed) from *recommended* ones. The agent stops hard on a missing required field and refuses to publish, so no half-broken posts go live.
- **Idempotency.** `insert_card` does nothing if a card for that slug is already in the index. No duplicates.
- **Dry run.** Every insert can be previewed without writing a byte.

## Usage

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
export BLOG_REPO="/path/to/your/blog/repo"   # defaults to a sibling clone

# dry run (safe)
python agent.py "Publish the post at blog/squish/ as a dry run."

# for real
python agent.py "Publish the post at blog/squish/ for real."
```

## Stack

Python · [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (FastMCP) · Anthropic API (Claude) · BeautifulSoup + lxml

## What this demonstrates

Agentic design patterns, MCP tool-layer integration, the separation of deterministic execution from LLM reasoning, and a real automation built on an existing system rather than a toy.
