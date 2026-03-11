/** @odoo-module **/
/**
 * PageBreakPlugin — adds a "Page Break" command to the html_editor powerbox.
 *
 * Inserting a page break places a <div class="o_page_break"> at the cursor.
 * In the editor it renders as a visual dashed separator line.
 * When the document is exported to PDF, the CSS rule
 * `page-break-before: always` on that div forces wkhtmltopdf to start a
 * new page at that point.
 */
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { parseHTML } from "@html_editor/utils/html";
import { _t } from "@web/core/l10n/translation";

export class PageBreakPlugin extends Plugin {
    static id = "page_break";
    static dependencies = ["dom", "history", "selection", "baseContainer", "sanitize"];

    resources = {
        user_commands: [
            {
                id: "insert_page_break",
                title: _t("Page Break"),
                description: _t("Insert a manual page break — starts a new page in the exported PDF"),
                icon: "fa-scissors",
                run: () => this.insertPageBreak(),
            },
        ],
        powerbox_categories: withSequence(55, {
            id: "page_layout",
            name: _t("Layout"),
        }),
        powerbox_items: [
            {
                commandId: "insert_page_break",
                categoryId: "page_layout",
            },
        ],
    };

    insertPageBreak() {
        // Build the non-editable page-break sentinel div.
        // The o-contenteditable-false class lets the sanitize plugin manage
        // the contenteditable attribute consistently with other editor blocks.
        const pageBreakEl = parseHTML(
            this.document,
            `<div class="o_page_break user-select-none o-contenteditable-false" ` +
                `contenteditable="false" data-oe-role="page-break">` +
                `<span class="o_page_break_label">— Page Break —</span>` +
                `</div>`,
        ).childNodes[0];

        this.dependencies.dom.insert(pageBreakEl);

        // Place cursor in a fresh paragraph after the page break so the user
        // can continue typing on the new page immediately.
        const newP = this.dependencies.baseContainer.createBaseContainer();
        const br = this.document.createElement("br");
        newP.appendChild(br);
        pageBreakEl.after(newP);
        this.dependencies.selection.setCursorStart(newP);
        this.dependencies.history.addStep();
    }
}
