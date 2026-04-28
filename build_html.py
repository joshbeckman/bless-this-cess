"""Combine all newsletter markdown files into a single browseable HTML page."""
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
NEWSLETTERS = ROOT / "newsletters"
OUT = ROOT / "lost-lake-cookbook.html"

CSS = """
:root {
  --ink: #2b2118;
  --paper: #fbf6ee;
  --accent: #c44536;
  --muted: #8a7a6c;
  --rule: #d9cfc1;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  font-size: 17px;
  line-height: 1.6;
}
.wrap { max-width: 720px; margin: 0 auto; padding: 3rem 1.5rem 6rem; }
header.cover {
  text-align: center;
  padding: 4rem 1.5rem 3rem;
  border-bottom: 2px solid var(--rule);
  margin-bottom: 3rem;
}
header.cover h1 {
  font-size: 2.6rem;
  margin: 0 0 0.5rem;
  letter-spacing: 0.02em;
}
header.cover p {
  margin: 0.25rem 0;
  color: var(--muted);
  font-style: italic;
}
nav.toc {
  background: rgba(255,255,255,0.5);
  border: 1px solid var(--rule);
  padding: 1.5rem 2rem;
  margin: 0 0 3rem;
  border-radius: 4px;
}
nav.toc h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
}
nav.toc ol {
  margin: 0;
  padding-left: 1.25rem;
  columns: 2;
  column-gap: 2rem;
}
nav.toc li { margin: 0.2rem 0; break-inside: avoid; }
nav.toc a { color: var(--ink); text-decoration: none; }
nav.toc a:hover { color: var(--accent); text-decoration: underline; }
nav.toc .date { color: var(--muted); font-size: 0.85em; }

article.issue {
  margin-bottom: 4rem;
  padding-bottom: 3rem;
  border-bottom: 1px solid var(--rule);
}
article.issue:last-child { border-bottom: none; }
article.issue h1 {
  font-size: 2rem;
  margin: 0 0 0.25rem;
  color: var(--accent);
}
article.issue > p:first-of-type em {
  color: var(--muted);
  font-style: normal;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.85em;
}
article.issue h2 {
  font-size: 1.3rem;
  margin: 2.5rem 0 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px dashed var(--rule);
  padding-bottom: 0.4rem;
}
article.issue p { margin: 0.8rem 0; }
article.issue strong { color: var(--accent); }
article.issue img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5rem auto;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
article.issue a {
  color: var(--accent);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
.back-to-top {
  display: block;
  text-align: center;
  margin-top: 2rem;
  font-size: 0.85em;
  color: var(--muted);
}
.back-to-top a { color: var(--muted); text-decoration: none; }
.back-to-top a:hover { color: var(--accent); }

@media print {
  body { background: white; font-size: 11pt; }
  .wrap { max-width: none; padding: 0; }
  nav.toc { break-after: page; }
  article.issue { break-before: page; border: none; padding: 0; margin: 0 0 2rem; }
  article.issue img { max-height: 4in; box-shadow: none; }
  .back-to-top { display: none; }
  a { color: inherit; text-decoration: none; }
}
"""


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def extract_title(md_text: str) -> tuple[str, str]:
    """Pull the H1 and date line off the top of a newsletter markdown."""
    lines = md_text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else "Untitled"
    date = ""
    for ln in lines[1:5]:
        m = re.match(r"\*(\d{4}-\d{2}-\d{2})\*", ln.strip())
        if m:
            date = m.group(1)
            break
    return title, date


def render_issue(path: Path) -> tuple[str, str, str, str]:
    """Return (slug, title, date, body_html) for a newsletter file."""
    md_text = path.read_text(encoding="utf-8")
    title, date = extract_title(md_text)
    # Strip the H1 + date from body — we render those ourselves with the slug anchor
    body_md = re.sub(
        r"\A#\s.+\n\n\*\d{4}-\d{2}-\d{2}\*\n\n", "", md_text, count=1
    )
    body_html = markdown.markdown(
        body_md, extensions=["extra", "sane_lists", "nl2br"]
    )
    # Images in markdown are relative to newsletters/, but the combined HTML lives at the project root
    body_html = body_html.replace('src="../images/', 'src="images/')
    slug = slugify(path.stem)
    return slug, title, date, body_html


def main():
    files = sorted(NEWSLETTERS.glob("*.md"))
    issues = [render_issue(p) for p in files]

    toc_items = "\n".join(
        f'<li><a href="#{slug}">{title}</a> <span class="date">{date}</span></li>'
        for slug, title, date, _ in issues
    )

    article_blocks = []
    for slug, title, date, body in issues:
        article_blocks.append(
            f'<article class="issue" id="{slug}">\n'
            f'<h1>{title}</h1>\n'
            f'<p><em>{date}</em></p>\n'
            f"{body}\n"
            f'<p class="back-to-top"><a href="#top">↑ back to contents</a></p>\n'
            f"</article>"
        )
    articles = "\n\n".join(article_blocks)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lost Lake Community Thread — Cookbook</title>
<style>{CSS}</style>
</head>
<body id="top">
<div class="wrap">
<header class="cover">
<h1>Lost Lake Community Thread</h1>
<p>Recipes, stories, and ephemera from a Chicago tiki bar in quarantine</p>
<p>March – May 2020</p>
</header>
<nav class="toc">
<h2>Contents</h2>
<ol>
{toc_items}
</ol>
</nav>
{articles}
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.name} ({len(html):,} chars, {len(issues)} issues)")


if __name__ == "__main__":
    main()
