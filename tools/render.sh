#!/usr/bin/env sh
# Render one language edition (<lang>, default en): the book (HTML, PDF, EPUB,
# DOCX), the 404 page and the per-chapter revealjs decks.
#
# tools/build_book.py runs first: Quarto resolves book.chapters before the
# pre-render hook, so a fresh checkout has no chapters/<slug>.qmd when Quarto
# starts. Deck and 404 renders are single-file renders, so Quarto writes them next
# to their source and they are moved into _render/<lang>/ at the end.
set -e
lang="${1:-en}"
cd "$(dirname "$0")/.."
py=python3
command -v python3 >/dev/null 2>&1 || py=python  # Git Bash has no python3

QUARTO_PROFILE="$lang" "$py" tools/build_book.py
quarto render --profile "$lang"
quarto render 404.qmd --profile "$lang"
for f in .ch-"$lang"-*.qmd; do
        quarto render "$f"
done

mkdir -p "_render/$lang"
for f in ./*-slides.html ./*-files 404.html; do
        [ -e "$f" ] || continue  # (set -e: an unmatched glob must not abort)
        mv "$f" "_render/$lang/"
done

echo "rendered $lang -> _render/$lang/"
