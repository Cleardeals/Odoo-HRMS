# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
from io import BytesIO


class DocumentArticle(models.Model):
    """Document Article Model - Knowledge-style document editor."""
    
    _name = 'document.template'
    _description = 'Document Article'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc, id desc'
    
    # Basic Information
    name = fields.Char(
        string='Document Title',
        required=True,
        tracking=True,
        help='Title of the document'
    )
    
    category_id = fields.Many2one(
        comodel_name='document.category',
        string='Category',
        tracking=True,
        help='Document category for organization'
    )
    
    tag_ids = fields.Many2many(
        comodel_name='document.tag',
        string='Tags',
        help='Tags for categorizing and searching documents'
    )
    
    # Content
    html_content = fields.Html(
        string='Content',
        sanitize_attributes=False,
        sanitize_form=False,
        help='Rich text content of the document'
    )
    
    summary = fields.Text(
        string='Summary',
        help='Brief summary or description of the document'
    )
    
    # PDF Export
    pdf_filename = fields.Char(
        string='PDF Filename',
        compute='_compute_pdf_filename'
    )
    
    pdf_file = fields.Binary(
        string='PDF File',
        attachment=True,
        readonly=True,
        help='Generated PDF file'
    )
    
    has_pdf = fields.Boolean(
        string='Has PDF',
        compute='_compute_has_pdf',
        store=True,
        help='Whether a PDF has been generated'
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, the document will be archived'
    )
    
    favorite = fields.Boolean(
        string='Favorite',
        default=False,
        help='Mark as favorite for quick access'
    )
    
    # Company
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company this document belongs to'
    )
    
    @api.depends('name')
    def _compute_pdf_filename(self):
        """Compute PDF filename from document name."""
        for document in self:
            if document.name:
                safe_name = document.name.replace('/', '-').replace('\\', '-')
                document.pdf_filename = f"{safe_name}.pdf"
            else:
                document.pdf_filename = 'document.pdf'
    
    @api.depends('pdf_file')
    def _compute_has_pdf(self):
        """Check if PDF has been generated."""
        for document in self:
            document.has_pdf = bool(document.pdf_file)
    
    def action_generate_pdf(self):
        """Generate PDF from HTML content."""
        self.ensure_one()
        
        if not self.html_content:
            raise ValidationError(_('Cannot generate PDF from empty document.'))
        
        # Use wkhtmltopdf through Odoo's report engine
        try:
            pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf(
                [self.html_content],
                landscape=False,
                specific_paperformat_args={}
            )
            
            self.write({
                'pdf_file': base64.b64encode(pdf_content)
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('PDF generated successfully'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise ValidationError(_('Error generating PDF: %s') % str(e))
    
    def action_download_pdf(self):
        """Download the generated PDF."""
        self.ensure_one()
        
        if not self.has_pdf:
            raise ValidationError(_('No PDF available. Please generate it first.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/document.template/{self.id}/pdf_file/{self.pdf_filename}?download=true',
            'target': 'self',
        }
    
    def action_duplicate(self):
        """Duplicate the current document."""
        self.ensure_one()
        new_doc = self.copy()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'document.template',
            'res_id': new_doc.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def copy(self, default=None):
        """Override to add 'Copy' suffix to duplicated documents."""
        default = dict(default or {})
        default.setdefault('name', _('%s (Copy)', self.name))
        default.setdefault('pdf_file', False)  # Don't copy PDF
        return super().copy(default)
    
    def action_toggle_favorite(self):
        """Toggle favorite status."""
        for document in self:
            document.favorite = not document.favorite


class DocumentCategory(models.Model):
    """Document categories for organization."""
    
    _name = 'document.category'
    _description = 'Document Category'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    color = fields.Integer(
        string='Color Index',
        default=0
    )
    
    parent_id = fields.Many2one(
        comodel_name='document.category',
        string='Parent Category',
        ondelete='cascade'
    )
    
    child_ids = fields.One2many(
        comodel_name='document.category',
        inverse_name='parent_id',
        string='Subcategories'
    )
    
    document_count = fields.Integer(
        string='Documents',
        compute='_compute_document_count'
    )
    
    @api.depends('name')
    def _compute_document_count(self):
        """Count documents in this category."""
        for category in self:
            category.document_count = self.env['document.template'].search_count([
                ('category_id', '=', category.id)
            ])


class DocumentTag(models.Model):
    """Tags for document organization."""
    
    _name = 'document.tag'
    _description = 'Document Tag'
    _order = 'name'
    
    name = fields.Char(
        string='Tag Name',
        required=True,
        translate=True
    )
    
    color = fields.Integer(
        string='Color Index',
        default=0
    )
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tag name must be unique!')
    ]
