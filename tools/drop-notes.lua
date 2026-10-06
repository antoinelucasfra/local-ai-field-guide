-- Drop presenter-note divs from the book formats. Chapter sources carry
-- ::: {.notes} blocks; revealjs keeps them as speaker notes, html/pdf/epub/docx
-- must not.
function Div(el)
        if el.classes:includes("notes") then
                return {}
        end
        return nil
end
