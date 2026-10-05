#!/usr/bin/env python3
"""Fill the landing page's contents block from the rendered book.

Reads chapter titles + anchors from _render/<lang>/book.html, part labels
and order from chapters/_order.txt, and the book title from build_book; writes
the landing page with the generated regions regenerated. A chapter whose anchor
is missing from the render aborts the build, so the landing page cannot drift
from the book.

Generated regions (markers in tools/index.html):
  <!--AL-META:BEGIN-->  <head> identity: title, description, share-card tags
  <!--AL-META:END-->
  <!--AL-TOC:BEGIN-->   the contents block (parts + chapters)
  <!--AL-TOC:END-->
  <!--AL-BRAND-->       the topbar brand link

Run: python3 tools/make_index.py            (after a render)
"""

import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_book as book  # noqa: E402  (same-directory helper)

BEGIN = "<!--AL-TOC:BEGIN-->"
END = "<!--AL-TOC:END-->"
META_BEGIN = "<!--AL-META:BEGIN-->"
META_END = "<!--AL-META:END-->"
BRAND = "<!--AL-BRAND-->"
SECTION_RE = re.compile(
        r'<section id="([^"]+)" class="level\d[^"]*">\s*<h\d[^>]*>(.*?)</h\d>', re.S
)


def rendered_titles(path):
        """{anchor id: plain-text heading} for every rendered section."""
        source = Path(path).read_text(encoding="utf-8")
        out = {}
        for anchor, raw in SECTION_RE.findall(source):
                text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
                out.setdefault(anchor, " ".join(text.split()))
        return out


def toc(en_html):
        """[(part, [(href, title), ...]), ...] in book order."""
        titles = rendered_titles(en_html)
        parts, missing = [], []
        for raw in book.order():
                if raw.startswith("PART"):
                        _, en, fr = (x.strip() for x in raw.split("|"))
                        parts.append({"en": en, "fr": fr, "chapters": []})
                else:
                        slug = raw.split()[1][:-4]
                        src = Path(book.CH, slug + ".qmd").read_text(encoding="utf-8")
                        keep, _, _ = book.chapter_titles(book.dedup_ids(src.rstrip()), slug)
                        found = [i for i in sorted(keep or ()) if i in titles]
                        if len(found) != 1:
                                ids = ", ".join(sorted(keep or ())) or "no id"
                                missing.append(f"{slug} ({ids})")
                                continue
                        parts[-1]["chapters"].append((f"en/book.html#{found[0]}", titles[found[0]]))
        if missing:
                sys.exit(f"make_index: chapter anchors not found in render: {'; '.join(missing)}")
        if not parts or any(not p["chapters"] for p in parts):
                sys.exit("make_index: a PART has no rendered chapter — check chapters/_order.txt")
        return parts


def fragment(parts):
        out = ['      <div class="parts">']
        for p in parts:
                out.append('        <section class="part">')
                out.append(f"          <p>{html.escape(p['en'])}<small>{html.escape(p['fr'])}</small></p>")
                out.append('          <ul class="chapters">')
                for href, title in p["chapters"]:
                        out.append(
                                f'            <li><a href="{href}">{html.escape(title)}</a></li>'
                        )
                out.append("          </ul>")
                out.append("        </section>")
        out.append("      </div>")
        return "\n".join(out)


def meta_block():
        """Landing-page identity: title, description, share-card tags."""
        title, desc = book.TITLE_EN, book.DESCRIPTION_EN
        return "\n".join(
                [
                        f"    <title>{title}</title>",
                        f'    <meta name="description" content="{desc}" />',
                        '    <meta property="og:type" content="website" />',
                        f'    <meta property="og:title" content="{title}" />',
                        f'    <meta property="og:description" content="{desc}" />',
                        f'    <meta property="og:url" content="{book.SITE}" />',
                        '    <meta property="og:image" content="og-card.png" />',
                        f'    <meta property="og:image:alt" content="{title} — run, fine-tune, serve, govern" />',
                        '    <meta name="twitter:card" content="summary_large_image" />',
                ]
        )


def splice(text, begin, end, body, indent):
        """Replace the region between two markers with generated markup."""
        if begin not in text or end not in text:
                sys.exit(f"make_index: {begin} / {end} missing from the template")
        head, rest = text.split(begin, 1)
        _, tail = rest.split(end, 1)
        return head + begin + "\n" + body + "\n" + indent + end + tail


def main():
        ap = argparse.ArgumentParser(description=__doc__)
        ap.add_argument("--en", default="_render/en/book.html", help="rendered book")
        ap.add_argument("--template", default="tools/index.html")
        ap.add_argument("--out", default="_site/index.html")
        args = ap.parse_args()

        tpl = Path(args.template).read_text(encoding="utf-8")
        if BRAND not in tpl:
                sys.exit(f"make_index: {args.template} lacks {BRAND}")

        parts = toc(args.en)
        out = splice(tpl, META_BEGIN, META_END, meta_block(), "    ")
        out = splice(out, BEGIN, END, fragment(parts), "      ")
        out = out.replace(BRAND, f'<a class="brand" href="./">{book.BRAND_EN}</a>')
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out, encoding="utf-8")
        chapters = sum(len(p["chapters"]) for p in parts)
        print(f"index: {chapters} chapters in {len(parts)} parts -> {args.out}")


if __name__ == "__main__":
        main()
