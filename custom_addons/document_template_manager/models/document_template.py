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
        sanitize_attributes=False,
        sanitize_form=False,
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

    # ── Actions ───────────────────────────────────────────────────────
    def action_export_pdf(self):
        """Export template as PDF.

        If the template contains variables the export wizard is opened so
        the user can fill in every placeholder value.  Otherwise the PDF
        is generated and downloaded straight away.
        """
        self.ensure_one()
        if not self.html_content:
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
    def _generate_pdf_bytes(self, html_body):
        """Wrap *html_body* in a full-page document and run wkhtmltopdf."""
        company = self.env.company
        company_logo = company.logo if company.logo else ""

        # Prepare header HTML with company logo
        header_html = f"""
        <div style="text-align: center; padding: 10px 0; border-bottom: 2px solid #333;">
            {f'<img src="data:image/png;base64,{company_logo.decode()}" style="max-height: 60px; max-width: 200px;" />' if company_logo else f'<h2 style="margin: 0;">{company.name}</h2>'}
        </div>
        """

        # Prepare footer HTML with company info and page numbers
        footer_html = f"""
        <div style="text-align: center; font-size: 10px; padding: 5px 0; border-top: 1px solid #ccc; margin-top: 10px;">
            <div>{company.name} | {company.street or ""} {company.city or ""} | {company.phone or ""}</div>
            <div style="margin-top: 3px;">Page <span class="page"></span> of <span class="topage"></span></div>
        </div>
        """

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        @page {{ margin: 90px 20mm 70px 20mm; }}
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: #333;
            line-height: 1.6;
        }}
        h1 {{ font-size: 24px; }}
        h2 {{ font-size: 20px; }}
        h3 {{ font-size: 16px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td, th {{ padding: 8px; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
        return self.env["ir.actions.report"]._run_wkhtmltopdf(
            [full_html],
            landscape=False,
            specific_paperformat_args={
                "header-html": header_html,
                "footer-html": footer_html,
                "header-spacing": 5,
                "footer-spacing": 5,
            },
        )

    def _save_and_download_pdf(self, pdf_bytes):
        """Persist PDF on the template and return a download action."""
        self.write({"pdf_file": base64.b64encode(pdf_bytes)})
        attachment = self.env["ir.attachment"].create(
            {
                "name": self.pdf_filename,
                "type": "binary",
                "datas": base64.b64encode(pdf_bytes),
                "mimetype": "application/pdf",
            },
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

    @api.depends("name")
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

    @api.constrains("name")
    def _check_unique_name(self):
        for tag in self:
            if tag.name:
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
