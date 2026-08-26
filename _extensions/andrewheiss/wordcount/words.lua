-- Local patch: Quarto expands shortcodes BEFORE pre-quarto filters run, so the
-- original implementation (reading meta.wordcount_* at expansion time) always
-- saw nil and emitted "cannot find ... in meta data" plus an empty result.
-- Instead we emit a placeholder Span here; wordcount.lua (wired post-quarto)
-- replaces it with the real count after walking the document.

placeholder = function(keys)
  return pandoc.Span("", { ["data-wordcount"] = table.concat(keys, "+") })
end

as_num = function(meta_value)
  if (meta_value == nil) then
    return 0
  end
  return meta_value
end

return {
  ['words-body'] = function(args, kwargs, meta) return placeholder({ 'body' }) end,
  ['words-ref'] = function(args, kwargs, meta) return placeholder({ 'ref' }) end,
  ['words-append'] = function(args, kwargs, meta) return placeholder({ 'append' }) end,
  ['words-note'] = function(args, kwargs, meta) return placeholder({ 'note' }) end,
  ['words-abstract'] = function(args, kwargs, meta) return placeholder({ 'abstract' }) end,
  ['words-total'] = function(args, kwargs, meta) return placeholder({ 'total' }) end,
  ['words-sum'] = function(args, kwargs, meta)
    local keys = {}
    for _, arg in ipairs(args) do
      if arg:match("body") then table.insert(keys, 'body') end
      if arg:match("abstract") then table.insert(keys, 'abstract') end
      if arg:match("ref") then table.insert(keys, 'ref') end
      if arg:match("append") then table.insert(keys, 'append') end
      if arg:match("note") then table.insert(keys, 'note') end
    end
    if #keys == 0 then keys = { 'total' } end
    return placeholder(keys)
  end
}
