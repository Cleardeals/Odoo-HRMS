/** @odoo-module **/
/**
 * Patch HtmlField to inject the PageBreakPlugin into every html editor
 * instance that is rendered inside the document-template form view
 * (.o_document_editor_form).
 *
 * The powerbox command "Page Break" (type "/" then search for it) becomes
 * available once this patch is applied.
 */
import { patch } from "@web/core/utils/patch";
import { HtmlField } from "@html_editor/fields/html_field";
import { PageBreakPlugin } from "./page_break_plugin";

/**
 * Strip presentational ``width`` / ``height`` attributes from every <img>
 * in a DocumentFragment or Element, converting them to inline CSS so the
 * editor's resize handles remain the single source of truth for dimensions.
 *
 * Pasted images from browsers, Word, or other web pages often carry these
 * attributes.  Without this cleanup they compete with the ``style`` attribute
 * that the editor writes when the user drags a resize handle, causing the
 * image to snap back to its original size on every save/reload.
 */
function stripImgPresentationalAttrs(root) {
    const imgs = root.querySelectorAll ? root.querySelectorAll("img") : [];
    for (const img of imgs) {
        for (const attr of ["width", "height"]) {
            const val = img.getAttribute(attr);
            if (val === null) continue;

            const px = /^\d+$/.test(val) ? `${val}px` : val;
            const style = img.getAttribute("style") || "";
            // Only inject into style when the property isn't already there.
            if (!style.replace(/\s/g, "").includes(`${attr}:`)) {
                img.setAttribute(
                    "style",
                    (style.replace(/;\s*$/, "") + `; ${attr}: ${px};`).replace(/^;\s*/, "")
                );
            }
            img.removeAttribute(attr);
        }
    }
}

patch(HtmlField.prototype, {
    getConfig() {
        const config = super.getConfig(...arguments);
        // Only inject if not already present (guard against double-patching).
        if (!config.Plugins.includes(PageBreakPlugin)) {
            config.Plugins = [...config.Plugins, PageBreakPlugin];
        }
        return config;
    },

    // Intercept paste so that images copied from external sources never
    // arrive in the editor with bare width/height attributes.
    async startEditing(...args) {
        const result = await super.startEditing(...args);
        const editable = this.el?.querySelector("[contenteditable]");
        if (editable) {
            editable.addEventListener(
                "paste",
                (ev) => {
                    const html = ev.clipboardData?.getData("text/html");
                    if (!html || !html.includes("<img")) return;

                    // Parse the clipboard HTML, clean the images, and put
                    // the sanitised markup back into the clipboard event by
                    // replacing the default paste with our own insertHTML.
                    ev.preventDefault();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, "text/html");
                    stripImgPresentationalAttrs(doc.body);
                    const clean = doc.body.innerHTML;
                    document.execCommand("insertHTML", false, clean);
                },
                true  // capture phase — runs before the editor's own handler
            );
        }
        return result;
    },
});
