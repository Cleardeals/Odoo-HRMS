# Document Template Manager

## Overview

Odoo 19.0 module for creating and managing document templates with HTML editor, Jinja2 templating, and PDF generation.

## Features

- HTML WYSIWYG editor for template creation
- Jinja2 templating with dynamic variables
- PDF generation using wkhtmltopdf
- Multi-model support (works with any Odoo model)
- Version control for generated documents
- Document states: draft, final, archived
- Email integration with PDF attachments
- Live preview in generation wizard
- Multi-company support
- Chatter integration

## Template Types

Contracts, Invoices, Letters, Reports, Proposals, Certificates, Custom

## Security

- **Document User**: Can generate documents from templates
- **Document Manager**: Can create/edit templates and manage all documents
- Multi-company record rules
- User-specific access control

## Quick Start

1. Install module from Apps menu
2. Assign user groups: Settings → Users & Companies → Users
3. Create templates: Documents → Templates → All Templates
4. Generate documents using the wizard or from records

## Template Variable Syntax

The module uses Jinja2 templating. Here are the available variables and syntax:

#### Available Variables

```jinja2
${object}              # The current record (e.g., partner, sale order)
${user}                # Current user
${company}             # Current company
${today}               # Today's date
${now}                 # Current date and time
```

#### Accessing Record Fields

```jinja2
${object.name}         # Record name
${object.email}        # Email field
${object.street}       # Street address
${object.phone}        # Phone number
```

#### Conditional Logic

```jinja2
% if object.email:
    Email: ${object.email}
% else:
    No email available
% endif
```

#### Loops

```jinja2
% for line in object.order_line:
    Product: ${line.product_id.name} - Qty: ${line.product_uom_qty}
% endfor
```

#### Formatting Functions

```jinja2
${format_date(today)}                          # Format date
${format_datetime(now)}                        # Format datetime
${format_amount(1250.50, object.currency_id)}  # Format amount
```

#### Example Template

```html
<div style="font-family: Arial; padding: 20px;">
    <h1>Sales Contract</h1>
    
    <p>Date: ${today}</p>
    
    <h3>Customer Information</h3>
    <p>
        Name: ${object.name}<br/>
        % if object.email:
        Email: ${object.email}<br/>
        % endif
        % if object.phone:
        Phone: ${object.phone}<br/>
        % endif
    </p>
    
    <p>This contract is between ${company.name} and ${object.name}.</p>
    
    <p>Prepared by: ${user.name}</p>
</div>
```

## Usage

### Generating a Document

There are multiple ways to generate a document:

#### Method 1: From Template

1. Go to **Documents → Templates → All Templates**
2. Open a template
3. Click **Generate Document** button
4. In the wizard:
   - Template will be pre-selected
   - Choosee Document
1. Open template → Click "Generate Document"
2. Select record and options
3. Preview and generate

### Document Actions
- Generate/Download PDF
- Send via Email
- Duplicate (creates new version)
- Mark as Final/Draft
- Archive

### Sample Templates
Includes 3 sample templates: Sales Contract, Welcome Letter, Invoice
#### `document.generated`
- Stores generated documents
- Inherits: `mail.thread`, `mail.activity.mixin`
- Fields: name, template_id, html_content, res_model, res_id, state, pdf_file, version
- Methods: Template rendering, PDF generation, version control, email sending

#### `document.generate.wizard`
- Transient model for document generation wizard
- Features: Template selection, record selection, live preview, options

### Security

- **Groups**: Document User, Document Manager
- **Record Rules**: Multi-company, user-specific access
- **Access Rights**: Defined in ir.model.access.csv

### Dependencies

- `base`: Core Odoo functionality
- `web`: Web interface and HTML widget
- `mail`: Chatter integration and email features

## Troubleshooting

### Template Variables Not Showing

Make sure you've selected a model in the "Applies To" field. The template variables are dynamically generated based on the selected model.

### PDF Generation Fails

Ensure wkhtmltopdf is properly installed on your Odoo server:
```bash
sudo apt-get install wkhtmltopdf
```

### Template Rendering Errors

- Check your Jinja2 syntax
- Ensure variables exist on the record
- Use conditional checks for optional fields
- Review the template variables tab for available fields

### Permission Issues

- Verify user has appropriate group (Document User or Document Manager)
- Check multi-company settings
- Ensure record rules are properly configured

## Roadmap

Potential future enhancements:

- [ ] Template categories and tags
- [ ] Template marketplace/sharing
- [ ] Advanced PDF options (page size, margins, headers/footers)
- [ ] Batch document generation
- [ ] Document signing integration
- [ ] Template approval workflow
- [ ] Document expiry dates
- [ ] Template variables library
- [ ] Document archiving automation
- [ ] Advanced analytics and reporting

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