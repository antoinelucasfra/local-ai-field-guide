#!/usr/bin/env python3
"""Build the bilingual Quarto book configuration.

Sources : chapters/*.qmd fragments + chapters/_order.txt (the edited files)
          index.qmd                            (the book home page)
Outputs : _quarto.yml + _quarto-fr.yml           book project config, regenerated
          .ch-<lang>-<slug>.qmd                  revealjs decks (hidden, gitignored)

Id convention: the second occurrence of {#id} in a fragment (the FR heading)
becomes {#id-fr}; langsel.lua renames it back after filtering, so pandoc never
sees duplicate ids and final anchors stay language-independent.

The book itself is a real Quarto book project: chapters, parts and appendices
live in the generated config, and Quarto does the numbering, sidebar, search,
downloads and cross-file links. Only the per-chapter revealjs decks are still
generated here, because a book project renders its chapters, not extra decks.

Run automatically as project pre-render; manual: python3 tools/build_book.py
"""

import glob
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
SUBTITLE_EN = "Run, fine-tune, serve and govern on your own hardware"
SUBTITLE_FR = "Exécuter, affûter, servir et gouverner sur votre propre matériel"
BRAND_EN = "The <em>Local AI Field Guide</em>"
DESCRIPTION_EN = (
        "An open, bilingual field guide to running open-weight language models on your "
        "own hardware: choosing models, inference, fine-tuning, agents, RAG, serving, "
        "evaluation and GDPR. Available in French."
)
DESCRIPTION_FR = (
        "Un guide de terrain ouvert et bilingue pour exécuter des modèles à poids "
        "ouverts sur votre propre matériel : choix des modèles, inférence, "
        "fine-tuning, agents, RAG, service, évaluation et RGPD."
)
SITE = "https://antoinelucasfra.github.io/local-ai-field-guide/"
REPO = "https://github.com/antoinelucasfra/local-ai-field-guide"

# Project-level filter chain, applied to every book format. The decks override
# this with FILTERS_DECK (same minus drop-notes: speaker notes must survive).
FILTERS = """  - langsel
  - include-code-files
  - passage-xref
  - details
  - code-window
  - lightbox
  - tools/drop-notes.lua"""

FILTERS_DECK = """  - langsel
  - include-code-files
  - passage-xref
  - details
  - code-window
  - lightbox"""

# Charts/tables keep their own numbering; appendices get "Appendix A —".
CROSSREF_EN = """crossref:
  appendix-title: "Appendix\""""
CROSSREF_FR = """crossref:
  appendix-title: "Annexe\""""

FORMATS = """format:
  html:
    theme:
      light: [cosmo, al-brand-light, al-brand-book.scss]
      dark: [cosmo, al-brand-dark, al-brand-book.scss]
    toc: true
    toc-depth: 3
    number-depth: 1
    code-copy: true
    lightbox: auto
  typst:
    toc: true
    papersize: a4
    margin:
      x: 2cm
      y: 2cm
  epub:
    toc: true
  docx:
    toc: true"""

EXTENSIONS = """extensions:
  linkrot:
    fail-on-error: false
    timeout: 8
    cache-results: true"""

# One deck per chapter per language: a book project renders its chapters, so
# these stay separate single-file renders. embed-resources keeps each deck
# shareable as one file; the chapter title drops back to a slide (# -> ##).
DECK = """---
title: "{title}"
lang: {lang}
filters:
{filters}
format:
  revealjs:
    output-file: "{slug}-slides.html"
    theme: [default, al-brand-slides.scss]
    slide-number: c/t
    hash-type: number
    progress: true
    scrollable: true
    smaller: true
    highlight-style: github
    embed-resources: true
---

"""

REPO_SRC = f"{REPO}/blob/main/chapters/"
BOOK_URL = f"{SITE}og-card.png"


def order():
        """[(kind, a, b, *titles)] from chapters/_order.txt.

        kind is PART (a=EN label, b=FR label), APPENDICES, HOME (the book home
        page) or FILE — for which a = path, b = slug and titles = (EN, FR), the
        one place chapter titles live.
        """
        out = []
        for raw in _open(os.path.join(CH, "_order.txt")):
                line = raw.strip()
                if not line or line.startswith("#"):
                        continue
                head, *rest = (x.strip() for x in line.split("|"))
                if line.startswith("APPENDICES"):
                        out.append(
                                (
                                        "APPENDICES",
                                        rest[0] if rest else "Appendices",
                                        rest[1] if len(rest) > 1 else "Annexes",
                                )
                        )
                elif line.startswith("PART"):
                        out.append(("PART", rest[0], rest[1]))
                elif line.startswith("HOME"):
                        out.append(("HOME", "index.qmd", "welcome", rest[0], rest[1]))
                elif line.startswith("FILE"):
                        slug = head.split()[1][:-4]
                        if len(rest) != 2:
                                sys.exit(f"build_book: FILE line needs EN|FR titles: {line}")
                        out.append(("FILE", f"chapters/{slug}.qmd", slug, rest[0], rest[1]))
                else:
                        sys.exit(f"build_book: unknown _order.txt line: {line}")
        if not out or out[0][0] == "APPENDICES":
                sys.exit("build_book: _order.txt must start with a PART")
        return out


def book_entries(entries, lang):
        """The book: / appendices: blocks for one language ('' = EN, 'fr')."""
        index = 1 if lang == "" else 2
        chapters, appendices = ["    - index.qmd"], []
        target, part = chapters, False
        for entry in entries:
                kind, a, b = entry[0], entry[1], entry[2]
                if kind == "HOME":
                        continue
                if kind == "APPENDICES":
                        target, part = appendices, False
                elif kind == "PART":
                        target.append(f'    - part: "{a if lang == "" else b}"')
                        target.append("      chapters:")
                        part = True
                else:
                        target.append(f"{'        ' if part else '    '}- {a}")
        if not appendices:
                sys.exit("build_book: _order.txt has no APPENDICES section")
        return "\n".join(chapters), "\n".join(appendices)


def chapter_meta(entries, lang):
        """Chapter-title metadata for one language, used by each source's shared
        H1 (`# {{< meta ch-<slug> >}}`) and by the deck front matter."""
        out = []
        for entry in entries:
                if entry[0] not in ("FILE", "HOME"):
                        continue
                slug, ten, tfr = entry[2], entry[3], entry[4]
                title = ten if lang == "" else tfr
                out.append(f'ch-{slug}: "{title.replace(chr(34), chr(39))}"')
        return "\n".join(out)


def deck_body(body, title, slug):
        """A deck: the shared chapter title becomes a slide, book links point at
        book pages, and includes are rewritten for a root-level document."""
        body = re.sub(
                r"^#\s+\{\{< meta ch-[\w-]+ >\}\}\s*(\{#[\w-]+\})\s*$",
                rf"## {title} \1",
                body,
                count=1,
                flags=re.M,
        )
        body = body.replace('include="../code/', 'include="code/')
        body = re.sub(r"\]\((?:\.\./)?(?:chapters/)?([\w-]+)\.qmd#", r"](\1.html#", body)
        return re.sub(r"\]\((?:\.\./)?(?:chapters/)?([\w-]+)\.qmd\)", r"](\1.html)", body)


def main():
        entries = order()
        # the generator owns .ch-*.qmd: drop decks from an older layout
        for stale in glob.glob(os.path.join(ROOT, ".ch-*.qmd")):
                os.remove(stale)
        decks = []
        for entry in entries:
                if entry[0] != "FILE":
                        continue
                _, path, slug, ten, tfr = entry
                body = _open(os.path.join(ROOT, path)).read().rstrip()
                for lang, title in (("en", ten), ("fr", tfr)):
                        out = os.path.join(ROOT, f".ch-{lang}-{slug}.qmd")
                        with _open(out, "w") as f:
                                f.write(
                                        DECK.format(
                                                title=title.replace('"', "'"),
                                                lang=lang,
                                                slug=slug,
                                                filters=FILTERS_DECK,
                                        )
                                        + deck_body(body, title, slug)
                                        + "\n"
                                )
                        decks.append(out)

        en_chapters, en_appendices = book_entries(entries, "")
        fr_chapters, fr_appendices = book_entries(entries, "fr")
        # Quarto *concatenates* list values when it merges a profile into
        # _quarto.yml, so book.chapters/appendices must live in the profile files
        # only — putting the EN list in the base would render the whole book
        # twice in the French edition (and duplicate every heading label).
        configs = {
                ".yml": f"""project:
  type: book
  output-dir: _render/en
  pre-render: tools/build_book.py
profile:
  default: [en]

lang: en
metadata:
  lang: en

filters:
{FILTERS}

{EXTENSIONS}

book:
  title: "{TITLE_EN}"
  subtitle: "{SUBTITLE_EN}"
  author: "Support IA — LocalAI"
  date: today
  description: "{DESCRIPTION_EN}"
  output-file: book
  cover-image: tools/cover.png
  cover-image-alt: "{TITLE_EN}"
  downloads: [pdf, epub, docx]
  repo-url: {REPO}
  repo-actions: [edit, issue]
  site-url: {SITE}
  sharing: [twitter, linkedin]
  search: true
  page-navigation: true
  reader-mode: true
  favicon: tools/favicon.svg
  image: {BOOK_URL}
  image-alt: "{TITLE_EN}"
  twitter-card: true
  open-graph: true

{CROSSREF_EN}

{FORMATS}

# Per-chapter titles. Each chapter's single H1 is `# {{{{< meta ch-<slug> >}}}}`,
# so the title follows the language profile instead of a language-specific
# heading that the book structure would read before filtering.
{chapter_meta(entries, "")}
""",
                "-en.yml": f"""book:
  chapters:
{en_chapters}
  appendices:
{en_appendices}
""",
                "-fr.yml": f"""project:
  output-dir: _render/fr

lang: fr
metadata:
  lang: fr

book:
  title: "{TITLE_FR}"
  subtitle: "{SUBTITLE_FR}"
  description: "{DESCRIPTION_FR}"
  cover-image-alt: "{TITLE_FR}"
  image-alt: "{TITLE_FR}"
  site-url: {SITE}fr/
  chapters:
{fr_chapters}
  appendices:
{fr_appendices}

{CROSSREF_FR}

{chapter_meta(entries, "fr")}
""",
        }
        for name, content in configs.items():
                with _open(os.path.join(ROOT, f"_quarto{name}"), "w") as f:
                        f.write(content)
        print(
                f"built _quarto.yml + _quarto-en.yml + _quarto-fr.yml + {len(decks)} "
                f"revealjs decks ({len(decks) // 2}x EN/FR)"
        )


if __name__ == "__main__":
        main()
