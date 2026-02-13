{
    'name': 'Document Template Manager',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Documents',
    'summary': 'Create document templates with variables and generate professional PDFs',
    'description': """
Document Template Manager
=========================

Create rich document templates with dynamic variables and export them as
professionally formatted PDFs.

Key Features
------------
* **Rich Text Editor** — Full WYSIWYG editor (Notion / Word-style canvas)
* **Template Variables** — Insert {{placeholders}} that are filled in at export time
* **One-click PDF Export** — Fill variable values in a simple form and download the PDF
* **Auto-detect Variables** — Scan your document and create variable definitions automatically
* **Categories & Tags** — Organize templates for easy discovery
* **Favorites** — Star frequently used templates
* **Multi-company** — Company-scoped templates

Ideal for
---------
* Offer letters, experience certificates, relieving letters
* Contracts and agreements
* Company policies and SOPs
* Any document that follows a repeatable format
    """,
    'author': 'ClearDeals',
    'website': 'https://www.cleardeals.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/document_category_data.xml',

        # Report
        'report/document_pdf_report.xml',

        # Wizard
        'wizard/document_export_wizard_views.xml',

        # Views
        'views/document_template_views.xml',
        'views/document_category_views.xml',
        'views/document_tag_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'document_template_manager/static/src/css/document_editor.css',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
