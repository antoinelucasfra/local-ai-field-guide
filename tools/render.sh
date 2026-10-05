#!/usr/bin/env sh
# Render one language edition: the book (HTML, PDF, EPUB, DOCX), the 404 page
# and the per-chapter revealjs decks.
#
#   tools/render.sh        # English
#   tools/render.sh fr     # French
#
# The book render also runs tools/build_book.py (pre-render), which regenerates
# _quarto.yml, _quarto-fr.yml and the deck sources. Deck and 404 renders are
# single-file renders: Quarto writes those next to their source, so they are
# moved into _render/<lang>/ afterwards.
set -e
lang="${1:-en}"
cd "$(dirname "$0")/.."

quarto render --profile "$lang"
quarto render 404.qmd --profile "$lang"
for f in .ch-"$lang"-*.qmd; do
        quarto render "$f"
done

mkdir -p "_render/$lang"
for f in ./*-slides.html; do
        [ -e "$f" ] && mv "$f" "_render/$lang/"
done
[ -e 404.html ] && mv 404.html "_render/$lang/"
[ -d 404_files ] && mv 404_files "_render/$lang/"

echo "rendered $lang -> _render/$lang/"
