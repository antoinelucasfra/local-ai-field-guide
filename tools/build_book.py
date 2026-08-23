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
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, 'chapters')

FRONT = '''---
author: "Support IA — LocalAI"
date: today
filters:
  - highlight-text
  - langsel
title: "doc"
title-en: "{ten}"
title-fr: "{tfr}"
format-links: false
format:
{fmt}
---

'''

BOOK_FMT = '''  html:
    output-file: book.html
    toc: true
    toc-depth: 3
    theme: cosmo
    embed-resources: true
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
    toc: true'''

# Each chapter is emitted as TWO hidden docs so no single document ever
# declares both html-family formats (quarto renders a doc's formats
# concurrently; html + revealjs race on the shared <slug>_files dir and
# corrupt embed-resources). Split docs = parallel-safe plain `quarto render`.
SLIDES_FMT = '''  revealjs:
    output-file: {slug}-slides.html
    theme: default
    slide-number: c/t
    hash-type: number
    progress: true
    scrollable: true
    smaller: true
    highlight-style: github
    embed-resources: true'''

DOC_FMT = '''  typst:
    output-file: {slug}.pdf
    papersize: a4
    margin:
      x: 1.8cm
      y: 1.8cm
  html:
    output-file: {slug}.html
    toc: true
    toc-depth: 2
    theme: cosmo
    embed-resources: true'''

YML = '''project:
  type: default
  pre-render: tools/build_book.py
  render:
    - .book.qmd{entries}
profile:
  default: [en]
'''


def order():
    out = []
    for l in open(os.path.join(CH, '_order.txt')):
        l = l.strip()
        if l and not l.startswith('#'):
            out.append(l)
    return out


def dedup_ids(body):
    """Second occurrence of {#id} (the FR heading) becomes {#id-fr}."""
    seen = set()
    def sub(m):
        i = m.group(1)
        if i in seen:
            return '{#' + i + '-fr}'
        seen.add(i)
        return m.group(0)
    return re.sub(r'\{#([\w-]+)\}', sub, body)


def chapter_titles(body, slug):
    ten = tfr = None
    lines = body.split('\n')
    for i, l in enumerate(lines):
        m = re.match(r'^## (.+?) \{#\w+', l.strip())
        if not m:
            continue
        prev = lines[i - 1].strip() if i else ''
        if prev == '::: {.en}' and ten is None:
            ten = m.group(1)
        elif prev == '::: {.fr}' and tfr is None:
            tfr = m.group(1)
    return (ten or slug), (tfr or slug)


def rewrite_foreign_links(body, ids):
    def sub(m):
        return m.group(0).replace(f'(#{m.group(2)})', f'(book.html#{m.group(2)})') \
            if m.group(2) not in ids else m.group(0)
    return re.sub(r'\[([^\]]+)\]\(#([\w-]+)\)', sub, body)


def main():
    slugs, book = [], []
    for raw in order():
        if raw.startswith('PART'):
            _, en, fr = (x.strip() for x in raw.split('|'))
            book.append(f'::: {{.en}}\n# {en} {{.unnumbered}}\n:::\n\n'
                        f'::: {{.fr}}\n# {fr} {{.unnumbered}}\n:::\n\n')
        elif raw.startswith('FILE'):
            slug = raw.split()[1][:-4]
            slugs.append(slug)
            slug_body = dedup_ids(open(os.path.join(CH, slug + '.qmd')).read().rstrip())
            # presenter notes are for slide decks only — never in the merged volume
            body = re.sub(r'\n*::: \{\.notes\}.*?\n:::\n?', '', slug_body, flags=re.S)
            strip = (f'\n\n::: {{.en}}\nThis chapter standalone: '
                     f'[slides]({slug}-slides.html) · [PDF]({slug}.pdf) · '
                     f'[HTML]({slug}.html)\n:::\n\n'
                     f'::: {{.fr}}\nCe chapitre seul : '
                     f'[diapositives]({slug}-slides.html) · [PDF]({slug}.pdf) · '
                     f'[HTML]({slug}.html)\n:::\n')
            book.append(body + strip + '\n\n')
            ten, tfr = chapter_titles(body, slug)
            ids = set(re.findall(r'\{#([\w-]+)\}', body))
            sbody = rewrite_foreign_links(body, ids)
            # standalone docs: .ch keeps presenter notes (slides), .chh drops them
            meta = dict(ten=ten.replace('"', "'"), tfr=tfr.replace('"', "'"))
            open(os.path.join(ROOT, f'.ch-{slug}.qmd'), 'w').write(
                FRONT.format(fmt=SLIDES_FMT.format(slug=slug), **meta)
                + rewrite_foreign_links(slug_body,
                    set(re.findall(r'\{#([\w-]+)\}', slug_body))).rstrip()
                + '\n')
            open(os.path.join(ROOT, f'.chh-{slug}.qmd'), 'w').write(
                FRONT.format(fmt=DOC_FMT.format(slug=slug), **meta) + sbody.rstrip() + '\n')

    open(os.path.join(ROOT, '.book.qmd'), 'w').write(
        FRONT.format(ten='Sovereign Local AI — The Reference Guide',
                     tfr="L'IA locale souveraine — Le guide de référence",
                     fmt=BOOK_FMT) + ''.join(book))
    open(os.path.join(ROOT, '_quarto.yml'), 'w').write(YML.replace(
        '{entries}', ''.join(f'\n    - .ch-{s}.qmd\n    - .chh-{s}.qmd' for s in slugs)))
    print(f'built .book.qmd + {len(slugs)}x(.ch,.chh).qmd + _quarto.yml')


if __name__ == '__main__':
    main()
