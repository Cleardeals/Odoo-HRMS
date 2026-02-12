# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DocumentGenerateWizard(models.TransientModel):
    """Wizard to generate documents from templates."""
    
    _name = 'document.generate.wizard'
    _description = 'Generate Document Wizard'
    
    # Template Selection
    template_id = fields.Many2one(
        comodel_name='document.template',
        string='Template',
        required=True,
        domain="[('active', '=', True)]",
        help='Select template to use for document generation'
    )
    
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        related='template_id.model_id',
        readonly=True
    )
    
    model_name = fields.Char(
        string='Model Name',
        related='template_id.model_name',
        readonly=True
    )
    
    # Record Selection
    record_selection_method = fields.Selection(
        selection=[
            ('current', 'Current Record'),
            ('manual', 'Select Record'),
        ],
        string='Record Selection',
        default='current',
        required=True,
        help='How to select the record for document generation'
    )
    
    res_id = fields.Integer(
        string='Record ID',
        help='ID of the record to use for document generation'
    )
    
    res_name = fields.Char(
        string='Record Name',
        compute='_compute_res_name',
        help='Name of the selected record'
    )
    
    # Document Details
    document_name = fields.Char(
        string='Document Name',
        required=True,
        help='Name for the generated document'
    )
    
    # Preview
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview_html',
        sanitize=False,
        help='Preview of the generated document'
    )
    
    # Options
    generate_pdf = fields.Boolean(
        string='Generate PDF',
        default=True,
        help='Automatically generate PDF after creating document'
    )
    
    mark_as_final = fields.Boolean(
        string='Mark as Final',
        default=False,
        help='Mark document as final immediately'
    )
    
    @api.depends('model_name', 'res_id')
    def _compute_res_name(self):
        """Compute record name from model and ID."""
        for wizard in self:
            if wizard.model_name and wizard.res_id:
                try:
                    record = self.env[wizard.model_name].browse(wizard.res_id)
                    if record.exists():
                        wizard.res_name = record.display_name
                    else:
                        wizard.res_name = _('Record not found')
                except Exception:
                    wizard.res_name = _('Invalid record')
            else:
                wizard.res_name = False
    
    @api.depends('template_id', 'res_id', 'model_name')
    def _compute_preview_html(self):
        """Generate preview of the document."""
        for wizard in self:
            if wizard.template_id and wizard.model_name and wizard.res_id:
                try:
                    record = self.env[wizard.model_name].browse(wizard.res_id)
                    if record.exists():
                        # Render template with record data
                        document_obj = self.env['document.generated']
                        rendered_html = document_obj._render_template(
                            wizard.template_id.html_content,
                            record
                        )
                        wizard.preview_html = rendered_html
                    else:
                        wizard.preview_html = _('<p>Please select a valid record to preview.</p>')
                except Exception as e:
                    wizard.preview_html = _(
                        '<p style="color: red;">Error generating preview: %s</p>'
                    ) % str(e)
            else:
                wizard.preview_html = _('<p>Please select a template and record to preview.</p>')
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Handle template change."""
        if self.template_id:
            # Try to get current record from context
            active_model = self.env.context.get('active_model')
            active_id = self.env.context.get('active_id')
            
            # Check if active model matches template model
            if active_model == self.template_id.model_name and active_id:
                self.record_selection_method = 'current'
                self.res_id = active_id
                
                # Set default document name
                if active_id:
                    try:
                        record = self.env[active_model].browse(active_id)
                        if record.exists():
                            self.document_name = f"{self.template_id.name} - {record.display_name}"
                    except Exception:
                        self.document_name = self.template_id.name
            else:
                self.record_selection_method = 'manual'
                self.document_name = self.template_id.name
    
    @api.onchange('record_selection_method')
    def _onchange_record_selection_method(self):
        """Handle record selection method change."""
        if self.record_selection_method == 'current':
            active_model = self.env.context.get('active_model')
            active_id = self.env.context.get('active_id')
            
            if active_model == self.template_id.model_name and active_id:
                self.res_id = active_id
        else:
            self.res_id = False
    
    def action_generate_document(self):
        """Generate document from template."""
        self.ensure_one()
        
        # Validate
        if not self.template_id:
            raise ValidationError(_('Please select a template.'))
        
        if not self.res_id:
            raise ValidationError(_('Please select a record.'))
        
        if not self.document_name:
            raise ValidationError(_('Please enter a document name.'))
        
        # Get record
        try:
            record = self.env[self.model_name].browse(self.res_id)
            if not record.exists():
                raise ValidationError(_('Selected record does not exist.'))
        except Exception as e:
            raise ValidationError(_('Error accessing record: %s') % str(e))
        
        # Render template
        document_obj = self.env['document.generated']
        try:
            rendered_html = document_obj._render_template(
                self.template_id.html_content,
                record
            )
        except Exception as e:
            raise UserError(_('Error rendering template: %s') % str(e))
        
        # Create document
        document_vals = {
            'name': self.document_name,
            'template_id': self.template_id.id,
            'html_content': rendered_html,
            'res_model': self.model_name,
            'res_id': self.res_id,
            'state': 'final' if self.mark_as_final else 'draft',
        }
        
        document = self.env['document.generated'].create(document_vals)
        
        # Generate PDF if requested
        if self.generate_pdf:
            document.action_generate_pdf()
        
        # Post message on source record
        try:
            record.message_post(
                body=_('Document generated: <a href="#id=%s&model=document.generated">%s</a>') % (
                    document.id, document.name
                ),
                subject=_('Document Generated')
            )
        except Exception:
            pass  # Source record might not have chatter
        
        # Return action to open created document
        return {
            'name': _('Generated Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.generated',
            'res_id': document.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_preview(self):
        """Preview document without generating."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'document.generate.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
