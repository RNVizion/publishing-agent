# rnv-publishing (MCP)

A publishing agent for [rnvizion.dev](https://rnvizion.dev). One instruction ships a blog post end to end: it validates the post, generates the index card and a per-post social image, commits and pushes, waits for the page to go live, then refreshes the retrieval assistant that answers questions about the site.

A language model decides *whether* to publish. Deterministic tools do the work, in a fixed order, and refuse to ship anything broken.

Built on the Model Context Protocol (FastMCP) and the Anthropic API.

---

## The idea

The hard part of an agent isn't getting a model to call tools; it's keeping the failure modes legible when it does. This one draws a hard line between the two kinds of work:

- **Reasoning is the model's job.** It makes a single judgment from a plain-language request: publish this post, or don't; for real, or as a dry run.
- **Execution is the tools' job.** Every step that touches the filesystem, git, or the network is an ordinary Python function with one responsibility and a typed result. No step improvises.

The orchestration itself is code, not a prompt. `publish_post` runs the chain in sequence and stops at the first step that returns `ok: false`. That's deliberate: an earlier version let the model orchestrate the steps freely, and it occasionally skipped one, publishing a post with no index card. Moving the sequence into a tool removed that whole class of error. The model's only decision is the one a model is actually good at.

## The chain

`publish_post(slug, for_real)` runs, in order:

1. `validate_post` — checks the post carries everything the feed needs; **stops the publish if a required field is missing**
2. `generate_card` — builds the blog-index card from the post's own metadata
3. `insert_card` — inserts it at the top of the index (idempotent; a re-run is a no-op)
4. `generate_og_image` — renders the per-post Open Graph share image (Pillow, in the site's palette)
5. `commit_and_push` — stages the post, card, and image, commits, and pushes
6. `wait_for_live` — polls the live URL until it returns 200, so nothing downstream runs against a page that hasn't deployed
7. `update_corpus` — registers the post with the RAG corpus and triggers a rebuild

A **dry run** (`for_real=false`, the default) runs steps 1–3 in preview and stops, writing and pushing nothing. It's a full rehearsal with no side effects.

## Refusal as a design value

The agent would rather publish nothing than publish something half-built.

- `validate_post` separates required fields from recommended ones; a missing required field halts the chain with an exact report of what's absent.
- `update_corpus` refuses to register a URL that isn't live, so the assistant's knowledge base never points at a 404.
- `wait_for_live` gates the corpus rebuild behind a confirmed-live page.

Each tool returns `{ ok, ... }`, so the chain reasons about success structurally instead of parsing prose.

## The tools

| Tool | Job |
| --- | --- |
| `list_posts` | Enumerate published posts with slug, title, date |
| `validate_post` | Gate: required vs. recommended fields |
| `generate_card` | Build the blog-index card |
| `generate_og_image` | Render the per-post share image |
| `insert_card` | Insert the card, newest-first (idempotent) |
| `commit_and_push` | Stage the post + card + image, commit, push |
| `wait_for_live` | Poll until the page serves 200 |
| `update_corpus` | Register the post and trigger a RAG rebuild |
| `publish_post` | Run the whole chain, stopping at the first failure |

## Usage

Run from a Codespace on the site repo, where the agent has native write access:

```bash
# rehearse — validates, builds the card, previews the insert, writes nothing
python agent.py "Publish blog/<slug> as a dry run."

# ship it — runs the full chain
python agent.py "Publish blog/<slug> for real."
```

## How it fits together

The agent edits the **site** repo directly and pushes natively. The RAG rebuild runs where it belongs: `update_corpus` commits a one-line source change to the corpus repo, and a GitHub Action there re-ingests and pushes the vector store to a Hugging Face Space. The heavy ML dependencies and the Hugging Face token stay in CI, never in the publishing environment.

```
agent.py  ──drives──►  server.py (FastMCP: 8 tools)
                            │
          ┌─────────────────┼──────────────────┐
   site repo (Pages)   live site (poll)   corpus repo → Action → HF Space
```

## Setup

Environment:

- `ANTHROPIC_API_KEY` — the reasoning model
- `BLOG_REPO` — path to the site checkout (default `/workspaces/rnvizion.github.io`)
- `CORPUS_REPO` — path to the corpus checkout (default `/workspaces/ask-the-corpus`)
- `SITE_URL` — live origin for `wait_for_live` (default `https://rnvizion.dev`)

Dependencies: the Anthropic SDK, the MCP SDK, and Pillow (for the share image). Install with `pip install -r requirements.txt`.

## What this demonstrates

For anyone reading this as work rather than docs:

- **Agentic design that's safe by construction.** The model holds one decision; the pipeline is deterministic code. Failures are typed and stop the chain, not silent.
- **MCP as a tool layer.** A clean FastMCP server with small, single-purpose, idempotent tools that compose.
- **Integrity gating.** "Refuse to ship broken" is enforced in code, at three points, not left to a prompt.
- **Real automation on a real system.** It extends an existing static site, feed, and retrieval assistant; it isn't a toy built to demo the pattern.

---

Built by Christian Smith ([RNVizion](https://rnvizion.dev)).
