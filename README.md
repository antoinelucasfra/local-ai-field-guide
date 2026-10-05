# The Local AI Field Guide / Le guide de terrain de l'IA locale — bilingual book

One Quarto project → **a single coherent book** (20 chapters in 5 parts + 5 appendices), rendered in **French or English**, delivered as:

| Deliverable | Files |
| --- | --- |
| Full book | `book.html` (self-contained) · `book.pdf` · `book.docx` · `book.epub` |
| Per chapter ×25 | `<slug>-slides.html` (reveal deck, self-contained, shareable numbered URLs) · `<slug>.pdf` · `<slug>.html` |

The download strip sits under every chapter title — plus a *suggest an edit* link straight to the chapter source on GitHub.

## Companion code

`code/` holds runnable companions to the recipes (fine-tune script, evaluation gate, minimal RAG, Ollama Modelfile) — shipped with every release and served on Pages under `/code/`. See `code/README.md`.

## Render

```bash
quarto render --profile fr     # French  (~5 min, everything)
quarto render --profile en     # English
```

Plain `quarto render` works too (defaults to English). All outputs land in `_render/<lang>/`, nothing is written to the repo root. The landing page is the one assembled piece: `python3 tools/make_index.py` splices the contents block into `tools/index.html` (CI does this while assembling `_site/`). The generated sources are hidden dotfiles (`.book.qmd`, `.ch-*.qmd`, `.chh-*.qmd`) — `ls` stays clean and git ignores them.

## CI · Pages · Releases

One workflow (`.github/workflows/book.yml`) drives everything:

| Event | What runs |
| --- | --- |
| push / PR | `quarto render --profile en` — build check |
| push `main` | EN + FR render → site assembled (`index.html` + `en/` + `fr/`) → GitHub Pages |
| tag `v*` | EN + FR render → release assets (`local-ai-field-guide-book-vX.Y.Z-en.zip` = PDF+EPUB+DOCX per lang, `local-ai-field-guide-code-vX.Y.Z.zip` = companion scripts, full site zip) → GitHub Release |

Links are checked during every render by the `linkrot` extension (`fail-on-error: false`, so a dead link warns instead of blocking a build).

Pages is live after the first push to `main`: Settings → Pages → Source **GitHub Actions**. Cut a release with:

```bash
git tag v1.0.0 && git push origin main v1.0.0
```

## Book structure

Parts and chapter order live in `chapters/_order.txt` — the single place to edit them. The landing page's contents block is generated from that list plus the rendered book (`tools/make_index.py`), so it cannot drift from the book.

## Architecture

```
chapters/*.qmd      source fragments: ::: {.en} / ::: {.fr} divs, no YAML  ← edit these
chapters/_order.txt part headings + chapter order
tools/build_book.py pre-render hook: regenerates .book.qmd, .ch-*/.chh-* docs
                    and _quarto.yml from _order.txt (never out of sync)
tools/index.html     landing page shell (hero, styling)
tools/make_index.py  splices the landing page from build_book + the EN render + _order.txt
tools/og-card.svg    share-card source (export to og-card.png for social previews)
_quarto-en/fr.yml   profiles: lang + output dir (_render/en|fr)
_extensions/langsel/ filter: keeps the matching language divs; swaps titles;
                    renames {#id-fr} heading ids back to {#id}
```

Three non-obvious build constraints are documented next to the code that depends on them: the two-docs-per-chapter split (`tools/build_book.py`), the `{#id-fr}` id dance (`_extensions/langsel/langsel.lua`), and the wordcount filter's requirement to return a flat block list (`_extensions/andrewheiss/wordcount/wordcount.lua` — wrapping the document in a Div silently empties the HTML table of contents).

Cross-chapter links (`#agents` etc.) resolve inside the merged book; standalone chapter PDFs/HTML get them retargeted to `book.html#…` by the builder.

The book title, subtitle, description and URLs live once, as constants at the top of `tools/build_book.py`. `tools/make_index.py` reads them for the landing page's `<title>`, description, share-card tags and brand, so a rename is one edit plus a re-run of the site assembly.

## Editing

Write each language variant inside its div (`::: {.en}` / `::: {.fr}`); keep heading ids identical across languages (the `-fr` suffixing is automatic). To add a chapter: create `chapters/NN-slug.qmd`, add a `FILE NN-slug.qmd` line to `_order.txt` under the right `PART`. Nothing else — `_quarto.yml` regenerates on next render.

## Conventions

- Slide decks follow slidecrafting defaults: numbered hash URLs (`#/3`), progress bar, scrollable overflow for wide tables, `smaller` density, github highlighting.
- **Branding**: `_extensions/antoinelucasfra/al-brand` (personal Quarto brand extension) supplies palette + typography (light/dark). `al-brand-book.scss` layers book-specific styling on top (part dividers, download pills, TOC/table polish); `al-brand-slides.scss` ports the identity to revealjs decks.
- **Speaker notes**: chapters 1–7 carry bilingual presenter notes in `::: {.notes}` blocks — visible in reveal's presenter view (`S`), automatically stripped from book/pdf/html by the builder.
- Chapter 3 embeds a **WebLLM zero-install demo** (model runs in the browser via WebGPU); serve `_render/<lang>/` over HTTP for it to load.
- Benchmarks/product facts are an early-2026 snapshot (sources in Annex B); method chapters (5, 7, 13, 16) are durable.

## License and citation

Prose (this book, its chapters and figures): CC BY 4.0 — reuse, translate and quote freely, with attribution to *Support IA — LocalAI* and a link back. Companion code in `code/`: MIT. Metadata for citation managers lives in `CITATION.cff`; cite the version you read (releases are tagged `vX.Y.Z`).
