#!/usr/bin/env python3
"""Fill the landing page from the generated book config and the render.

Reads chapters/_order.txt for parts and chapter order, and _render/<lang>/ for
each chapter's rendered title (Quarto's chapter number included). A chapter
whose rendered page is missing aborts the build, so the landing page cannot
drift from the book.

Generated regions (markers in tools/index.html):
  <!--AL-META:BEGIN-->  <head> identity: title, description, share-card tags
  <!--AL-META:END-->
  <!--AL-TOC:BEGIN-->   the contents block (parts + chapters)
  <!--AL-TOC:END-->
  <!--AL-BRAND-->       the topbar brand link

Run: tools/render.sh en && python3 tools/make_index.py
"""

import argparse
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_book as book  # noqa: E402  (same-directory helper)

BEGIN = "<!--AL-TOC:BEGIN-->"
END = "<!--AL-TOC:END-->"
META_BEGIN = "<!--AL-META:BEGIN-->"
META_END = "<!--AL-META:END-->"
BRAND = "<!--AL-BRAND-->"
H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
NUMBER = re.compile(r'<span class="chapter-number">([^<]+)</span>')
TITLE = re.compile(r'<span class="chapter-title">(.*?)</span>', re.S)
TAG = re.compile(r"<[^>]+>")


def plain(raw):
        return " ".join(html.unescape(TAG.sub(" ", raw)).split())


def page_title(path):
        """'1. The rise of local AI' from a rendered chapter page."""
        raw = H1.search(pathlib.Path(path).read_text(encoding="utf-8"))
        if not raw:
                sys.exit(f"make_index: no <h1> in {path}")
        head = raw.group(1)
        number, title = NUMBER.search(head), TITLE.search(head)
        if number and title:
                return f"{number.group(1)}. {plain(title.group(1))}"
        return plain(head)


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


def toc(render, lang):
        """[(en label, fr label, [(href, title), ...]), ...] in book order."""
        parts, missing = [], []
        for kind, a, b, *_ in book.order():
                if kind == "PART":
                        parts.append([a, b, []])
                elif kind == "APPENDICES":
                        parts.append([a, b, []])
                elif kind == "HOME":
                        continue  # the landing page links the home page itself
                else:
                        page = pathlib.Path(render, a[:-4] + ".html")
                        if not page.exists():
                                missing.append(str(page))
                                continue
                        parts[-1][2].append((f"{lang}/{a[:-4]}.html", page_title(page)))
        if missing:
                sys.exit(f"make_index: rendered pages not found: {'; '.join(missing)}")
        if not parts or any(not p[2] for p in parts):
                sys.exit("make_index: a part has no rendered chapter — check chapters/_order.txt")
        return parts


def fragment(parts):
        out = ['      <div class="parts">']
        for en, fr, chapters in parts:
                out.append('        <section class="part">')
                out.append(f"          <p>{html.escape(en)}<small>{html.escape(fr)}</small></p>")
                out.append('          <ul class="chapters">')
                for href, title in chapters:
                        out.append(
                                f'            <li><a href="{href}">{html.escape(title)}</a></li>'
                        )
                out.append("          </ul>")
                out.append("        </section>")
        out.append("      </div>")
        return "\n".join(out)


def splice(text, begin, end, body, indent):
        """Replace the region between two markers with generated markup."""
        if begin not in text or end not in text:
                sys.exit(f"make_index: {begin} / {end} missing from the template")
        head, rest = text.split(begin, 1)
        _, tail = rest.split(end, 1)
        return head + begin + "\n" + body + "\n" + indent + end + tail


def main():
        ap = argparse.ArgumentParser(description=__doc__)
        ap.add_argument("--render", default="_render/en", help="rendered book directory")
        ap.add_argument("--lang", default="en", help="link prefix for chapter pages")
        ap.add_argument("--template", default="tools/index.html")
        ap.add_argument("--out", default="_site/index.html")
        args = ap.parse_args()

        tpl = pathlib.Path(args.template).read_text(encoding="utf-8")
        if BRAND not in tpl:
                sys.exit(f"make_index: {args.template} lacks {BRAND}")

        parts = toc(args.render, args.lang)
        out = splice(tpl, META_BEGIN, META_END, meta_block(), "    ")
        out = splice(out, BEGIN, END, fragment(parts), "      ")
        out = out.replace(BRAND, f'<a class="brand" href="./">{book.BRAND_EN}</a>')
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(out, encoding="utf-8")
        chapters = sum(len(p[2]) for p in parts)
        print(f"index: {chapters} chapters in {len(parts)} parts -> {args.out}")


if __name__ == "__main__":
        main()
