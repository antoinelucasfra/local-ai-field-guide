#!/usr/bin/env python3
"""Merge chapters/*.qmd into the single book volume _gen/book.qmd.

Chapter order and part headings come from chapters/_order.txt.
Run before quarto render:  python3 tools/build_book.py && quarto render --profile fr
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, 'chapters')
OUT = os.path.join(ROOT, 'book.qmd')

FRONTMATTER = '''---
author: "Support IA — LocalAI"
date: today
filters:
  - highlight-text
  - langsel
title: "doc"
title-en: "Sovereign Local AI — The Reference Guide"
title-fr: "L'IA locale souveraine — Le guide de référence"
subtitle-en: "Researchers, public institutes, companies · with Unsloth"
subtitle-fr: "Chercheurs, instituts publics, entreprises · avec Unsloth"
number-sections: true
number-depth: 2
format-links: false
format:
  html:
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
    toc: true
---

'''

def main():
    lines = [FRONTMATTER]
    for raw in open(os.path.join(CH, '_order.txt')):
        raw = raw.strip()
        if not raw or raw.startswith('#'):
            continue
        if raw.startswith('PART'):
            _, en, fr = (x.strip() for x in raw.split('|'))
            lines.append(f'::: {{.en}}\n# {en} {{.unnumbered}}\n:::\n\n::: {{.fr}}\n# {fr} {{.unnumbered}}\n:::\n\n')
        elif raw.startswith('FILE'):
            fname = raw.split()[1]
            body = open(os.path.join(CH, fname)).read().rstrip()
            # demote chapter H2 pairs are already ## — fine; ensure single blank line separation
            lines.append(body + '\n\n')
        else:
            sys.exit(f'bad line in _order.txt: {raw!r}')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w').write(''.join(lines))
    n = sum(1 for l in lines)
    print(f'built {OUT} ({n} blocks)')

if __name__ == '__main__':
    main()
