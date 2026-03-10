import base64
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# ═══════════════════════════════════════════════════════════════════════
#  DOCUMENT TEMPLATE
# ═══════════════════════════════════════════════════════════════════════


class DocumentTemplate(models.Model):
    """
    A reusable document template with a rich-text body and dynamic
    {{variable}} placeholders that are resolved at PDF-export time.
    """

    _name = "document.template"
    _description = "Document Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "write_date desc, id desc"

    # ── Basic info ────────────────────────────────────────────────────
    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
    )
    category_id = fields.Many2one(
        "document.category",
        string="Category",
        tracking=True,
    )
    tag_ids = fields.Many2many(
        "document.tag",
        string="Tags",
    )
    summary = fields.Text(
        string="Summary",
        help="Brief description of this template",
    )

    # ── Content ───────────────────────────────────────────────────────
    html_content = fields.Html(
        string="Content",
        sanitize=False,
        sanitize_attributes=False,
        sanitize_form=False,
    )
    header_html = fields.Html(
        string="Page Header",
        sanitize=False,
        sanitize_attributes=False,
        sanitize_form=False,
        help="HTML repeated at the top of every page when Print Mode is Digital.",
    )

    # ── Variables ─────────────────────────────────────────────────────
    variable_ids = fields.One2many(
        "document.template.variable",
        "template_id",
        string="Variables",
        copy=True,
    )
    variable_count = fields.Integer(
        compute="_compute_variable_count",
        store=True,
    )

    # ── PDF ───────────────────────────────────────────────────────────
    pdf_filename = fields.Char(compute="_compute_pdf_filename")
    pdf_file = fields.Binary(
        string="Last Generated PDF",
        attachment=True,
        readonly=True,
    )
    has_pdf = fields.Boolean(
        compute="_compute_has_pdf",
        store=True,
    )

    # ── Status / flags ────────────────────────────────────────────────
    active = fields.Boolean(default=True, tracking=True)
    favorite = fields.Boolean(default=False)

    # ── Print Mode ────────────────────────────────────────────────────
    print_mode = fields.Selection(
        [
            ("letterhead", "Letterhead"),
            ("digital", "Digital"),
        ],
        string="Print Mode",
        default="letterhead",
        required=True,
        tracking=True,
        help="Letterhead: large margins for pre-printed letterhead paper, no digital header rendered.\n"
        "Digital: standard margins with the Page Header rendered on every PDF page.",
    )
    show_header = fields.Boolean(
        string="Show Header in PDF",
        default=True,
        help="Include the Page Header on every exported PDF page. Only applies in Digital mode.",
    )

    # ── Print / Margins (mm) ─────────────────────────────────────────
    margin_top = fields.Float(
        string="Top Margin (mm)",
        default=40.0,
        help="Space reserved at the top of each page.",
    )
    margin_bottom = fields.Float(
        string="Bottom Margin (mm)",
        default=25.0,
        help="Space reserved at the bottom of each page.",
    )
    margin_left = fields.Float(
        string="Left Margin (mm)",
        default=20.0,
    )
    margin_right = fields.Float(
        string="Right Margin (mm)",
        default=20.0,
    )

    # ── Company ───────────────────────────────────────────────────────
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )

    # ── Computes ──────────────────────────────────────────────────────
    @api.depends("variable_ids")
    def _compute_variable_count(self):
        for rec in self:
            rec.variable_count = len(rec.variable_ids)

    @api.depends("name")
    def _compute_pdf_filename(self):
        for rec in self:
            if rec.name:
                safe = rec.name.replace("/", "-").replace("\\", "-")
                rec.pdf_filename = f"{safe}.pdf"
            else:
                rec.pdf_filename = "document.pdf"

    @api.depends("pdf_file")
    def _compute_has_pdf(self):
        for rec in self:
            rec.has_pdf = bool(rec.pdf_file)

    @api.onchange("print_mode")
    def _onchange_print_mode(self):
        """Auto-populate margins with sensible defaults for each mode."""
        if self.print_mode == "letterhead":
            self.margin_top = 40.0
            self.margin_bottom = 25.0
            self.margin_left = 20.0
            self.margin_right = 20.0
            self.show_header = True
        else:  # digital
            self.margin_top = 20.0
            self.margin_bottom = 20.0
            self.margin_left = 20.0
            self.margin_right = 20.0
            self.show_header = True

    # ── Validation ────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get("name")
            if not name or not str(name).strip():
                raise ValidationError(_("Template name is required."))
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────
    def action_export_pdf(self):
        """Export template as PDF.

        If the template contains variables the export wizard is opened so
        the user can fill in every placeholder value.  Otherwise the PDF
        is generated and downloaded straight away.
        """
        self.ensure_one()
        if not self.html_content or not self.html_content.strip():
            raise ValidationError(_("Cannot export an empty document."))

        if self.variable_ids:
            # Has variables → open the fill-in wizard
            return {
                "name": _("Export PDF — %s", self.name),
                "type": "ir.actions.act_window",
                "res_model": "document.export.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_template_id": self.id},
            }

        # No variables → generate directly
        pdf_content = self._generate_pdf_bytes(self.html_content)
        return self._save_and_download_pdf(pdf_content)

    def action_download_pdf(self):
        """Download the last generated PDF."""
        self.ensure_one()
        if not self.has_pdf:
            raise ValidationError(_("No PDF available. Please export first."))
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/document.template/{self.id}"
                f"/pdf_file/{self.pdf_filename}?download=true"
            ),
            "target": "self",
        }

    def action_duplicate(self):
        """Duplicate this template."""
        self.ensure_one()
        new = self.copy()
        return {
            "type": "ir.actions.act_window",
            "res_model": "document.template",
            "res_id": new.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_toggle_favorite(self):
        for rec in self:
            rec.favorite = not rec.favorite

    def action_detect_variables(self):
        """Scan HTML content for ``{{variable}}`` placeholders and create
        missing variable records automatically."""
        self.ensure_one()
        if not self.html_content:
            raise ValidationError(_("Document is empty — nothing to scan."))

        found = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", self.html_content))
        existing = set(self.variable_ids.mapped("name"))
        new_vars = found - existing

        seq = max(self.variable_ids.mapped("sequence") or [0])
        for var_name in sorted(new_vars):
            seq += 10
            label = var_name.replace("_", " ").title()
            self.env["document.template.variable"].create(
                {
                    "template_id": self.id,
                    "name": var_name,
                    "label": label,
                    "variable_type": "char",
                    "required": True,
                    "sequence": seq,
                },
            )

        msg = (
            _("%d new variable(s) detected and added.", len(new_vars))
            if new_vars
            else _("No new variables found.")
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Variable Detection"),
                "message": msg,
                "type": "info" if new_vars else "warning",
                "sticky": False,
            },
        }

    # ── Helpers ───────────────────────────────────────────────────────
    def _build_header_html_doc(self, left, right):
        """Build a standalone HTML document for wkhtmltopdf ``--header-html``.

        wkhtmltopdf repeats ``--header-html`` on every page automatically.

        Why this works:
        - ``_run_wkhtmltopdf`` writes this string to a temp file and passes
          its path via ``--header-html <path>`` on the CLI.  wkhtmltopdf then
          renders that file into the top-margin area of every page.
        - The Odoo A4 paper format ships with ``header_spacing = 35`` mm
          (space between header bottom and body).  We override that via
          ``data-report-header-spacing`` in ``specific_paperformat_args``
          (see ``_generate_pdf_bytes``) so the header actually fits.
        - ``--disable-local-file-access`` only blocks resources loaded by the
          HTML *itself* (file:// URLs in img/link tags).  CLI-supplied paths
          like ``--header-html`` are NOT affected.

        Returns ``None`` when the header should not be rendered.
        """
        if self.print_mode != "digital" or not self.show_header:
            return None
        if not self.header_html or not self.header_html.strip():
            return None

        # Strip trailing empty editor paragraphs.
        clean = re.sub(
            r"(\s*<(?:p|div)[^>]*>\s*(?:<br\s*/?>)?\s*</(?:p|div)>)+\s*$",
            "",
            str(self.header_html),
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        if not clean:
            return None

        # Build the full standalone HTML document.
        # Use str.format() so that the CSS double-brace escaping is explicit
        # and user-content ({clean}) never risks being treated as a format
        # specifier.
        css = (
            "* { box-sizing: border-box; }"
            "html, body {"
            "  margin: 0; padding: 0;"
            "  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,"
            "              'Helvetica Neue', Ubuntu, 'Noto Sans', Arial, sans-serif;"
            "  font-size: 0.875rem; color: #333; line-height: 1.2;"
            "}"
            f"body {{ padding: 0 {right}mm 0 {left}mm; }}"
            "p, h1, h2, h3, h4, h5, h6 { margin: 0; padding: 0; line-height: 1.2; }"
            # ── Bootstrap / Odoo editor utility classes ────────────────
            ".d-flex { display: flex; }"
            ".d-block { display: block; }"
            ".d-inline-block { display: inline-block; }"
            ".align-items-center { align-items: center; }"
            ".align-items-start { align-items: flex-start; }"
            ".align-items-end { align-items: flex-end; }"
            ".justify-content-center { justify-content: center; }"
            ".justify-content-between { justify-content: space-between; }"
            ".flex-column { flex-direction: column; }"
            ".flex-fill { flex: 1 1 auto; }"
            ".w-100 { width: 100%; }"
            ".fw-bold { font-weight: 700; }"
            ".fw-semibold { font-weight: 600; }"
            ".fst-italic { font-style: italic; }"
            ".text-center { text-align: center; }"
            ".text-end { text-align: right; }"
            ".lh-1 { line-height: 1; }"
            ".small, .o_small-fs { font-size: 0.8rem; }"
            ".text-muted, .text-secondary { color: #6c757d; }"
            ".text-primary { color: #0d6efd; }"
            ".text-success { color: #198754; }"
            ".text-danger { color: #dc3545; }"
            ".text-dark { color: #212529; }"
            ".text-white { color: #fff; }"
            ".text-black { color: #000; }"
            ".bg-light { background-color: #f8f9fa; }"
            ".bg-white { background-color: #fff; }"
            ".border-bottom { border-bottom: 1px solid #dee2e6; }"
            ".border { border: 1px solid #dee2e6; }"
            ".rounded { border-radius: 0.375rem; }"
            ".p-0 { padding: 0; } .p-1 { padding: 0.25rem; }"
            ".p-2 { padding: 0.5rem; } .p-3 { padding: 1rem; }"
            ".pb-0 { padding-bottom: 0; } .pb-1 { padding-bottom: 0.25rem; }"
            ".pt-1 { padding-top: 0.25rem; } .px-2 { padding-left:0.5rem; padding-right:0.5rem; }"
            ".m-0 { margin: 0; } .mb-0 { margin-bottom: 0; }"
            ".mb-1 { margin-bottom: 0.25rem; } .mb-2 { margin-bottom: 0.5rem; }"
            ".me-1 { margin-right: 0.25rem; } .me-2 { margin-right: 0.5rem; }"
            ".ms-1 { margin-left: 0.25rem; } .ms-2 { margin-left: 0.5rem; }"
            ".mt-1 { margin-top: 0.25rem; } .gap-1 { gap: 0.25rem; }"
            ".gap-2 { gap: 0.5rem; }"
        )

        return (
            "<!DOCTYPE html>\n<html>\n<head>\n"
            '<meta charset="utf-8"/>\n'
            "<style>" + css + "</style>\n"
            "</head>\n<body>"
            + clean
            + '<hr style="border:none;border-bottom:1px solid #dee2e6;margin:4px 0 0 0;"/>'
            + "</body>\n</html>"
        )

    def _generate_pdf_bytes(self, html_body):
        """Wrap *html_body* in a full-page document and run wkhtmltopdf.

        Top/bottom margins are applied via Odoo's recognised
        ``data-report-margin-top`` / ``data-report-margin-bottom`` keys in
        ``specific_paperformat_args`` (the only keys that
        ``_build_wkhtmltopdf_args`` actually reads).

        Left/right cannot be overridden through that mechanism — Odoo always
        takes them from the paper-format record, which for A4 is 0 mm by
        default — so we apply them as CSS body margins instead.
        """
        top = self.margin_top
        bottom = self.margin_bottom
        left = self.margin_left
        right = self.margin_right

        # Strip trailing empty blocks that Odoo's editor appends automatically.
        # Without this, the last empty <p><br></p> creates a blank extra page.
        clean_body = re.sub(
            r"(\s*<(?:p|div)[^>]*>\s*(?:<br\s*/?>)?\s*</(?:p|div)>)+\s*$",
            "",
            html_body,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        /* ── Root font: mirror Odoo's system-font stack ─────────────
           Odoo defines $o-system-fonts as -apple-system, BlinkMacSystemFont,
           "Segoe UI", Roboto, "Helvetica Neue", Ubuntu, "Noto Sans", Arial.
           wkhtmltopdf skips Apple/Blink tokens but picks up "Segoe UI" on
           Windows or Roboto/"Noto Sans" on Linux — matching the browser. */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Ubuntu, "Noto Sans", Arial, sans-serif;
            font-size: 1rem;
            color: #333;
            line-height: 1.6;
            margin-left: {left}mm;
            margin-right: {right}mm;
        }}
        h1 {{ font-size: 2.5rem; font-weight: 700; margin: 0.67em 0; }}
        h2 {{ font-size: 2rem;   font-weight: 600; margin: 0.75em 0; }}
        h3 {{ font-size: 1.75rem; font-weight: 600; margin: 0.83em 0; }}
        h4 {{ font-size: 1.5rem;  font-weight: 600; margin: 0.83em 0; }}
        h5 {{ font-size: 1.25rem; font-weight: 600; margin: 0.83em 0; }}
        h6 {{ font-size: 1rem;    font-weight: 600; margin: 0.83em 0; }}
        p  {{ margin: 0 0 0.5rem 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td, th {{ padding: 8px; border: 1px solid #dee2e6; }}
        th {{ font-weight: 600; background-color: #f8f9fa; }}
        a  {{ color: #0d6efd; }}
        ul, ol {{ padding-left: 1.5rem; margin-bottom: 0.5rem; }}
        blockquote {{
            padding: 0.5rem 1rem;
            border-left: 4px solid #dee2e6;
            font-style: italic;
            margin: 1rem 0;
            color: #6c757d;
        }}
        pre, code {{
            font-family: "Consolas", "Courier New", monospace;
            font-size: 0.875rem;
        }}
        pre {{
            background: #f8f9fa;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            overflow: auto;
        }}

        /* ── Odoo html_editor font-size classes ──────────────────────
           The editor toolbar stores sizes as CSS classes, not inline styles.
           wkhtmltopdf never loads Odoo's Bootstrap SCSS, so redeclare them
           here. Values are taken verbatim from addons/web/.../report.scss
           (calc() fails in wkhtmltopdf, so report.scss uses fixed rems). */
        .display-1-fs, .display-1 {{ font-size: 6rem; }}
        .display-2-fs, .display-2 {{ font-size: 5.5rem; }}
        .display-3-fs, .display-3 {{ font-size: 4.5rem; }}
        .display-4-fs, .display-4 {{ font-size: 3.5rem; }}
        .h1-fs        {{ font-size: 2.5rem; }}
        .h2-fs        {{ font-size: 2rem; }}
        .h3-fs        {{ font-size: 1.75rem; }}
        .h4-fs        {{ font-size: 1.5rem; }}
        .h5-fs        {{ font-size: 1.25rem; }}
        .h6-fs        {{ font-size: 1rem; }}
        .base-fs      {{ font-size: 1rem; }}
        .small        {{ font-size: 0.875em; }}
        .o_small-fs   {{ font-size: 0.875rem; }}
        .lead         {{ font-size: 1.25rem; font-weight: 300; }}

        /* ── Bootstrap layout utilities used by the editor ──────────
           These are the specific utilities the html_editor injects as
           class attributes on its generated blocks (e.g. banners). */
        .d-flex           {{ display: flex; }}
        .d-block          {{ display: block; }}
        .d-inline-block   {{ display: inline-block; }}
        .align-items-center  {{ align-items: center; }}
        .align-items-start   {{ align-items: flex-start; }}
        .align-items-end     {{ align-items: flex-end; }}
        .justify-content-center {{ justify-content: center; }}
        .flex-column      {{ flex-direction: column; }}
        .flex-fill        {{ flex: 1 1 auto; }}
        .w-100            {{ width: 100%; }}
        .fw-bold          {{ font-weight: 700; }}
        .fw-semibold      {{ font-weight: 600; }}
        .fst-italic       {{ font-style: italic; }}
        .fst-normal       {{ font-style: normal; }}
        .text-center      {{ text-align: center; }}
        .text-end         {{ text-align: right; }}
        .lh-1             {{ line-height: 1; }}
        .font-monospace   {{ font-family: "Consolas", "Courier New", monospace; }}
        /* spacing */
        .p-0  {{ padding: 0; }}       .p-1  {{ padding: 0.25rem; }}
        .p-2  {{ padding: 0.5rem; }}  .p-3  {{ padding: 1rem; }}
        .p-4  {{ padding: 1.5rem; }}
        .pb-0 {{ padding-bottom: 0; }}
        .pt-3 {{ padding-top: 1rem; }}
        .px-3 {{ padding-left: 1rem; padding-right: 1rem; }}
        .py-2 {{ padding-top: 0.5rem; padding-bottom: 0.5rem; }}
        .m-0  {{ margin: 0; }}
        .mb-0 {{ margin-bottom: 0; }}
        .mb-1 {{ margin-bottom: 0.25rem; }}
        .mb-2 {{ margin-bottom: 0.5rem; }}
        .mb-3 {{ margin-bottom: 1rem; }}
        .mt-1 {{ margin-top: 0.25rem; }}
        .mt-2 {{ margin-top: 0.5rem; }}
        .me-2 {{ margin-right: 0.5rem; }}
        .ms-2 {{ margin-left: 0.5rem; }}
        /* text colour utilities (Bootstrap + Odoo) */
        .text-primary   {{ color: #0d6efd; }}
        .text-success   {{ color: #198754; }}
        .text-danger    {{ color: #dc3545; }}
        .text-warning   {{ color: #ffc107; }}
        .text-info      {{ color: #0dcaf0; }}
        .text-muted, .text-secondary {{ color: #6c757d; }}
        .text-dark      {{ color: #212529; }}
        .text-light     {{ color: #f8f9fa; }}
        .text-white     {{ color: #ffffff; }}
        .text-black     {{ color: #000000; }}
        /* background utilities */
        .bg-primary  {{ background-color: #0d6efd; }}
        .bg-success  {{ background-color: #198754; }}
        .bg-danger   {{ background-color: #dc3545; }}
        .bg-warning  {{ background-color: #ffc107; }}
        .bg-info     {{ background-color: #0dcaf0; }}
        .bg-light    {{ background-color: #f8f9fa; }}
        .bg-dark     {{ background-color: #212529; }}
        .bg-white    {{ background-color: #ffffff; }}
        .bg-transparent {{ background-color: transparent; }}
        /* border utilities */
        .border       {{ border: 1px solid #dee2e6; }}
        .border-0     {{ border: none; }}
        .rounded      {{ border-radius: 0.375rem; }}
        .rounded-3    {{ border-radius: 0.5rem; }}

        /* ── Bootstrap alert / Odoo banner blocks ────────────────────
           Odoo's html_editor inserts callout blocks as Bootstrap alerts.
           wkhtmltopdf has no Bootstrap loaded, so define the colours here.
           Values are Bootstrap 5 defaults: tint-color(base, 80%) for bg,
           tint-color(base, 60%) for border, shade-color(base, 30%) for text. */
        .alert {{
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            border: 1px solid transparent;
            border-radius: 0.375rem;
        }}
        .alert-info {{
            background-color: #cff4fc;
            border-color: #9eeaf9;
            color: #0a3e4f;
        }}
        .alert-success {{
            background-color: #d1e7dd;
            border-color: #a3cfbb;
            color: #0f5132;
        }}
        .alert-warning {{
            background-color: #fff3cd;
            border-color: #ffe69c;
            color: #664d03;
        }}
        .alert-danger {{
            background-color: #f8d7da;
            border-color: #f1aeb5;
            color: #58151c;
        }}
        .alert-secondary {{
            background-color: #e2e3e5;
            border-color: #d3d3d4;
            color: #41464b;
        }}
        .alert-light {{
            background-color: #fefefe;
            border-color: #fdfdfe;
            color: #636464;
        }}
        /* Odoo banner layout (wraps the alert div) */
        .o_editor_banner {{
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }}
        /* The emoji/icon cell does not render in wkhtmltopdf — hide it to
           avoid the □ (missing-glyph) placeholder appearing in the PDF. */
        .o_editor_banner_icon {{
            display: none;
        }}
        .o_editor_banner_content {{
            flex: 1;
            width: 100%;
            padding: 0 0.75rem;
        }}

        /* ── Checklist (from addons/web/.../report.scss verbatim) ────*/
        ul.o_checklist > li {{
            list-style: none;
            position: relative;
            margin-left: 20px;
        }}
        ul.o_checklist > li:not(.oe-nested)::before {{
            content: '';
            position: absolute;
            left: -20px;
            display: block;
            height: 14px;
            width: 14px;
            top: 1px;
            border: 1px solid;
        }}
        ul.o_checklist > li.o_checked::after {{
            content: "✓";
            position: absolute;
            left: -18px;
            top: -1px;
        }}
        li.oe-nested {{
            display: block;
        }}

        /* ── Manual page break ───────────────────────────────────────
           .o_page_break <div> inserted by the Page Break powerbox command.
           In wkhtmltopdf this forces a new page; the visual decoration is
           zeroed so no extra whitespace or lines appear in the PDF. */
        .o_page_break {{
            page-break-before: always;
            border: none !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 0 !important;
            line-height: 0 !important;
        }}
        .o_page_break_label {{
            display: none;
        }}
    </style>
</head>
<body>
{clean_body}
</body>
</html>"""

        # Build the header document and assemble wkhtmltopdf arguments.
        #
        # ``data-report-margin-top`` / ``data-report-margin-bottom`` are the
        # only top/bottom keys that _build_wkhtmltopdf_args maps to CLI flags.
        #
        # ``data-report-header-spacing`` overrides the paper format's
        # ``header_spacing`` field.  The Odoo A4 format ships with 35 mm of
        # header spacing, which far exceeds our margin_top and would push the
        # header out of the page entirely.  We set it to a small fixed value.
        header_doc = self._build_header_html_doc(left, right)
        specific_paperformat_args = {
            "data-report-margin-top": top,
            "data-report-margin-bottom": bottom,
        }
        if header_doc:
            # 2 mm gap between the bottom of the header and the body content.
            specific_paperformat_args["data-report-header-spacing"] = 2
        return self.env["ir.actions.report"]._run_wkhtmltopdf(
            [full_html],
            header=header_doc,
            landscape=False,
            specific_paperformat_args=specific_paperformat_args,
        )

    def _save_and_download_pdf(self, pdf_bytes):
        """Persist PDF on the template and return a download action."""
        self.write({"pdf_file": base64.b64encode(pdf_bytes)})
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": self.pdf_filename,
                    "type": "binary",
                    "datas": base64.b64encode(pdf_bytes),
                    "mimetype": "application/pdf",
                },
            )
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}/{self.pdf_filename}?download=true",
            "target": "self",
        }

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault("name", _("%s (Copy)", self.name))
        default.setdefault("pdf_file", False)
        return super().copy(default)


# ═══════════════════════════════════════════════════════════════════════
#  TEMPLATE VARIABLE
# ═══════════════════════════════════════════════════════════════════════


class DocumentTemplateVariable(models.Model):
    """A dynamic placeholder inside a document template.

    Users define variables here; each one maps to a ``{{name}}`` tag
    in the HTML body that gets replaced at PDF-export time.
    """

    _name = "document.template.variable"
    _description = "Template Variable"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "document.template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(
        string="Variable Name",
        required=True,
        index=True,
        help="Technical name used in the template as {{variable_name}}",
    )
    label = fields.Char(
        string="Display Label",
        required=True,
        help="Friendly label shown when filling in values",
    )
    variable_type = fields.Selection(
        [
            ("char", "Text"),
            ("text", "Long Text"),
            ("integer", "Whole Number"),
            ("float", "Decimal Number"),
            ("date", "Date"),
            ("selection", "Dropdown"),
        ],
        string="Type",
        default="char",
        required=True,
    )
    default_value = fields.Char(string="Default Value")
    selection_options = fields.Char(
        string="Dropdown Options",
        help="Comma-separated list of choices (only for Dropdown type)",
    )
    required = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    placeholder_tag = fields.Char(
        string="Placeholder",
        compute="_compute_placeholder_tag",
    )

    @api.depends("name")
    def _compute_placeholder_tag(self):
        for var in self:
            var.placeholder_tag = "{{%s}}" % var.name if var.name else ""

    @api.onchange("label")
    def _onchange_label(self):
        """Auto-generate a technical name from the display label."""
        if self.label and not self.name:
            name = self.label.lower().strip()
            name = re.sub(r"[^a-z0-9]+", "_", name)
            self.name = name.strip("_")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("template_id"):
                raise ValidationError(_("Template is required for variables."))

            name = vals.get("name")
            if not name or not str(name).strip():
                raise ValidationError(_("Variable name is required."))

            label = vals.get("label")
            if not label or not str(label).strip():
                raise ValidationError(_("Variable label is required."))

        return super().create(vals_list)

    @api.constrains("template_id", "name")
    def _check_unique_name_per_template(self):
        for var in self:
            if var.template_id and var.name:
                count = self.search_count(
                    [
                        ("template_id", "=", var.template_id.id),
                        ("name", "=", var.name),
                        ("id", "!=", var.id),
                    ],
                )
                if count > 0:
                    raise ValidationError(
                        _(
                            'Variable name "%s" already exists in this template.',
                            var.name,
                        ),
                    )


# ═══════════════════════════════════════════════════════════════════════
#  SUPPORTING MODELS
# ═══════════════════════════════════════════════════════════════════════


class DocumentCategory(models.Model):
    _name = "document.category"
    _description = "Document Category"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer(default=0)
    parent_id = fields.Many2one("document.category", ondelete="cascade")
    child_ids = fields.One2many("document.category", "parent_id")
    document_count = fields.Integer(compute="_compute_document_count")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or not vals.get("name").strip():
                raise ValidationError(_("Category name is required."))
        return super().create(vals_list)

    @api.constrains("name")
    def _check_name_not_empty(self):
        for category in self:
            if not category.name or not category.name.strip():
                raise ValidationError(_("Category name is required."))

    def _compute_document_count(self):
        for cat in self:
            cat.document_count = self.env["document.template"].search_count(
                [("category_id", "=", cat.id)],
            )


class DocumentTag(models.Model):
    _name = "document.tag"
    _description = "Document Tag"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(default=0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or not vals.get("name").strip():
                raise ValidationError(_("Tag name is required."))
        return super().create(vals_list)

    @api.constrains("name")
    def _check_unique_name(self):
        for tag in self:
            if not tag.name or not tag.name.strip():
                raise ValidationError(_("Tag name is required."))
            # Check uniqueness
            count = self.search_count(
                [
                    ("name", "=", tag.name),
                    ("id", "!=", tag.id),
                ],
            )
            if count > 0:
                raise ValidationError(
                    _('Tag name "%s" already exists.', tag.name),
                )
