#!/usr/bin/env bash
# Regression test for _extensions/langsel: recursion + duplicate-label safety.
# Usage: tools/test-langsel.sh   (exit 0 = pass)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp -r "$root/_extensions" "$root/tools/langsel-test.qmd" "$tmp/"
cd "$tmp"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

quarto render langsel-test.qmd --to markdown --output-dir md-en --quiet -M lang=en
quarto render langsel-test.qmd --to markdown --output-dir md-fr --quiet -M lang=fr

en="md-en/langsel-test.md"
fr="md-fr/langsel-test.md"

grep -q "English top-level" "$en" || fail "EN render lost top-level EN text"
grep -q "English nested pill" "$en" || fail "EN render lost NESTED EN text (recursion broken)"
grep -q "Titre partagé" "$en" && fail "EN render leaked FR content"
grep -q "Pastille" "$en" && fail "EN render leaked NESTED FR content"

grep -q "Paragraphe français de premier niveau" "$fr" || fail "FR render lost top-level FR text"
grep -q "Pastille française imbriquée" "$fr" || fail "FR render lost NESTED FR text (recursion broken)"
grep -q "Shared heading" "$fr" && fail "FR render leaked EN content"
grep -q "English nested pill" "$fr" && fail "FR render leaked NESTED EN content"

grep -qi "title: Titre français" "$fr" || fail "title-fr not promoted in FR render"
grep -qi "title: English title" "$en" || fail "title-en not promoted in EN render"

# Duplicate-label guard: if either language leaks, {#dup} appears twice and typst fails.
quarto render langsel-test.qmd --to typst --output-dir pdf-en --quiet -M lang=en ||
  fail "typst compile failed — duplicate labels? (language leak)"

echo "PASS: langsel recursion, title swap, label dedup"
