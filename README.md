# L'IA locale souveraine / Sovereign Local AI — bilingual book

One Quarto project → **a single coherent book** (19 chapters in 5 parts + 2 annexes), rendered in **French or English**, delivered as:

| Deliverable | Files |
|---|---|
| Full book | `book.html` (self-contained) · `book.pdf` · `book.docx` · `book.epub` |
| Per chapter ×24 | `<slug>-slides.html` (reveal deck, self-contained, shareable numbered URLs) · `<slug>.pdf` · `<slug>.html` |

Download links appear at the end of every chapter inside the book.

## Render

```bash
quarto render --profile fr     # French  (~5 min, everything)
quarto render --profile en     # English
```

Plain `quarto render` works too (defaults to English). All outputs land in `_render/<lang>/`, nothing is written to the repo root. The generated sources are hidden dotfiles (`.book.qmd`, `.ch-*.qmd`, `.chh-*.qmd`) — `ls` stays clean and git ignores them.

## Book structure

- **Part I — Foundations**: 1 why now · 2 choosing models
- **Part II — Running models**: 3 ecosystem & install · 4 Studio Chat · 5 inference parameters
- **Part III — Training**: 6 fine-tuning pipeline · 7 hyperparameters · 8 Data Recipes
- **Part IV — Developing & deploying**: 9 export · 10 coding agents · 11 harnesses (reco: pi) · 12 Python · 13 RAG cookbook · 14 voice/vision/images · 15 team serving
- **Part V — Governing**: 16 evaluation · 17 GDPR & hardening · 18 business case · 19 strategy paper
- **Appendices**: A researcher primer · B sources & limits · C projects directory · D hardware guide · E DPIA template

## Architecture

```
chapters/*.qmd      source fragments: ::: {.en} / ::: {.fr} divs, no YAML  ← edit these
chapters/_order.txt part headings + chapter order
tools/build_book.py pre-render hook: regenerates .book.qmd, .ch-*/.chh-* docs
                    and _quarto.yml from _order.txt (never out of sync)
_quarto-en/fr.yml   profiles: lang + output dir (_render/en|fr)
_extensions/langsel/ filter: keeps the matching language divs; swaps titles;
                    renames {#id-fr} heading ids back to {#id}
```

Why two generated docs per chapter: Quarto renders a document's formats concurrently, and `html` + `revealjs` race on the shared `<slug>_files` dir which corrupts self-contained slide embedding. Slides live in `.ch-<slug>.qmd`, pdf+html in `.chh-<slug>.qmd`, so no document ever declares two html-family formats.

Why `{#id-fr}`: pandoc warns about duplicate identifiers *before* the language filter runs. The builder suffixes the FR occurrence; langsel restores canonical ids after filtering, so anchors stay `#params` in both languages and warnings disappear.

Cross-chapter links (`#agents` etc.) resolve inside the merged book; standalone chapter PDFs/HTML get them retargeted to `book.html#…` by the builder.

## Editing

Write each language variant inside its div (`::: {.en}` / `::: {.fr}`); keep heading ids identical across languages (the `-fr` suffixing is automatic). To add a chapter: create `chapters/NN-slug.qmd`, add a `FILE NN-slug.qmd` line to `_order.txt` under the right `PART`. Nothing else — `_quarto.yml` regenerates on next render.

## Conventions

- Slide decks follow slidecrafting defaults: numbered hash URLs (`#/3`), progress bar, scrollable overflow for wide tables, `smaller` density, github highlighting.
- **Speaker notes**: chapters 1–7 carry bilingual presenter notes in `::: {.notes}` blocks — visible in reveal's presenter view (`S`), automatically stripped from book/pdf/html by the builder.
- Chapter 3 embeds a **WebLLM zero-install demo** (model runs in the browser via WebGPU); serve `_render/<lang>/` over HTTP for it to load.
- Benchmarks/product facts are an early-2026 snapshot (sources in Annex B); method chapters (5, 7, 13, 16) are durable.
