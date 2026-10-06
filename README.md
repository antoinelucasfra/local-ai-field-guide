# The Local AI Field Guide / Le guide de terrain de l'IA locale — bilingual book

One Quarto **book** project → **a single coherent book** (19 chapters in 5 parts + 5 appendices), rendered in **French or English**, delivered as:

| Deliverable | Files |
| --- | --- |
| Book | one HTML page per chapter plus `index.html`, `book.pdf` · `book.docx` · `book.epub` |
| Per chapter ×24 | `<slug>-slides.html` (reveal deck, self-contained, shareable numbered URLs) |

Quarto owns the book furniture: parts and appendices in the sidebar, chapter numbering, full-text search, previous/next navigation and *report an issue*, plus a PDF/EPUB/Word download block. Two things are generated: the per-chapter revealjs decks (a book project renders its chapters, not extra decks) and the per-language chapter files, because Quarto reads a chapter's title from its first heading *before* filters run and uses that text for the sidebar, breadcrumbs and search index.

## Companion code

`code/` holds runnable companions to the recipes (fine-tune script, evaluation gate, minimal RAG, Ollama Modelfile) — shipped with every release and served on Pages under `/code/`. See `code/README.md`.

## Render

```bash
tools/render.sh        # English: book (HTML/PDF/EPUB/DOCX) + decks + 404
tools/render.sh fr     # French
```

Everything lands in `_render/<lang>/`; nothing is left in the repo root. The landing page is the one assembled piece: `python3 tools/make_index.py --render _render/en --lang en` splices the contents block into `tools/index.html` (CI does this while assembling `_site/`). Every run regenerates three configs (`_quarto.yml`, `_quarto-en.yml`, `_quarto-fr.yml`), the chapter files `chapters/<slug>.qmd` and the deck sources `.ch-<lang>-<slug>.qmd`; all of it is gitignored, and only `chapters/_src/` is yours to edit.

## CI · Pages · Releases

One workflow (`.github/workflows/book.yml`) drives everything:

| Event | What runs |
| --- | --- |
| push / PR | `tools/render.sh en` — build check |
| push `main` | EN + FR render → site assembled (`index.html` + `en/` + `fr/`) → GitHub Pages |
| tag `v*` | EN + FR render → release assets (`local-ai-field-guide-book-vX.Y.Z-en.zip` = PDF+EPUB+DOCX per lang, `local-ai-field-guide-code-vX.Y.Z.zip` = companion scripts, full site zip) → GitHub Release |

Links are checked during every render by the `linkrot` extension (`fail-on-error: false`, so a dead link warns instead of blocking a build).

Pages is live after the first push to `main`: Settings → Pages → Source **GitHub Actions**. Cut a release with:

```bash
git tag v1.0.0 && git push origin main v1.0.0
```

## Book structure

Parts and chapter order live in `chapters/_order.txt` — the single place to edit them, including the `APPENDICES|EN|FR` marker that switches the rest of the list into the book's appendices. `tools/build_book.py` turns it into `book: chapters:` (with `part:` labels per language) and the landing page's contents block is generated from the same list plus the rendered chapter titles, so neither can drift.

## Architecture

```
index.qmd                  the book home page (Quarto requires one), unnumbered
chapters/_src/*.qmd        chapters: ::: {.en} / ::: {.fr} divs, no YAML ← edit these
chapters/_order.txt        parts, appendices and chapter order
chapters/*.qmd             generated per render, one language's title  (gitignored)
tools/build_book.py        pre-render hook: writes _quarto.yml + _quarto-fr.yml, the
                           chapters/<slug>.qmd files and the deck sources
tools/drop-notes.lua       filter: removes ::: {.notes} blocks from the book formats
tools/render.sh            one command per language: book + decks + 404
tools/index.html           landing page shell (hero, styling, generated markers)
tools/make_index.py        splices the landing page from build_book + the render
tools/cover.svg|png        book cover (HTML home page + EPUB)
tools/og-card.svg|png      share card for social previews
tools/favicon.svg    book favicon
_extensions/langsel/ filter: keeps the matching language divs; swaps titles;
                     renames {#id-fr} heading ids back to {#id}
```

Constraints are documented next to the code that depends on them.

Cross-chapter links are written file-qualified in the sources (`16-evaluer.qmd#evaluate`); Quarto resolves them to the rendered page in every format. The deck sources get the same links rewritten to `.html`, since the decks sit next to the book pages.

The book title, subtitle, description and URLs live once, as constants at the top of `tools/build_book.py`. `tools/make_index.py` reads them for the landing page's `<title>`, description, share-card tags and brand, so a rename is one edit plus a re-run of the site assembly.

## Editing

Write each language variant inside its div (`::: {.en}` / `::: {.fr}`); keep heading ids identical across languages — the second (French) occurrence is written `{#id-fr}` and langsel renames it back after filtering. To add a chapter: create `chapters/_src/NN-slug.qmd` starting with `# {{< meta ch-NN-slug >}} {#id}` (the marker the generator replaces), add a `FILE NN-slug.qmd|EN title|FR title` line to `_order.txt` under the right `PART`. Nothing else — the config and the per-language chapter files regenerate on next render. Chapter numbers are Quarto's: never write one into a heading. `index.qmd` is the one hand-written page (Quarto wants the home page at the project root, so it is not generated): it keeps the title marker, and its one-item breadcrumb is hidden in CSS because Quarto builds that crumb from the raw marker.

## Conventions

- Slide decks follow slidecrafting defaults: numbered hash URLs (`#/3`), progress bar, scrollable overflow for wide tables, `smaller` density, github highlighting.
- **Branding**: `_extensions/antoinelucasfra/al-brand` (personal Quarto brand extension) supplies palette + typography (light/dark). `al-brand-book.scss` layers book-specific styling on top (headings, code surfaces, tables, TOC polish); `al-brand-slides.scss` ports the identity to revealjs decks.
- **Speaker notes**: chapters 1–7 carry bilingual presenter notes in `::: {.notes}` blocks — visible in reveal's presenter view (`S`), dropped from HTML/PDF/EPUB/Word by `tools/drop-notes.lua`.
- Chapter 3 embeds a **WebLLM zero-install demo** (model runs in the browser via WebGPU); serve `_render/<lang>/` over HTTP for it to load.
- Benchmarks/product facts are an early-2026 snapshot (sources in Annex B); method chapters (5, 7, 13, 16) are durable.

## License and citation

Prose (this book, its chapters and figures): CC BY 4.0 — reuse, translate and quote freely, with attribution to *Support IA — LocalAI* and a link back. Companion code in `code/`: MIT. Metadata for citation managers lives in `CITATION.cff`; cite the version you read (releases are tagged `vX.Y.Z`).
