# Document Template Manager

**Internal Tool - For Company Use Only**

## Overview

Internal Odoo 19.0 module for managing dynamic document generation within our HRMS system. This tool enables staff to create templated documents with Jinja2 variables and generate PDFs programmatically.

**Module Name:** `document_template_manager`
**Version:** 19.0.1.0.0
**Author:** Internal Development Team
**Category:** Human Resources/Productivity
**License:** LGPL-3

## Purpose

This internal tool was developed to standardize document generation across the organization. It provides:
- Centralized template management for HR documents, contracts, letters, and reports
- HTML-based template editor with Jinja2 variable support
- Automated PDF generation and versioning
- Email delivery integration
- Audit trail via Chatter integration

## Technical Architecture

### Core Models

#### `document.template`
Primary model for storing document templates.

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Key Fields:**
- `name` (Char): Template name
- `applies_to_model` (Selection): Target Odoo model
- `html_content` (Html): Template body with Jinja2 variables
- `document_type` (Selection): Contract, Invoice, Letter, Report, etc.
- `active` (Boolean): Archive functionality
- `company_id` (Many2one): Multi-company support

**Key Methods:**
- `_get_available_models()`: Returns list of available Odoo models
- `action_generate_document()`: Opens generation wizard
- Template variable computation based on selected model

#### `document.generated`
Stores generated document instances.

**Inherits:** `mail.thread`, `mail.activity.mixin`

**Key Fields:**
- `name` (Char): Document identifier
- `template_id` (Many2one): Source template reference
- `html_content` (Html): Rendered content
- `res_model` / `res_id` (Char/Integer): Related record references
- `state` (Selection): draft/final/archived
- `pdf_file` (Binary): Generated PDF
- `pdf_filename` (Char): PDF file name
- `version` (Char): Version tracking
- `generated_by` (Many2one): User who generated
- `generated_date` (Datetime): Creation timestamp

**Key Methods:**
- `_render_template()`: Jinja2 rendering engine
- `action_generate_pdf()`: PDF generation via wkhtmltopdf
- `action_send_email()`: Email delivery with PDF attachment
- `action_duplicate()`: Version control
- `action_set_final()` / `action_set_draft()`: State management

#### `document.generate.wizard`
Transient model for the document generation wizard interface.

**Fields:**
- `template_id` (Many2one): Selected template
- `res_model` / `res_id`: Target record
- `preview_html` (Html): Live preview
- `include_pdf` (Boolean): Generate PDF option
- `send_email` (Boolean): Email delivery option

**Methods:**
- `_compute_preview()`: Real-time HTML preview
- `action_generate()`: Main generation logic

### Views & UI

- **Templates List View:** Grid with filters (document type, model, state)
- **Template Form View:** HTML editor with variable helper tab
- **Generated Documents:** Kanban + list views with PDF download
- **Generation Wizard:** Multi-step form with preview

### Security

**User Groups:**
- `group_document_user`: Can generate documents from existing templates
- `group_document_manager`: Full CRUD on templates + all documents

**Access Control:**
- Defined in `security/ir.model.access.csv`
- Multi-company record rules in `security/security.xml`
- User-scoped document access (users see only their generated documents unless manager)

**Record Rules:**
- Templates: Multi-company access control
- Generated Documents: User + company filtering

## Installation & Configuration

### Prerequisites

**System Requirements:**
- Odoo 19.0
- Python 3.10+
- wkhtmltopdf 0.12.6+ (for PDF generation)

**Verify wkhtmltopdf:**
```bash
wkhtmltopdf --version
```

**Install if missing:**
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# RHEL/CentOS
sudo yum install wkhtmltopdf
```

### Module Installation

1. Module is located in `custom_addons/document_template_manager`
2. Update apps list: Settings → Apps → Update Apps List
3. Search for "Document Template Manager"
4. Click Install

### Post-Installation

1. **Assign User Groups:**
   - Settings → Users & Companies → Users
   - Edit user → Groups tab
   - Add "Document Manager" or "Document User"

2. **Sample Templates:**
   - Three demo templates are created on installation
   - Review and modify as needed: Documents → Templates → All Templates

3. **Multi-Company Setup:**
   - Templates are company-specific if `company_id` is set
   - Leave blank for company-wide templates

## Template Development

### Jinja2 Syntax Reference

**Context Variables:**
```python
{
    'object': record,           # Current record (res_id)
    'user': self.env.user,     # Current user
    'company': company,         # Current company
    'today': date.today(),      # Today's date
    'now': datetime.now(),      # Current datetime
}
```

**Custom Functions:**
```python
format_date(date_obj)                          # Format date per user locale
format_datetime(datetime_obj)                  # Format datetime
format_amount(amount, currency_id=None)        # Format monetary amount
```

### Template Examples

**Basic Template:**
```html
<div style="font-family: Arial;">
    <h1>${object.name}</h1>
    <p>Generated on: ${format_date(today)}</p>
    <p>By: ${user.name}</p>
</div>
```

**With Conditionals:**
```jinja2
% if object.email:
    <p>Email: ${object.email}</p>
% else:
    <p>No email on file</p>
% endif
```

**With Loops (e.g., Sale Order Lines):**
```jinja2
<table>
% for line in object.order_line:
    <tr>
        <td>${line.product_id.name}</td>
        <td>${line.product_uom_qty}</td>
        <td>${format_amount(line.price_subtotal, object.currency_id)}</td>
    </tr>
% endfor
</table>
```

**Accessing Related Fields:**
```jinja2
${object.partner_id.name}          # Many2one relation
${object.partner_id.street}        # Nested field access
${object.partner_id.country_id.name}  # Multiple levels
```

### Best Practices

1. **Always use conditionals** for optional fields to prevent rendering errors
2. **Use format functions** for dates and amounts
3. **Test templates** with various records before marking as final
4. **Version control** important templates via duplication
5. **Document variables** in template description field

## Usage Workflows

### Creating a Template

1. Navigate to: Documents → Templates → All Templates
2. Click "Create"
3. Fill in:
   - Name: Descriptive template name
   - Applies To: Select target model (e.g., hr.employee, sale.order)
   - Document Type: Category
   - HTML Content: Use editor + Jinja2 syntax
4. Save and test generation

### Generating a Document

**Method 1: From Template**
1. Open template record
2. Click "Generate Document" button
3. Wizard opens with template pre-selected
4. Select target record
5. Preview renders automatically
6. Click "Generate" → Document created + PDF generated

**Method 2: From Wizard Directly**
1. Documents → Generate Document (menu action)
2. Select template
3. Select record
4. Generate

### Document Lifecycle

1. **Draft:** Initial state, editable
2. **Final:** Locked state, archived version
3. **Archived:** Soft-deleted

**Actions:**
- Download PDF: Direct download link
- Send Email: Opens email composer with PDF attached
- Duplicate: Create new version
- Set Final/Draft: State transitions
- Archive: Soft delete

## Testing

### Unit Tests

Test suite located in `tests/` directory:
- `test_document_template.py`: Template CRUD and validation
- `test_pdf_generation.py`: PDF generation functionality
- `test_template_rendering.py`: Jinja2 rendering edge cases
- `test_document_wizard.py`: Wizard workflow

**Run tests:**
```bash
python odoo-bin -c odoo.conf -d test_db -u document_template_manager --test-enable --stop-after-init
```

### Manual Testing Checklist

- [ ] Create template for multiple models
- [ ] Test variable rendering with different record types
- [ ] Verify PDF generation quality
- [ ] Test email delivery
- [ ] Verify multi-company isolation
- [ ] Test user group permissions
- [ ] Verify version control via duplication

## Troubleshooting

### Common Issues

**Issue:** Template variables not appearing in helper tab
**Solution:** Ensure "Applies To" model is selected first

**Issue:** PDF generation fails with error
**Solution:**
```bash
# Check wkhtmltopdf installation
which wkhtmltopdf
# Verify Odoo config has correct path
# Check server logs for detailed error
```

**Issue:** Jinja2 rendering errors
**Solution:**
- Verify syntax: `% endif`, `% endfor` closing tags
- Use conditionals: `% if object.field:`
- Check field exists on model
- Review error message in server logs

**Issue:** Permission denied errors
**Solution:**
- Verify user group assignment
- Check record rules in Security settings
- Ensure multi-company configuration is correct

**Issue:** Empty PDF or broken formatting
**Solution:**
- Validate HTML structure
- Check CSS inline styles (wkhtmltopdf has limited CSS support)
- Test HTML in browser first

### Debugging

**Enable debug mode:**
```python
# In template rendering method
_logger.info("Rendering context: %s", context)
```

**Check generated HTML:**
- Save HTML content before PDF conversion
- Validate in browser
- Check for JavaScript errors (not supported in PDF)

## Data Files

### Demo Data
- `data/document_template_demo.xml`: 3 sample templates (Sales Contract, Welcome Letter, Invoice)

### Security
- `security/security.xml`: User groups and record rules
- `security/ir.model.access.csv`: Model access rights

### Views
- `views/document_template_views.xml`: Template form/list/search
- `views/document_generated_views.xml`: Generated document views
- `views/document_template_menu.xml`: Main menu structure
- `wizard/document_generate_wizard_views.xml`: Wizard interface

## API Reference

### Python API

**Generate document programmatically:**
```python
# Get template
template = self.env['document.template'].browse(template_id)

# Generate document
doc = self.env['document.generated'].create({
    'template_id': template.id,
    'res_model': 'sale.order',
    'res_id': order_id,
})

# Render and generate PDF
doc.action_generate_pdf()

# Send via email
doc.action_send_email()
```

**Batch generation:**
```python
orders = self.env['sale.order'].search([('state', '=', 'sale')])
template = self.env['document.template'].search([('name', '=', 'Invoice Template')], limit=1)

for order in orders:
    self.env['document.generated'].create({
        'template_id': template.id,
        'res_model': 'sale.order',
        'res_id': order.id,
        'name': f"Invoice - {order.name}",
    }).action_generate_pdf()
```

## Maintenance & Support

### Internal Contacts

- **Module Owner:** Internal Development Team
- **Technical Support:** IT Department
- **Feature Requests:** Submit via internal ticket system

### Version History

- **19.0.1.0.0** (2026-02): Initial internal release

### Known Limitations

- wkhtmltopdf CSS support is limited (no Flexbox, Grid, some CSS3 features)
- Large documents (>100 pages) may have memory issues
- Complex JavaScript in templates not supported in PDF
- Image URLs must be accessible from server

## Future Enhancements

- Template approval workflow for compliance
- Batch document generation UI
- Digital signature integration
- Advanced PDF options (custom headers/footers, watermarks)
- Template versioning system
- Document expiry and auto-archival
- Analytics dashboard

## Support

For issues, questions, or contributions:

- Check the documentation in this README
- `document.template` - Template definitions (inherits mail.thread)
- `document.generated` - Generated documents (inherits mail.thread)
- `document.generate.wizard` - Transient model for generation wizard

### Dependencies
- base, web, mail

### Module Information
- **Version**: 19.0.1.0.0
- **License**: LGPL-3
- **Category**: Productivity/Documents
