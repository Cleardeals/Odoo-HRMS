# -*- coding: utf-8 -*-

import base64
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DocumentExportWizard(models.TransientModel):
    """Wizard that collects variable values and generates a PDF.

    Opened automatically when the user clicks **Export PDF** on a template
    that contains at least one variable.  Each variable becomes a line in
    the wizard where the user fills in the concrete value.
    """

    _name = 'document.export.wizard'
    _description = 'Export Document as PDF'

    template_id = fields.Many2one(
        'document.template',
        string='Template',
        required=True,
        readonly=True,
        index=True,
    )
    template_name = fields.Char(
        related='template_id.name',
        readonly=True,
    )
    line_ids = fields.One2many(
        'document.export.wizard.line',
        'wizard_id',
        string='Variables',
    )
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview_html',
        sanitize=False,
    )

    # ── Defaults ──────────────────────────────────────────────────────
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        template_id = (
            res.get('template_id')
            or self._context.get('default_template_id')
        )
        if template_id:
            template = self.env['document.template'].browse(template_id)
            if template.exists():
                res['template_id'] = template.id
                lines = []
                for var in template.variable_ids.sorted('sequence'):
                    lines.append((0, 0, {
                        'variable_id': var.id,
                        'name': var.name,
                        'label': var.label,
                        'variable_type': var.variable_type,
                        'value_char': var.default_value or '',
                        'is_required': var.required,
                        'selection_options': var.selection_options or '',
                    }))
                res['line_ids'] = lines
        return res

    # ── Preview ───────────────────────────────────────────────────────
    @api.depends('line_ids.value_char')
    def _compute_preview_html(self):
        for wiz in self:
            if wiz.template_id and wiz.template_id.html_content:
                wiz.preview_html = wiz._render_html()
            else:
                wiz.preview_html = (
                    '<p style="color:#999;">No content to preview.</p>'
                )

    # ── Generate ──────────────────────────────────────────────────────
    def action_generate_pdf(self):
        """Validate inputs, render variables, generate PDF and download."""
        self.ensure_one()

        # Validate required fields
        missing = self.line_ids.filtered(
            lambda l: l.is_required and not l.value_char
        )
        if missing:
            names = ', '.join(missing.mapped('label'))
            raise ValidationError(
                _('Please fill in the required fields: %s') % names
            )

        rendered_html = self._render_html()
        pdf_bytes = self.template_id._generate_pdf_bytes(rendered_html)

        # Persist last-generated PDF on the template
        self.template_id.write({
            'pdf_file': base64.b64encode(pdf_bytes),
        })

        # Create a downloadable attachment
        filename = self.template_id.pdf_filename or 'document.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d/%s?download=true' % (
                attachment.id, filename,
            ),
            'target': 'self',
        }

    # ── Helpers ───────────────────────────────────────────────────────
    def _render_html(self):
        """Replace all ``{{variable}}`` placeholders with user values."""
        html = self.template_id.html_content or ''
        for line in self.line_ids:
            if line.name:
                pattern = r'\{\{\s*' + re.escape(line.name) + r'\s*\}\}'
                html = re.sub(pattern, (line.value_char or ''), html)
        return html


class DocumentExportWizardLine(models.TransientModel):
    """One variable line inside the export wizard."""

    _name = 'document.export.wizard.line'
    _description = 'Export Wizard – Variable Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'document.export.wizard',
        ondelete='cascade',
    )
    variable_id = fields.Many2one(
        'document.template.variable',
        string='Variable',
    )
    name = fields.Char('Variable Name')
    label = fields.Char('Label')
    variable_type = fields.Selection(
        [
            ('char', 'Text'),
            ('text', 'Long Text'),
            ('integer', 'Whole Number'),
            ('float', 'Decimal Number'),
            ('date', 'Date'),
            ('selection', 'Dropdown'),
        ],
        string='Type',
        default='char',
    )
    value_char = fields.Char('Value')
    is_required = fields.Boolean('Required')
    selection_options = fields.Char('Dropdown Options')
    sequence = fields.Integer(default=10)
