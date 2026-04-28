"""Scrape Lost Lake Community Thread newsletters into markdown files."""
import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).parent
OUT = ROOT / "newsletters"
IMG = ROOT / "images"
CACHE = ROOT / "cache"

# (date, volume_label, eepurl_id) — collected from the archive listing
ISSUES = [
    ("2020-05-22", "vol-17", "g4xwNj"),
    ("2020-05-15", "vol-16", "g3HmOr"),
    ("2020-05-07", "vol-15", "g2FQZr"),
    ("2020-05-05", "vol-14", "g2mGPn"),
    # Publication labeled both 04/28 and 04/30 as "Volume 12"; we suffix to disambiguate.
    ("2020-04-30", "vol-12b", "g1LqqX"),
    ("2020-04-28", "vol-12a", "g1qIIP"),
    ("2020-04-23", "vol-11", "g0UKDD"),
    ("2020-04-21", "vol-10", "g0Dyzf"),
    # Same publication issue: both 04/14 and 04/16 labeled "Volume 8".
    ("2020-04-16", "vol-08b", "gZ6NQL"),
    ("2020-04-14", "vol-08a", "gZPFf1"),
    ("2020-04-09", "vol-07", "gZkmi9"),
    ("2020-04-07", "vol-06", "gY4HSv"),
    ("2020-04-02", "vol-05", "gYt40H"),
    ("2020-03-31", "vol-04", "gYafVL"),
    ("2020-03-26", "vol-03", "gXlvSH"),
    ("2020-03-24", "vol-02", "gXjStr"),
    ("2020-03-20", "vol-01-welcome", "gWVzRX"),
]


def fetch(eepurl_id: str) -> str:
    cache_path = CACHE / f"{eepurl_id}.html"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    CACHE.mkdir(exist_ok=True)
    req = urllib.request.Request(
        f"https://eepurl.com/{eepurl_id}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    cache_path.write_text(html, encoding="utf-8")
    return html


INLINE_BOLD = {"strong", "b"}
INLINE_ITALIC = {"em", "i"}
BLOCK_BREAK = {"p", "div", "li", "blockquote"}
LIST_TAGS = {"ul", "ol"}


def render(node, out: list[str], in_bold: bool = False, in_italic: bool = False):
    if isinstance(node, NavigableString):
        text = str(node).replace("\xa0", " ")
        # HTML treats text-node whitespace (including newlines) as insignificant
        text = re.sub(r"\s+", " ", text)
        if in_bold and text.strip():
            text = f"**{text.strip()}**"
        elif in_italic and text.strip():
            text = f"*{text.strip()}*"
        out.append(text)
        return
    if not isinstance(node, Tag):
        return
    name = node.name.lower()
    if name in {"script", "style"}:
        return
    if name == "br":
        out.append("\n")
        return
    if name == "a":
        href = node.get("href", "")
        inner: list[str] = []
        for c in node.children:
            render(c, inner, in_bold, in_italic)
        text = "".join(inner).strip()
        if href and text:
            out.append(f"[{text}]({href})")
        else:
            out.append(text)
        return
    if name == "img":
        src = node.get("src", "")
        alt = node.get("alt", "") or ""
        if src:
            out.append(f"\n\n![{alt}]({src})\n\n")
        return
    if name in INLINE_BOLD:
        for c in node.children:
            render(c, out, True, in_italic)
        return
    if name in INLINE_ITALIC:
        for c in node.children:
            render(c, out, in_bold, True)
        return
    if name == "li":
        out.append("\n- ")
        for c in node.children:
            render(c, out, in_bold, in_italic)
        return
    if name in LIST_TAGS:
        out.append("\n")
        for c in node.children:
            render(c, out, in_bold, in_italic)
        out.append("\n")
        return
    if name in BLOCK_BREAK:
        out.append("\n\n")
        for c in node.children:
            render(c, out, in_bold, in_italic)
        out.append("\n\n")
        return
    # Default: just recurse (table, tbody, tr, td, span, etc.)
    for c in node.children:
        render(c, out, in_bold, in_italic)


def normalize_block(block: Tag) -> str:
    out: list[str] = []
    render(block, out)
    text = "".join(out)
    # Merge adjacent bold/italic spans split by whitespace only
    text = re.sub(r"\*\*(\s+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(\s+)\*(?!\*)", r"\1", text)
    # Collapse 3+ newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim trailing whitespace per line
    text = re.sub(r"[ \t]+\n", "\n", text)
    # Trim per-line whitespace while preserving blank lines
    lines = [ln.strip() for ln in text.split("\n")]
    text = "\n".join(lines).strip()
    return text


def is_heading(block_text: str) -> bool:
    """Headings are short, in caps, no markdown formatting beyond bold."""
    plain = re.sub(r"[*_`#\[\]()!]", "", block_text).strip()
    if not plain or len(plain) > 80:
        return False
    if "\n" in plain.strip():
        return False
    letters = [c for c in plain if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return upper_ratio >= 0.7


def heading_text(block_text: str) -> str:
    """Strip markdown formatting/punctuation from a detected heading."""
    text = re.sub(r"\*+", "", block_text)
    text = text.strip().strip("|").strip()
    return text


def is_footer(block_text: str) -> bool:
    return "All rights reserved" in block_text or block_text.startswith("Copyright ©")


def is_intro_branding(block_text: str) -> bool:
    """The 'Lost Lake Community Thread <3' or 'twice-weekly community thread' header."""
    plain = re.sub(r"[*_`#\[\]()!<>]", "", block_text).strip().lower()
    return (
        plain.startswith("lost lake community thread")
        or "twice-weekly community thread" in plain
    )


def download_image(url: str, volume: str, idx: int) -> str | None:
    """Download an image to images/<volume>-<idx>.<ext>, return relative path."""
    IMG.mkdir(exist_ok=True)
    # Determine extension from URL
    ext_match = re.search(r"\.([a-zA-Z0-9]{2,5})(?:\?|$)", url)
    ext = ext_match.group(1).lower() if ext_match else "jpg"
    filename = f"{volume}-{idx:02d}.{ext}"
    path = IMG / filename
    if path.exists():
        return f"../images/{filename}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            path.write_bytes(resp.read())
    except Exception as exc:
        print(f"  image fail {url}: {exc}", file=sys.stderr)
        return None
    return f"../images/{filename}"


def convert_issue(html: str, date: str, volume: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else f"Lost Lake — {volume}"

    # Walk body in document order, picking up text blocks and content images
    body = soup.find("body") or soup
    blocks: list[tuple[str, str]] = []  # (kind, content)
    seen = set()
    img_idx = 0

    # Find all relevant elements in document order
    for el in body.find_all(["td", "div", "img"]):
        if el.name in {"td", "div"} and "mcnTextContent" in (el.get("class") or []):
            text = normalize_block(el)
            if not text or is_intro_branding(text) or is_footer(text):
                continue
            key = re.sub(r"\s+", " ", text)[:120]
            if key in seen:
                continue
            seen.add(key)
            blocks.append(("text", text))
        elif el.name == "img" and "mcnImage" in (el.get("class") or []):
            # Skip the small Lost Lake logo
            try:
                width = float(el.get("width", "0"))
            except ValueError:
                width = 0
            if width < 200:
                continue
            src = el.get("src", "")
            if not src or src in seen:
                continue
            seen.add(src)
            img_idx += 1
            local = download_image(src, volume, img_idx)
            if local:
                blocks.append(("image", local))

    body_parts = []
    for kind, content in blocks:
        if kind == "image":
            body_parts.append(f"![]({content})")
        elif is_heading(content):
            body_parts.append(f"## {heading_text(content)}")
        else:
            body_parts.append(content)

    out = "\n\n".join(body_parts)
    front = f"# {title}\n\n*{date}*\n\n"
    return front + out + "\n"


def main():
    OUT.mkdir(exist_ok=True)
    for date, volume, eep in ISSUES:
        html = fetch(eep)
        try:
            md_text = convert_issue(html, date, volume)
        except Exception as exc:
            print(f"FAIL {date} {volume}: {exc}", file=sys.stderr)
            continue
        path = OUT / f"{date}-{volume}.md"
        path.write_text(md_text, encoding="utf-8")
        print(f"wrote {path.name} ({len(md_text)} chars)")


if __name__ == "__main__":
    main()
