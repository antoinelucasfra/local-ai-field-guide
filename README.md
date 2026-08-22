# Local AI with Unsloth — bilingual document suite

One Quarto project → **four documents × four formats (HTML, PDF, Word, slides) × two languages (FR/EN)**, chosen at render time.

## Documents

| File | Audience | Output |
|---|---|---|
| `index.qmd` | AI practitioners — full setup, fine-tuning, agents, GDPR mapping | `guide.html`, `guide-slides.html`, `guide.docx`, `guide.pdf` |
| `researcher-brief.qmd` | Researchers new to AI — 30-minute primer | `researcher-brief.{html,pdf}` |
| `business-case.qmd` | Lab/department directors — TCO, risks, 90-day pilot | `business-case.{html,pdf}` |
| `strategy-paper.qmd` | Institute leadership — sovereignty, EU AI Act, investment scenarios | `strategy-paper.{html,pdf}` |

## Render

```bash
quarto render --profile fr   # French  -> _render/fr/
quarto render --profile en   # English -> _render/en/
```

Single format or single file:

```bash
quarto render --profile fr --to revealjs
quarto render researcher-brief.qmd --profile en
```

## How it works

- `_quarto-en.yml` / `_quarto-fr.yml` — Quarto profiles: set `lang` and the output dir.
- `_extensions/langsel/` — local filter that keeps only the `::: {.fr}` / `::: {.en}` blocks matching `lang`, and swaps bilingual titles. Runs in the `Pandoc` handler because Quarto defers `Meta` handlers until after body filters.
- **Bilingual titles**: each `.qmd` carries a placeholder `title:` plus hidden `title-en:` / `title-fr:` (and `-subtitle`) pairs; langsel promotes the matching variant. The placeholder is required — without any `title`, Quarto substitutes the filename *after* pandoc and clobbers the swap.
- `_extensions/mcanouil/highlight-text/` — [mcanouil's extension](https://github.com/mcanouil/quarto-highlight-text) for `[text]{fg="…"}` colour spans that compile across HTML, Reveal.js, Typst/PDF and Word.
- PDF uses the Typst engine (bundled with Quarto) — no LaTeX needed.

## Editing

Write each language variant in a div:

```markdown
::: {.en}
English text
:::

::: {.fr}
Texte français
:::
```

Headings go inside the divs; keep the same `{#id .lang}` anchor in both variants so links stay stable. For a new document, copy the frontmatter pattern from an existing one (placeholder title + title/subtitle pairs + both filters).

## Adding a language

1. Copy heading/body blocks into `::: {.de}` divs.
2. Add `'de'` handling in `_extensions/langsel/langsel.lua`.
3. Create `_quarto-de.yml` with `lang: de` and its output dir; add `title-de` fields to each doc.
