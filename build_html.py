"""Combine all newsletter markdown files into a single browseable HTML page."""
import re
from pathlib import Path

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).parent
NEWSLETTERS = ROOT / "newsletters"
OUT = ROOT / "index.html"

CSS = """
:root {
  --ink: #2b2118;
  --paper: #fbf6ee;
  --accent: #c44536;
  --muted: #8a7a6c;
  --rule: #d9cfc1;
  --card: #fffaf0;
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
nav.toc .recipe-link {
  display: block;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed var(--rule);
  column-span: all;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-size: 0.9rem;
}

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

.recipe {
  background: var(--card);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--accent);
  border-radius: 4px;
  margin: 2rem 0;
  padding: 1.5rem 1.75rem;
  display: grid;
  grid-template-columns: minmax(180px, 1fr) 2fr;
  gap: 1.25rem 1.75rem;
  break-inside: avoid;
  page-break-inside: avoid;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.recipe .recipe-title {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 1.35rem;
  color: var(--accent);
  letter-spacing: 0.01em;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.5rem;
}
.recipe .recipe-desc {
  grid-column: 1 / -1;
  margin: 0;
  font-style: italic;
  color: #4a3a2c;
  font-size: 0.95rem;
}
.recipe .ingredients {
  list-style: none;
  margin: 0;
  padding: 0;
  font-family: "Iowan Old Style", Georgia, serif;
  font-size: 0.95rem;
  line-height: 1.5;
}
.recipe .ingredients li {
  padding: 0.3rem 0;
  border-bottom: 1px dotted var(--rule);
}
.recipe .ingredients li:last-child { border-bottom: none; }
.recipe .ingredients strong { color: var(--ink); }
.recipe .ingredients .ing-section {
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.75em;
  color: var(--muted);
  margin-right: 0.4em;
}
.recipe .method {
  font-style: italic;
  color: #4a3a2c;
  line-height: 1.65;
}
.recipe .method em { font-style: normal; }
.recipe .method p { margin: 0 0 0.75rem; }
.recipe .method p:last-child { margin-bottom: 0; }

@media (max-width: 600px) {
  .recipe { grid-template-columns: 1fr; }
  .recipe .recipe-title { padding-bottom: 0.4rem; }
}

section.recipe-index {
  margin-top: 5rem;
  padding-top: 3rem;
  border-top: 2px solid var(--rule);
  break-before: page;
}
section.recipe-index h2 {
  font-size: 1.6rem;
  margin: 0 0 1.5rem;
  text-align: center;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}
section.recipe-index ol {
  columns: 2;
  column-gap: 2.5rem;
  padding-left: 1.25rem;
  margin: 0;
}
section.recipe-index li {
  margin: 0.3rem 0;
  break-inside: avoid;
  padding-right: 0.5rem;
}
section.recipe-index a {
  color: var(--ink);
  text-decoration: none;
}
section.recipe-index a:hover { color: var(--accent); text-decoration: underline; }
section.recipe-index .issue-ref {
  color: var(--muted);
  font-size: 0.8em;
  display: block;
  margin-top: 0.1rem;
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
  .recipe {
    box-shadow: none;
    background: #fff;
    border: 1px solid #999;
    border-left: 3px solid #444;
  }
  .recipe .recipe-title { color: #000; }
  section.recipe-index { break-before: page; }
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


def split_by_br(p: Tag) -> list[list]:
    """Split a paragraph's children into segments separated by <br/> tags."""
    segments: list[list] = [[]]
    for child in p.children:
        if isinstance(child, Tag) and child.name == "br":
            segments.append([])
        else:
            segments[-1].append(child)
    return segments


def segment_text(segment: list) -> str:
    return "".join(
        str(n) if isinstance(n, NavigableString) else n.get_text() for n in segment
    ).strip()


def segment_html(segment: list) -> str:
    return "".join(str(n) for n in segment).strip()


def first_meaningful(segment: list):
    for n in segment:
        if isinstance(n, NavigableString):
            if n.strip():
                return n
        else:
            return n
    return None


# Ingredient lines virtually always start with a quantity glyph (digit or fraction).
INGREDIENT_LEAD = re.compile(r"^[\s\W]*[\d¼½¾⅓⅔⅛⅜⅝⅞]")
SECTION_METHOD = {"directions", "method", "instructions", "preparation", "to make"}
SECTION_OTHER = {"equipment", "notes", "garnish", "optional"}
STEP_LEAD = re.compile(r"^[\s]*[-•*]\s*\S")


def looks_like_ingredient(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    return bool(INGREDIENT_LEAD.match(text))


def non_empty(segments: list) -> list:
    return [s for s in segments if segment_text(s)]


def is_recipe_paragraph(p: Tag) -> bool:
    """Recipe = <p> starting with a <strong> title and structured ingredient lines.

    The original heuristic required the last segment to be italic (the method).
    That rejects recipes that lead with an italic description and end with a
    plain-text method (Vol 5 style). Relax to: title + <strong>, plus either
    italic somewhere in the body or ≥2 ingredient-shaped lines.
    """
    segments = non_empty(split_by_br(p))
    if len(segments) < 3:
        return False
    head = first_meaningful(segments[0])
    if not (isinstance(head, Tag) and head.name == "strong"):
        return False
    # The first segment may carry a parenthetical after the <strong> title
    # (e.g., "**Dalgona coffee** (one serving)"). Only require that the
    # paragraph leads with bold; the strong's text is the title.
    middle = segments[1:]
    has_em = any(
        any(isinstance(n, Tag) and n.name == "em" for n in seg) for seg in middle
    )
    ingredient_count = sum(1 for s in middle if looks_like_ingredient(segment_text(s)))
    if has_em and ingredient_count >= 1:
        return True
    if ingredient_count >= 2:
        return True
    return False


def extract_recipe(p: Tag) -> dict:
    segments = non_empty(split_by_br(p))
    title = first_meaningful(segments[0]).get_text().strip()

    body_start = 1
    description_html = None
    if len(segments) > 1:
        seg1_html = segment_html(segments[1])
        seg1_text = segment_text(segments[1])
        m = re.fullmatch(r"<em>(.*)</em>", seg1_html, flags=re.DOTALL)
        if m and not looks_like_ingredient(seg1_text):
            description_html = m.group(1)
            body_start = 2

    # Method = trailing segments that don't look like ingredients (italic prose
    # OR plain-text instructions, possibly across multiple lines such as a
    # closing remark). Walk backwards from end and stop at the first ingredient.
    # If the whole tail is ingredients (mug-cake style), leave method empty —
    # a continuation paragraph may carry it.
    end = len(segments)
    method_start = end
    while method_start > body_start and not looks_like_ingredient(
        segment_text(segments[method_start - 1])
    ):
        method_start -= 1

    # Require at least one ingredient between body_start and method_start.
    method_html = ""
    if method_start > body_start and method_start < end:
        parts = []
        for s in segments[method_start:end]:
            h = segment_html(s)
            m = re.fullmatch(r"<em>(.*)</em>", h, flags=re.DOTALL)
            if m:
                h = m.group(1)
            parts.append(h)
        method_html = "<br/>".join(parts)
        end = method_start

    ingredients = [segment_html(s) for s in segments[body_start:end]]

    return {
        "title": title,
        "description_html": description_html,
        "ingredients": ingredients,
        "method_html": method_html,
    }


def detect_section_header(p: Tag) -> tuple[str | None, list]:
    """If the paragraph leads with a section header (bold or plain text),
    return (section_name, body_segments_after_header). Otherwise (None, [])."""
    segments = non_empty(split_by_br(p))
    if not segments:
        return None, []
    head = first_meaningful(segments[0])
    if isinstance(head, Tag) and head.name == "strong":
        label = (
            head.get_text().strip().lower().split("(")[0].strip().rstrip(":")
        )
        if label in SECTION_METHOD:
            return "method", segments[1:]
        if label in SECTION_OTHER:
            return label, segments[1:]
        return None, []
    first_text = segment_text(segments[0]).strip().lower().rstrip(":")
    if first_text in SECTION_METHOD:
        return "method", segments[1:]
    if first_text in SECTION_OTHER:
        return first_text, segments[1:]
    return None, []


def append_method(recipe: dict, segments: list) -> None:
    parts = []
    for s in segments:
        line = segment_html(s)
        line = re.sub(r"^[-•*]\s*", "", line).strip()
        if line:
            parts.append(line)
    if not parts:
        return
    block = "<br/>".join(parts)
    if recipe["method_html"]:
        recipe["method_html"] += "<br/><br/>" + block
    else:
        recipe["method_html"] = block


def append_ingredients(recipe: dict, segments: list, label: str | None = None) -> None:
    for s in segments:
        text = segment_text(s)
        if not text:
            continue
        html = segment_html(s)
        if label:
            recipe["ingredients"].append(
                f'<span class="ing-section">{label}:</span> {html}'
            )
        else:
            recipe["ingredients"].append(html)


def continuation_section(p, current: str, method_via_header: bool) -> str | None:
    """What section does this sibling paragraph contribute to (if any)?

    Method-extension via prose requires that we've already crossed an explicit
    "Directions"/"Method"/etc. header. Otherwise narrative paragraphs after a
    recipe with an inline italic method (e.g., the transitional prose after
    Lil Saint Nog) would be wrongly swallowed into the method block.
    """
    if not isinstance(p, Tag) or p.name != "p":
        return None
    if p.find("img"):
        return None
    section, _body = detect_section_header(p)
    if section is not None:
        return section
    if p.find("strong"):
        return None
    segments = non_empty(split_by_br(p))
    if not segments:
        return None
    if current == "method" and method_via_header:
        return "method"
    if current != "method" and all(
        looks_like_ingredient(segment_text(s)) for s in segments
    ):
        return current
    return None


def absorb(recipe: dict, p: Tag, section: str) -> None:
    header_section, body = detect_section_header(p)
    if header_section is not None:
        segments = body
    else:
        segments = non_empty(split_by_br(p))
    if section == "method":
        append_method(recipe, segments)
    elif section in SECTION_OTHER:
        append_ingredients(recipe, segments, label=section)
    else:
        append_ingredients(recipe, segments)


def render_recipe_card(recipe: dict, slug: str) -> str:
    ingredients_html = "\n".join(f"<li>{ing}</li>" for ing in recipe["ingredients"])
    desc = ""
    if recipe.get("description_html"):
        desc = f'<p class="recipe-desc">{recipe["description_html"]}</p>'
    method_block = ""
    if recipe["method_html"]:
        method_block = f'<div class="method"><p>{recipe["method_html"]}</p></div>'
    return (
        f'<div class="recipe" id="{slug}">'
        f'<h3 class="recipe-title">{recipe["title"]}</h3>'
        f"{desc}"
        f'<ul class="ingredients">{ingredients_html}</ul>'
        f"{method_block}"
        f"</div>"
    )


def transform_recipes(
    body_html: str, issue_slug: str, issue_title: str, collected: list
) -> str:
    soup = BeautifulSoup(body_html, "html.parser")
    seen_slugs: set[str] = set()
    for p in list(soup.find_all("p")):
        # `p` may have been removed by an earlier absorption pass.
        if p.parent is None:
            continue
        if not is_recipe_paragraph(p):
            continue
        recipe = extract_recipe(p)

        # Absorb continuation paragraphs (mug-cake / dalgona style: a recipe's
        # ingredients/method split across multiple <p> blocks, sometimes with
        # bold section headers like "Equipment", "Directions", "Optional").
        # Track the current section so once a "Directions" header appears,
        # subsequent prose paragraphs continue extending the method.
        absorbed = []
        current_section = "method" if recipe["method_html"] else "ingredients"
        method_via_header = False
        sib = p.find_next_sibling()
        while sib is not None:
            section = continuation_section(sib, current_section, method_via_header)
            if section is None:
                break
            absorb(recipe, sib, section)
            if section == "method":
                # Only mark "method via header" when the absorbed paragraph
                # actually carried a header — not when prose extends an
                # already-headered method.
                header_section, _ = detect_section_header(sib)
                if header_section == "method":
                    method_via_header = True
            current_section = section
            absorbed.append(sib)
            sib = sib.find_next_sibling()

        base = slugify(recipe["title"])
        rslug = f"recipe-{issue_slug}-{base}"
        i = 2
        while rslug in seen_slugs:
            rslug = f"recipe-{issue_slug}-{base}-{i}"
            i += 1
        seen_slugs.add(rslug)
        collected.append(
            {
                "title": recipe["title"],
                "slug": rslug,
                "issue_slug": issue_slug,
                "issue_title": issue_title,
            }
        )
        replacement = BeautifulSoup(render_recipe_card(recipe, rslug), "html.parser")
        p.replace_with(replacement)
        for s in absorbed:
            s.decompose()
    return str(soup)


def render_issue(path: Path, recipes: list) -> tuple[str, str, str, str]:
    md_text = path.read_text(encoding="utf-8")
    title, date = extract_title(md_text)
    body_md = re.sub(r"\A#\s.+\n\n\*\d{4}-\d{2}-\d{2}\*\n\n", "", md_text, count=1)
    body_html = markdown.markdown(
        body_md, extensions=["extra", "sane_lists", "nl2br"]
    )
    body_html = body_html.replace('src="../images/', 'src="images/')
    slug = slugify(path.stem)
    body_html = transform_recipes(body_html, slug, title, recipes)
    return slug, title, date, body_html


def render_recipe_index(recipes: list) -> str:
    if not recipes:
        return ""
    sorted_recipes = sorted(recipes, key=lambda r: r["title"].lower())
    items = []
    for r in sorted_recipes:
        items.append(
            f'<li><a href="#{r["slug"]}">{r["title"]}</a>'
            f'<span class="issue-ref">{r["issue_title"]}</span></li>'
        )
    return (
        '<section class="recipe-index" id="recipe-index">\n'
        "<h2>Recipe Index</h2>\n"
        "<ol>\n" + "\n".join(items) + "\n</ol>\n"
        "</section>"
    )


def main():
    files = sorted(NEWSLETTERS.glob("*.md"))
    recipes: list = []
    issues = [render_issue(p, recipes) for p in files]

    toc_items = "\n".join(
        f'<li><a href="#{slug}">{title}</a> <span class="date">{date}</span></li>'
        for slug, title, date, _ in issues
    )
    if recipes:
        toc_items += (
            '\n<li class="recipe-link">'
            '<a href="#recipe-index">Recipe Index →</a></li>'
        )

    article_blocks = []
    for slug, title, date, body in issues:
        article_blocks.append(
            f'<article class="issue" id="{slug}">\n'
            f"<h1>{title}</h1>\n"
            f"<p><em>{date}</em></p>\n"
            f"{body}\n"
            f'<p class="back-to-top"><a href="#top">↑ back to contents</a></p>\n'
            f"</article>"
        )
    articles = "\n\n".join(article_blocks)
    recipe_index_html = render_recipe_index(recipes)

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
{recipe_index_html}
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(
        f"wrote {OUT.name} ({len(html):,} chars, {len(issues)} issues, "
        f"{len(recipes)} recipes)"
    )


if __name__ == "__main__":
    main()
