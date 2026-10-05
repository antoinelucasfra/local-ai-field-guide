#!/usr/bin/env python3
"""Build the book volume + per-chapter standalone documents + _quarto.yml.

Sources : chapters/*.qmd fragments + chapters/_order.txt   (the only edited files)
Outputs : .book.qmd, .ch-<slug>.qmd   (hidden root files, gitignored)
          _quarto.yml                  (regenerated -> never out of sync)

Id convention: the second occurrence of an {#id} in a fragment (the FR heading)
is rewritten {#id-fr}; langsel.lua renames it back after filtering, so pandoc
never sees duplicates and final anchors stay canonical (#id).

Run automatically as project pre-render; manual: python3 tools/build_book.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _open(path, mode="r"):
        # generator inputs must fail loud — but with a readable message
        # (encoding is explicit: chapters are UTF-8, Windows defaults aren't)
        try:
                return open(path, mode, encoding="utf-8")
        except OSError as e:
                sys.exit(f"build_book: {e}")


CH = os.path.join(ROOT, "chapters")

# Book identity — the single source. tools/make_index.py reads these for the
# landing page, so a rename is one edit here.
TITLE_EN = "The Local AI Field Guide"
TITLE_FR = "Le guide de terrain de l'IA locale"
BRAND_EN = "The <em>Local AI Field Guide</em>"
DESCRIPTION_EN = (
        "An open, bilingual field guide to running open-weight language models on your "
        "own hardware: choosing models, inference, fine-tuning, agents, RAG, serving, "
        "evaluation and GDPR. Available in French."
)
SITE = "https://antoinelucasfra.github.io/local-ai-field-guide/"
REPO = "https://github.com/antoinelucasfra/local-ai-field-guide"

FRONT = """---
author: "Support IA — LocalAI"
date: today
filters:
  - langsel{ext_filters}
  - at: post-quarto
    path: _extensions/andrewheiss/wordcount/wordcount.lua
extensions:
  linkrot:
    fail-on-error: false
    timeout: 8
    cache-results: true
title: "doc"
title-en: "{ten}"
title-fr: "{tfr}"
format-links: false
format:
{fmt}
---

"""

EXT_FILTERS = """
  - include-code-files
  - passage-xref
  - details
  - code-window
  - lightbox
  - linkrot
  - wordcount"""

BOOK_FMT = """  html:
    output-file: book.html
    toc: true
    toc-depth: 3
    theme:
      light: [cosmo, al-brand-light, al-brand-book.scss]
      dark: [cosmo, al-brand-dark, al-brand-book.scss]
    include-in-header: tools/book-head.html
    embed-resources: true
    lightbox: auto
  epub:
    output-file: book.epub
    toc: true
  docx:
    output-file: book.docx
    toc: true
  typst:
    output-file: book.pdf
    papersize: a4
    margin:
      x: 2cm
      y: 2cm
    toc: true"""

# Each chapter is emitted as TWO hidden docs so no single document ever
# declares both html-family formats (quarto renders a doc's formats
# concurrently; html + revealjs race on the shared <slug>_files dir and
# corrupt embed-resources). Split docs = parallel-safe plain `quarto render`.
SLIDES_FMT = """  revealjs:
    output-file: {outfile}
    theme: [default, al-brand-slides.scss]
    slide-number: c/t
    hash-type: number
    progress: true
    scrollable: true
    smaller: true
    highlight-style: github
    embed-resources: true"""

DOC_FMT = """  typst:
    output-file: {slug}.pdf
    papersize: a4
    margin:
      x: 1.8cm
      y: 1.8cm
  docx:
    output-file: {slug}.docx
    toc: true
  html:
    output-file: {slug}.html
    toc: true
    toc-depth: 2
    theme:
      light: [cosmo, al-brand-light, al-brand-book.scss]
      dark: [cosmo, al-brand-dark, al-brand-book.scss]
    include-in-header: tools/book-head.html
    embed-resources: true
    lightbox: auto"""

YML = """project:
  type: default
  pre-render: tools/build_book.py
  render:
    - .book.qmd{entries}
profile:
  default: [en]
"""


REPO_SRC = "https://github.com/antoinelucasfra/local-ai-field-guide/blob/main/chapters/"


def order():
        out = []
        with _open(os.path.join(CH, "_order.txt")) as f:
                for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                                out.append(line)
        return out


def dedup_ids(body):
        """Second occurrence of {#id} (the FR heading) becomes {#id-fr}."""
        seen = set()

        def sub(m):
                i = m.group(1)
                if i in seen:
                        return "{#" + i + "-fr}"
                seen.add(i)
                return m.group(0)

        return re.sub(r"\{#([\w-]+)\}", sub, body)


def chapter_titles(body, slug):
        """Chapter titles + title-heading ids in one scan.

        Titles fall back to the slug. Ids are None unless both languages carry
        a titled chapter heading (the welcome page has none).
        """
        ten = tfr = None
        ids = []
        for m in re.finditer(
                r"^[ \t]*:::[ \t]*\{\.(en|fr)\}[ \t]*\n[ \t]*## (.+?) \{#([\w-]+)\}",
                body,
                re.M,
        ):
                lang, title, ident = m.group(1), m.group(2), m.group(3)
                if lang == "en" and ten is None:
                        ten = title
                        ids.append(ident)
                elif lang == "fr" and tfr is None:
                        tfr = title
                        ids.append(ident)
        return (set(ids) if len(ids) == 2 else None), (ten or slug), (tfr or slug)


def demote_sections(body, keep):
        """In the merged volume, demote every heading except the chapter's own
        EN/FR titles one level, so sections nest under their chapter (pandoc
        TOC + PDF outline follow suit)."""
        out = []
        for line in body.split("\n"):
                m = re.match(r"^#{2,4} .*?\{#([\w-]+)\}", line)
                if m and m.group(1) not in keep:
                        line = "#" + line
                out.append(line)
        return "\n".join(out)


def rewrite_foreign_links(body, ids):
        def sub(m):
                return (
                        m.group(0).replace(
                                f"(#{m.group(2)})", f"(book.html#{m.group(2)})"
                        )
                        if m.group(2) not in ids
                        else m.group(0)
                )

        return re.sub(r"\[([^\]]+)\]\(#([\w-]+)\)", sub, body)


def add_standalone_links(body, slug):
        """Links to this chapter's standalone formats, placed directly under
        each language's chapter-title heading instead of the chapter tail."""
        en = (
                f"\n::: {{.dl-strip}}\nThis chapter standalone: "
                f"[slides]({slug}-slides.html) · [PDF]({slug}.pdf) · "
                f"[HTML]({slug}.html) · "
                f"[suggest an edit]({REPO_SRC}{slug}.qmd)\n:::\n"
        )
        fr = (
                f"\n::: {{.dl-strip}}\nCe chapitre seul : "
                f"[diapositives]({slug}-slides.html) · [PDF]({slug}.pdf) · "
                f"[HTML]({slug}.html) · "
                f"[proposer une modification]({REPO_SRC}{slug}.qmd)\n:::\n"
        )
        out = re.sub(
                r"(::: \{\.en\}\n#+[^\n]+\n)", lambda m: m.group(1) + en, body, count=1
        )
        hit_en = out != body
        body2 = re.sub(
                r"(::: \{\.fr\}\n#+[^\n]+\n)", lambda m: m.group(1) + fr, out, count=1
        )
        # no titled language blocks (welcome page): put strips at the very top
        if not (hit_en and body2 != out):
                return en + "\n" + fr + "\n" + body
        return body2


def main():
        slugs, book, slides = [], [], []
        for raw in order():
                if raw.startswith("PART"):
                        _, en, fr = (x.strip() for x in raw.split("|"))
                        book.append(
                                f"::: {{.en}}\n# {en} {{.unnumbered}}\n:::\n\n"
                                f"::: {{.fr}}\n# {fr} {{.unnumbered}}\n:::\n\n"
                        )
                        slides.append(
                                f"# {en} {{.unnumbered}}\n\n# {fr} {{.unnumbered}}\n\n"
                        )
                elif raw.startswith("FILE"):
                        slug = raw.split()[1][:-4]
                        slugs.append(slug)
                        with _open(os.path.join(CH, slug + ".qmd")) as f:
                                # ponytail: single typo rule, replaces the search-replace
                                # extension; (?<!\w) mirrors its %f[%w] frontier so
                                # llama.cpp is untouched.
                                src = re.sub(
                                        r"(?<!\w)lama\.cpp",
                                        "Llama.cpp",
                                        f.read().rstrip(),
                                )
                                slug_body = dedup_ids(src)
                        # presenter notes are for slide decks only — never in the merged volume
                        body = re.sub(
                                r"\n*::: \{\.notes\}.*?\n:::\n?",
                                "",
                                slug_body,
                                flags=re.S,
                        )
                        keep, ten, tfr = chapter_titles(body, slug)
                        if slug == "00-bienvenue":
                                keep = None
                        if keep:
                                body = demote_sections(body, keep)
                        book.append(add_standalone_links(body, slug) + "\n\n")
                        ids = set(re.findall(r"\{#([\w-]+)\}", body))
                        sbody = rewrite_foreign_links(body, ids)
                        # standalone docs: .ch keeps presenter notes (slides), .chh drops them
                        meta = {
                                "ten": ten.replace('"', "'"),
                                "tfr": tfr.replace('"', "'"),
                        }
                        sslug = rewrite_foreign_links(
                                slug_body, set(re.findall(r"\{#([\w-]+)\}", slug_body))
                        )
                        with _open(os.path.join(ROOT, f".ch-{slug}.qmd"), "w") as f:
                                f.write(
                                        FRONT.format(
                                                fmt=SLIDES_FMT.format(
                                                        outfile=f"{slug}-slides.html"
                                                ),
                                                ext_filters=EXT_FILTERS,
                                                **meta,
                                        )
                                        + sslug.rstrip()
                                        + "\n"
                                )
                        slides.append(sslug.rstrip() + "\n\n")
                        with _open(os.path.join(ROOT, f".chh-{slug}.qmd"), "w") as f:
                                f.write(
                                        FRONT.format(
                                                fmt=DOC_FMT.format(slug=slug),
                                                ext_filters=EXT_FILTERS,
                                                **meta,
                                        )
                                        + add_standalone_links(sbody, slug).rstrip()
                                        + "\n"
                                )

        with _open(os.path.join(ROOT, ".book.qmd"), "w") as f:
                f.write(
                        FRONT.format(
                                ten=TITLE_EN,
                                tfr=TITLE_FR,
                                fmt=BOOK_FMT,
                                ext_filters=EXT_FILTERS,
                        )
                        + "".join(book)
                )
        with _open(os.path.join(ROOT, ".book-slides.qmd"), "w") as f:
                f.write(
                        FRONT.format(
                                ten=f"{TITLE_EN} — Slides",
                                tfr=f"{TITLE_FR} — Diapositives",
                                fmt=SLIDES_FMT.format(outfile="book-slides.html"),
                                ext_filters=EXT_FILTERS,
                        )
                        + "".join(slides)
                )
        with _open(os.path.join(ROOT, "_quarto.yml"), "w") as f:
                f.write(
                        YML.replace(
                                "{entries}",
                                "\n    - .book-slides.qmd"
                                + "".join(
                                        f"\n    - .ch-{s}.qmd\n    - .chh-{s}.qmd"
                                        for s in slugs
                                )
                                # site 404 page (GitHub Pages serves _site/404.html)
                                + "\n    - 404.qmd",
                        )
                )
        print(
                f"built .book.qmd + .book-slides.qmd + {len(slugs)}x(.ch,.chh).qmd + _quarto.yml"
        )


if __name__ == "__main__":
        main()
