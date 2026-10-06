#!/usr/bin/env python3
"""Build the bilingual Quarto book configuration and chapter files.

Sources : chapters/_src/*.qmd + chapters/_order.txt  (the edited files)
          index.qmd                                 (the book home page)
Outputs : _quarto.yml + _quarto-en.yml + _quarto-fr.yml  book config
          chapters/<slug>.qmd                       chapter, title in one language
          .ch-<lang>-<slug>.qmd                     revealjs decks (gitignored)

Every chapter has one H1 and it is not duplicated per language: the book reads a
chapter's first heading *before* filters run, so an English/French pair there
titled the French edition in English. The sources keep that heading as an inert
marker (`# {{< meta ch-<slug> >}} {#id}` — nothing expands it) and this generator
writes, per run, the chapter file the book lists with a real title for the active
profile: Quarto reads source text for the sidebar, breadcrumbs and search index.

Id convention: the second occurrence of {#id} in a source (the FR heading)
becomes {#id-fr}; langsel.lua renames it back after filtering, so pandoc never
sees duplicate ids and final anchors stay language-independent.

Run as project pre-render (QUARTO_PROFILE picks the language) and by tools/render.sh
before Quarto starts, because a fresh checkout has no chapters/<slug>.qmd yet and
Quarto resolves book.chapters before the pre-render hook.
"""

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CH = os.path.join(ROOT, "chapters")
# chapter bodies: Quarto ignores _-prefixed directories, so these are never
# rendered as pages of their own (the generated chapter files are)
SRC = os.path.join(CH, "_src")

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

# Project-level filter chain, applied to every book format. The decks use the
# same chain minus drop-notes: speaker notes must survive for revealjs.
FILTER_NAMES = [
        "langsel",
        "include-code-files",
        "passage-xref",
        "details",
        "code-window",
        "lightbox",
]
FILTERS = "\n".join(f"  - {f}" for f in [*FILTER_NAMES, "tools/drop-notes.lua"])
FILTERS_DECK = "\n".join(f"  - {f}" for f in FILTER_NAMES)

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

BOOK_URL = f"{SITE}og-card.png"

# The shared H1 marker of chapters/_src/*.qmd: `# {{< meta ch-<slug> >}} {#id}`
H1_MARKER = re.compile(r"^#\s+\{\{< meta ch-[\w-]+ >\}\}\s*(\{#[\w-]+\})\s*$", re.M)


def order():
        """[(kind, a, b, *titles)] from chapters/_order.txt.

        kind is PART (a=EN label, b=FR label), APPENDICES, HOME (the book home
        page) or FILE — for which a = path, b = slug and titles = (EN, FR), the
        one place chapter titles live.
        """
        out = []
        for raw in open(os.path.join(CH, "_order.txt"), encoding="utf-8"):
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


def deck_body(body, title):
        """A deck: the shared chapter title becomes a slide, book links point at
        book pages, and includes are rewritten for a root-level document."""
        body = H1_MARKER.sub(rf"## {title} \1", body, count=1)
        body = body.replace('include="../code/', 'include="code/')
        body = re.sub(r"\]\((?:\.\./)?(?:chapters/)?([\w-]+)\.qmd#", r"](\1.html#", body)
        return re.sub(r"\]\((?:\.\./)?(?:chapters/)?([\w-]+)\.qmd\)", r"](\1.html)", body)


def active_lang():
        """'' for English (the default profile), 'fr' for French."""
        return "fr" if "fr" in os.environ.get("QUARTO_PROFILE", "").split(",") else ""


def chapter_body(body, title):
        """The chapter file the book lists. Its single H1 keeps the marker's id but
        carries the profile's real title, because Quarto reads that text for the
        sidebar, the breadcrumbs and the search index."""
        return H1_MARKER.sub(rf"# {title} \1", body, count=1)


def main():
        entries = order()
        lang = active_lang()
        # the generator owns .ch-*.qmd and chapters/*.qmd: drop leftovers from an
        # older layout, or chapters that left _order.txt
        for stale in glob.glob(os.path.join(ROOT, ".ch-*.qmd")):
                os.remove(stale)
        wanted = {entry[1] for entry in entries if entry[0] == "FILE"}
        for stale in glob.glob(os.path.join(CH, "*.qmd")):
                if os.path.relpath(stale, ROOT).replace(os.sep, "/") not in wanted:
                        os.remove(stale)
        decks = []
        for entry in entries:
                if entry[0] != "FILE":
                        continue
                _, path, slug, ten, tfr = entry
                body = open(os.path.join(SRC, slug + ".qmd"), encoding="utf-8").read().rstrip()
                chapter = chapter_body(body, ten if lang == "" else tfr)
                if chapter == body:
                        sys.exit(f"build_book: {slug}: chapter heading marker not found")
                with open(os.path.join(ROOT, path), "w", encoding="utf-8") as f:
                        f.write(chapter + "\n")
                for deck_lang, title in (("en", ten), ("fr", tfr)):
                        out = os.path.join(ROOT, f".ch-{deck_lang}-{slug}.qmd")
                        with open(out, "w", encoding="utf-8") as f:
                                f.write(
                                        DECK.format(
                                                title=title.replace('"', "'"),
                                                lang=deck_lang,
                                                slug=slug,
                                                filters=FILTERS_DECK,
                                        )
                                        + deck_body(body, title)
                                        + "\n"
                                )
                        decks.append(out)

        en_chapters, en_appendices = book_entries(entries, "")
        fr_chapters, fr_appendices = book_entries(entries, "fr")
        # index.qmd is hand-written (not generated), so its shared H1 marker has
        # nothing to be replaced with: it expands this key instead. One key per
        # profile; generated chapters carry real titles and need none.
        home = next(e for e in entries if e[0] == "HOME")
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
  # no edit action: Quarto links the file it rendered, which for chapters is the
  # generated chapters/<slug>.qmd (per-language title, not in git). Sources are
  # chapters/_src/<slug>.qmd.
  repo-actions: [issue]
  site-url: {SITE}
  sharing: [twitter, linkedin]
  search: true
  page-navigation: true
  reader-mode: true
  page-footer:
    center: "Book: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — Support IA — LocalAI"
  favicon: tools/favicon.svg
  image: {BOOK_URL}
  image-alt: "{TITLE_EN}"
  twitter-card: true
  open-graph: true

{CROSSREF_EN}

{FORMATS}

ch-welcome: "{home[3]}"
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

language:
  tools-download: "Télécharger"
  tools-share: "Partager"

book:
  title: "{TITLE_FR}"
  subtitle: "{SUBTITLE_FR}"
  description: "{DESCRIPTION_FR}"
  cover-image-alt: "{TITLE_FR}"
  image-alt: "{TITLE_FR}"
  site-url: {SITE}fr/
  page-footer:
    center: "Livre : [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — Support IA — LocalAI"
  chapters:
{fr_chapters}
  appendices:
{fr_appendices}

{CROSSREF_FR}

ch-welcome: "{home[4]}"
""",
        }
        for name, content in configs.items():
                with open(os.path.join(ROOT, f"_quarto{name}"), "w", encoding="utf-8") as f:
                        f.write(content)
        print(
                f"built _quarto.yml + _quarto-en.yml + _quarto-fr.yml, "
                f"{len(decks) // 2} chapters ({lang or 'en'}), {len(decks)} decks"
        )


if __name__ == "__main__":
        main()
