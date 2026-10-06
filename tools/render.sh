#!/usr/bin/env sh
# Render one language edition: the book (HTML, PDF, EPUB, DOCX), the 404 page
# and the per-chapter revealjs decks.
#
#   tools/render.sh        # English
#   tools/render.sh fr     # French
#
# The book render also runs tools/build_book.py (pre-render) for the config and
# the decks, but Quarto resolves book.chapters *before* pre-render, so the
# generated chapter files have to exist before it starts: run the generator here.
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
for f in ./*-slides.html; do
        [ -e "$f" ] && mv "$f" "_render/$lang/"
done
[ -e 404.html ] && mv 404.html "_render/$lang/"
[ -d 404_files ] && mv 404_files "_render/$lang/"

echo "rendered $lang -> _render/$lang/"
