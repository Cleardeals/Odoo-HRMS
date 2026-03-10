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

patch(HtmlField.prototype, {
    getConfig() {
        const config = super.getConfig(...arguments);
        // Only inject if not already present (guard against double-patching).
        if (!config.Plugins.includes(PageBreakPlugin)) {
            config.Plugins = [...config.Plugins, PageBreakPlugin];
        }
        return config;
    },
});
