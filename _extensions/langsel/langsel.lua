-- Language selection filter.
-- Reads meta `lang` ("fr"/"en"), keeps matching .fr/.en Divs, drops the
-- rest. Also swaps bilingual title/subtitle: docs may define hidden
-- `title-en`/`title-fr` (+ `-subtitle`) pairs; the matching variant is
-- promoted to title/subtitle and the pair removed. Runs in Pandoc()
-- because quarto defers Meta handlers until after body filters.

local function drop(classes, lang)
  for _, c in ipairs(classes) do
    if c == 'fr' then return lang ~= 'fr' end
    if c == 'en' then return lang ~= 'en' end
  end
  return false
end

local function pick(meta, key, suffix)
  local v = meta[key .. '-' .. suffix]
  if v ~= nil then meta[key .. '-' .. suffix] = nil end
  return v
end

-- Builder renames the second (FR) occurrence of a shared {#id} to {#id-fr}
-- so pandoc never warns about duplicates; restore canonical ids after
-- filtering so anchors and internal links stay language-independent.
local function fix_ids(blocks)
  for _, b in ipairs(blocks) do
    if b.t == 'Header' then
      b.attr.identifier = b.attr.identifier:gsub('%-fr$', '')
    end
    if b.t == 'Div' or b.t == 'BlockQuote' or b.t == 'Figure' then
      fix_ids(b.content)
    end
  end
end

function Pandoc(doc)
  local lang = pandoc.utils.stringify(doc.meta.lang or 'en')

  for _, key in ipairs({'title', 'subtitle'}) do
    local v = pick(doc.meta, key, lang)
    if v ~= nil then doc.meta[key] = v end
  end

  -- Language divs can be NESTED (e.g. ::: {.en} inside :::: {.dl-strip}),
  -- so filtering must recurse into kept Divs/BlockQuotes/Figures.
  local function walk(blocks)
    local out = {}
    for _, b in ipairs(blocks) do
      if not (b.t == 'Div' and drop(b.classes, lang)) then
        if b.t == 'Div' or b.t == 'BlockQuote' or b.t == 'Figure' then
          b.content = walk(b.content)
        end
        table.insert(out, b)
      end
    end
    return out
  end

  local blocks = walk(doc.blocks)
  fix_ids(blocks)
  return pandoc.Pandoc(blocks, doc.meta)
end
