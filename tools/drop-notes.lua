-- Remove presenter-note divs from the book formats.
-- chapters/*.qmd carry ::: {.notes} blocks for the revealjs decks; in a book
-- project the chapter sources are rendered directly, so those blocks must be
-- dropped for html/pdf/epub/docx while revealjs keeps them as speaker notes.
function Div(el)
        if el.classes:includes("notes") then
                return {}
        end
        return nil
end
