#!/usr/bin/env bash
# ============================================================
# publish_sloth.sh  —  get the sloth post in place, then publish.
#
#   Run from anywhere in the publishing-agent Codespace:
#     bash publish_sloth.sh          # clone site, write post, verify, DRY RUN
#     bash publish_sloth.sh ship     # publish FOR REAL, then commit + push
#
#   Do the default run first. If the dry run shows the card with no
#   errors, then run the "ship" mode.
# ============================================================
set -uo pipefail

SITE="/workspaces/rnvizion.github.io"
AGENT="/workspaces/publishing-agent"
SLUG="sloth"
export BLOG_REPO="$SITE"
MODE="${1:-setup}"

clone_site() {
  if [ ! -d "$SITE/.git" ]; then
    echo "==> Cloning site repo to $SITE"
    git clone https://github.com/RNVizion/rnvizion.github.io.git "$SITE"
  else
    echo "==> Site repo already present at $SITE"
  fi
}

if [ "$MODE" = "ship" ]; then
  echo "==> SHIP MODE: publishing for real, then pushing"
  cd "$AGENT"
  python agent.py "Publish the post at blog/$SLUG/ for real."
  cd "$SITE"
  git add "blog/$SLUG/index.html" blog/index.html
  git commit -m "Publish: $SLUG"
  git push
  echo
  echo "==> Pushed. Next: confirm it is live, then re-ingest the RAG."
  echo "    curl -I https://rnvizion.dev/blog/$SLUG/"
  echo "    (then add the sloth URL to SOURCES and run the ingester)"
  exit 0
fi

# ---------- default: setup + dry run ----------
clone_site

echo "==> Writing blog/$SLUG/index.html"
mkdir -p "$SITE/blog/$SLUG"
cat > "$SITE/blog/$SLUG/index.html" <<'POST_EOF'
<!DOCTYPE html>
<html lang="en">
<!--
  ============================================================================
  RNVizion blog post — Lazy in the Right Way Is Leverage
  Place at: blog/sloth/index.html
  ============================================================================
-->
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Lazy in the Right Way Is Leverage — Christian Smith</title>
  <meta name="description" content="I built a machine to publish my blog, and it refused to ship a broken post. The two kinds of lazy, and why aiming effort at the future is leverage." />

  <!-- Blog-index card teaser. -->
  <meta name="card:summary" content="Two ways to be lazy about the same chore: one traps you in it forever, the other is how every tool ever got built." />

  <!-- Open Graph -->
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://rnvizion.dev/blog/sloth/" />
  <meta property="og:title" content="Lazy in the Right Way Is Leverage" />
  <meta property="og:description" content="I built a machine to publish my blog, and it refused to ship a broken post. The two kinds of lazy, and why aiming effort at the future is leverage." />
  <meta property="og:image" content="https://rnvizion.dev/assets/og-image.png" />
  <meta property="article:author" content="Christian Smith" />
  <meta property="article:published_time" content="2026-06-22" />

  <meta name="twitter:card" content="summary_large_image" />

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />

  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #0a0a0f;
      --bg-2: #11111a;
      --bg-3: #1a1a26;
      --border: #25253a;
      --border-soft: #1e1e2e;
      --text: #e8e8f0;
      --text-dim: #9a9ab0;
      --text-faint: #5a5a72;
      --accent: #d2bc93;
      --max-width: 1200px;
      --read-width: 720px;
      --font-display: 'Bricolage Grotesque', sans-serif;
      --font-serif: 'Instrument Serif', serif;
      --font-mono: 'JetBrains Mono', monospace;
      --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    html { scroll-behavior: smooth; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-body);
      font-size: 17px;
      line-height: 1.7;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(210, 188, 147, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(210, 188, 147, 0.025) 1px, transparent 1px);
      background-size: 48px 48px;
      pointer-events: none;
      z-index: 0;
      mask-image: radial-gradient(ellipse at center, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 70%);
    }

    body::after {
      content: '';
      position: fixed;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3CfeColorMatrix values='0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 0 0.55 0 0 0 0.04 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
      opacity: 0.5;
      pointer-events: none;
      z-index: 1;
    }

    main, nav, footer, article { position: relative; z-index: 2; }
    a { color: var(--accent); text-decoration: none; transition: color 0.2s ease; }
    a:hover { text-decoration: underline; text-underline-offset: 3px; }

    .container { max-width: var(--max-width); margin: 0 auto; padding: 0 32px; }
    .read-container { max-width: var(--read-width); margin: 0 auto; padding: 0 32px; }

    nav {
      position: sticky; top: 0;
      backdrop-filter: blur(20px);
      background: rgba(10, 10, 15, 0.7);
      border-bottom: 1px solid var(--border-soft);
      padding: 16px 0; z-index: 100;
    }

    nav .container {
      display: flex; justify-content: space-between; align-items: center;
    }

    .logo {
      font-family: var(--font-mono);
      font-weight: 600; font-size: 14px;
      letter-spacing: -0.5px; color: var(--text);
      display: flex; align-items: center; gap: 8px;
    }

    .logo .dot {
      width: 8px; height: 8px;
      background: var(--accent); border-radius: 50%;
      box-shadow: 0 0 12px var(--accent);
      animation: pulse 2.4s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    .nav-links {
      display: flex; gap: 32px;
      font-family: var(--font-mono); font-size: 13px;
    }

    .nav-links a { color: var(--text-dim); position: relative; }
    .nav-links a:hover { color: var(--accent); }
    .nav-links a.active { color: var(--accent); }
    .nav-links a:hover { text-decoration: none; }

    .nav-links a::after {
      content: ''; position: absolute;
      left: 0; bottom: -4px;
      width: 0; height: 1px; background: var(--accent);
      transition: width 0.25s ease;
    }

    .nav-links a:hover::after, .nav-links a.active::after { width: 100%; }

    .nav-toggle {
      display: none;
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 6px;
      width: 40px; height: 40px;
      cursor: pointer; padding: 0;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      gap: 5px;
      transition: border-color 0.2s ease;
    }

    .nav-toggle:hover { border-color: var(--accent); }

    .nav-toggle span {
      display: block; width: 18px; height: 1.5px;
      background: var(--text);
      transition: transform 0.25s ease, opacity 0.25s ease;
    }

    .nav-toggle.open span:nth-child(1) {
      transform: translateY(6.5px) rotate(45deg);
      background: var(--accent);
    }

    .nav-toggle.open span:nth-child(2) { opacity: 0; }

    .nav-toggle.open span:nth-child(3) {
      transform: translateY(-6.5px) rotate(-45deg);
      background: var(--accent);
    }

    @media (max-width: 640px) {
      .nav-toggle { display: flex; }

      .nav-links {
        position: fixed; top: 73px; left: 0; right: 0;
        background: rgba(10, 10, 15, 0.96);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border-soft);
        flex-direction: column; gap: 0;
        padding: 16px 32px 24px;
        transform: translateY(-12px);
        opacity: 0; pointer-events: none;
        transition: transform 0.25s ease, opacity 0.25s ease;
      }

      .nav-links.open {
        transform: translateY(0); opacity: 1; pointer-events: auto;
      }

      .nav-links a {
        padding: 14px 0; font-size: 15px;
        border-bottom: 1px solid var(--border-soft);
      }

      .nav-links a:last-child { border-bottom: none; }
      .nav-links a::after { display: none; }
    }

    .article-header { padding: 100px 0 60px; text-align: center; }

    .article-meta {
      font-family: var(--font-mono); font-size: 12px;
      color: var(--text-faint);
      text-transform: uppercase; letter-spacing: 0.15em;
      margin-bottom: 24px;
    }

    .article-meta .accent { color: var(--accent); }

    .article-header h1 {
      font-family: var(--font-display);
      font-size: clamp(2.2rem, 5vw, 3.6rem);
      font-weight: 500; letter-spacing: -0.03em;
      line-height: 1.1; margin-bottom: 32px;
    }

    .article-header h1 em {
      font-family: var(--font-serif);
      font-style: italic; color: var(--accent);
    }

    .article-subtitle {
      font-size: 1.15rem; color: var(--text-dim);
      max-width: 600px; margin: 0 auto;
    }

    .byline {
      font-family: var(--font-mono); font-size: 13px;
      color: var(--text-dim); margin-top: 28px;
      display: flex; justify-content: center;
      align-items: center; gap: 16px;
    }

    .byline-divider {
      width: 4px; height: 4px;
      background: var(--accent); border-radius: 50%;
    }

    article { padding: 40px 0 80px; }

    article p {
      margin-bottom: 24px; color: var(--text);
    }

    article p:first-of-type::first-letter {
      font-family: var(--font-serif);
      font-size: 4.2rem; float: left;
      line-height: 0.9;
      padding: 8px 14px 0 0;
      color: var(--accent);
    }

    article h2 {
      font-family: var(--font-display);
      font-size: 1.85rem; font-weight: 500;
      letter-spacing: -0.02em; line-height: 1.2;
      margin: 30px 0 24px; color: var(--text);
    }

    article h2 em {
      font-family: var(--font-serif);
      font-style: italic; color: var(--accent);
    }

    article strong { color: var(--accent); font-weight: 600; }
    article em { font-style: italic; }

    article hr {
      border: none;
      border-top: 1px solid var(--border-soft);
      margin: 24px auto; width: 80px;
    }

    article ul { margin: 0 0 24px 0; padding-left: 24px; }
    article ul li { margin-bottom: 12px; color: var(--text); }

    .post-teaser {
      font-family: var(--font-serif);
      font-style: italic;
      font-size: 1.2rem;
      color: var(--text-dim);
      text-align: center;
      margin-top: 8px;
    }

    .bio {
      margin-top: 64px; padding: 32px;
      border: 1px solid var(--border-soft);
      background: var(--bg-2); border-radius: 6px;
      font-size: 0.95rem; color: var(--text-dim);
      font-style: italic;
    }

    .bio strong { color: var(--text); font-weight: 600; }

    .post-footer {
      border-top: 1px solid var(--border-soft);
      padding: 48px 0; text-align: center;
    }

    .post-footer-label {
      font-family: var(--font-mono); font-size: 12px;
      color: var(--text-faint);
      text-transform: uppercase; letter-spacing: 0.15em;
      margin-bottom: 16px;
    }

    .post-footer-links {
      display: flex; gap: 24px;
      justify-content: center; flex-wrap: wrap;
      font-family: var(--font-mono); font-size: 14px;
    }

    .post-footer-links a { color: var(--text-dim); }
    .post-footer-links a:hover { color: var(--accent); text-decoration: none; }

    footer {
      border-top: 1px solid var(--border-soft);
      padding: 32px 0;
      font-family: var(--font-mono); font-size: 12px;
      color: var(--text-faint);
    }

    footer .container {
      display: flex; justify-content: space-between;
      align-items: center; flex-wrap: wrap; gap: 16px;
    }
  </style>
</head>
<body>

  <nav>
    <div class="container">
      <a href="/" class="logo">
        <span class="dot"></span>
        RNVizion
      </a>
      <div class="nav-links" id="nav-links">
        <a href="/#about">About</a>
        <a href="/#stack">Stack</a>
        <a href="/#work">Work</a>
        <a href="/blog/" class="active">Blog</a>
        <a href="/#contact">Contact</a>
      </div>
      <button class="nav-toggle" id="nav-toggle" aria-label="Toggle menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </div>
  </nav>

  <main>

    <header class="article-header">
      <div class="read-container">
        <div class="article-meta">
          <span class="accent">●</span> June 22, 2026 · ~3 min read
        </div>
        <h1>Lazy in the <em>Right Way</em> Is Leverage</h1>
        <p class="article-subtitle">I built a machine to publish my blog, and the first thing it did was tell me no.</p>
        <div class="byline">
          <span>by Christian Smith</span>
          <span class="byline-divider"></span>
          <span>RNVizion</span>
        </div>
      </div>
    </header>

    <article>
      <div class="read-container">

        <p>I told a machine to publish a post, and it refused.</p>

        <p>Not an error. Not a crash. A decision. I sent a post; it came back and told me, in plain words, the post was missing what it needed and it wouldn&rsquo;t ship something broken. I sat with that, a bit longer than I&rsquo;d like to admit. I built that refusal myself, that same afternoon; it still caught me off guard to watch it hold the line.</p>

        <p>Let me back up.</p>

        <p>I publish to my own site by hand, and publishing is more steps than it sounds. Write the post. Generate the little card that shows it on the index. Check that the post carries the right tags in its head, the ones the feed reads to know the thing exists. Insert the card at the top of the list, newest first. Push. None of that is hard; what it is, is the kind of repetitive that doesn&rsquo;t tax you so much as wear you, the same trivial moves every time, each a quiet chance to fat-finger something and not notice for a week.</p>

        <hr />

        <p>Here&rsquo;s the part I want to sit on. There are two ways to be lazy about a repetitive chore.</p>

        <p>The first is to keep doing it by hand, because it&rsquo;s &ldquo;only a few minutes,&rdquo; and a few minutes never feels worth fixing. That&rsquo;s the lazy that wins today and loses every day after; you save one afternoon and pay the few minutes forever.</p>

        <p>The second is to spend the time building the thing that does the process for you, turning lost time into margin. That&rsquo;s lazy too; I&rsquo;m not dressing it up as discipline. It&rsquo;s just laziness aimed at the future instead of the present: maximum economy of effort, measured across every post I&rsquo;ll ever publish instead of only the next one.</p>

        <p>I built the second kind.</p>

        <p>Both share the same drive: do less. The difference is direction. Aimed at right now, &ldquo;do less&rdquo; keeps you stuck with the chore. Aimed at the future, &ldquo;do less&rdquo; is the engine behind every tool anyone has ever made. Same instinct, opposite fruit.</p>

        <p>And here&rsquo;s what wasn&rsquo;t true a few years ago: the future-facing kind of lazy just got cheap. What I built in an afternoon would have been a week of work not long ago, easily more. The slow, one-time investment that buys you out of the fast, repetitive forever, the trade that used to be too expensive to bother with, now costs an afternoon. Speed didn&rsquo;t cut my work; it cut the price of ending the chore for good.</p>

        <p>That&rsquo;s the leverage. Not the machine doing my thinking. The machine letting me do my thinking once and keep the result.</p>

        <hr />

        <p>Which brings me back to the post it refused.</p>

        <p>I didn&rsquo;t teach it to publish so much as to judge. I taught it what a good post needs, and to refuse anything short of it: does this have its tags, its card, its place in the list, and if something&rsquo;s missing, don&rsquo;t ship it. One time, with a clear head. Now it runs that judgment on every post, including the ones I&rsquo;d wave through past midnight, tired and just wanting the thing live. The refusal isn&rsquo;t the machine overruling me. It&rsquo;s me, from a better moment &mdash; standing watch over me at a weaker one.</p>

        <p>I did the slow work once; it does the fast work forever, carefully.</p>

        <p>That&rsquo;s the whole trick, and it has nothing to do with working hard. <strong>Lazy in the right way is leverage.</strong></p>

        <p class="post-teaser">Next: an assistant that earns trust by knowing when to say &ldquo;I don&rsquo;t know.&rdquo;</p>

        <div class="bio">
          <strong>Christian Smith</strong> (RNVizion) is a Python developer, AR/VR Sales &amp; Support Specialist at Meta, and a self-described modern-day Renaissance man. He builds desktop tools, writes fiction, makes art, and is figuring out the rest as he goes. Find his work at <a href="https://rnvizion.dev">rnvizion.dev</a>.
        </div>

      </div>
    </article>

    <div class="post-footer">
      <div class="read-container">
        <div class="post-footer-label">Keep reading</div>
        <div class="post-footer-links">
          <a href="/blog/">← All posts</a>
          <a href="/">Home</a>
          <a href="/#work">My work</a>
          <a href="https://github.com/RNVizion" target="_blank" rel="noopener">GitHub</a>
        </div>
      </div>
    </div>

  </main>

  <footer>
    <div class="container">
      <div>© <span id="year"></span> Christian Smith · RNVizion</div>
      <div><a href="/resume/">Résumé</a> · Crafted with care in Washington, DC</div>
    </div>
  </footer>

  <script>
    document.getElementById('year').textContent = new Date().getFullYear();

    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    navToggle.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      navToggle.classList.toggle('open', open);
      navToggle.setAttribute('aria-expanded', open);
    });
    navLinks.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        navLinks.classList.remove('open');
        navToggle.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    });
  </script>
</body>
</html>
POST_EOF

echo "==> Verifying file and required tags"
ls -la "$SITE/blog/$SLUG/"
for tag in 'og:url' 'article:published_time' '<article'; do
  if grep -q "$tag" "$SITE/blog/$SLUG/index.html"; then
    echo "    ok: $tag"
  else
    echo "    MISSING: $tag"
  fi
done
if [ ! -f "$SITE/scripts/generate_card.py" ]; then
  echo "    WARNING: scripts/generate_card.py not in the clone; generate_card will fail"
fi

echo "==> Dry run via the agent"
cd "$AGENT"
python agent.py "Publish the post at blog/$SLUG/ as a dry run."

echo
echo "============================================================"
echo "If the dry run printed the card with no errors, ship it:"
echo "    bash publish_sloth.sh ship"
echo "============================================================"
