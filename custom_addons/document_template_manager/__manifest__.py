# -*- coding: utf-8 -*-
{
    'name': 'Document Editor',
    'version': '19.0.2.0.0',
    'category': 'Productivity/Documents',
    'summary': 'Knowledge-style document editor with rich text and PDF export',
    'description': """
        Document Editor
        ===============
        
        A Knowledge-style document editor for creating, organizing, and sharing
        documents with rich text formatting and PDF export capabilities.
        
        Key Features:
        ------------
        * Rich text WYSIWYG editor (similar to Notion/Confluence)
        * Document categories and tags for organization
        * PDF generation and download
        * Favorite documents for quick access
        * Document archiving
        * Multi-company support
        * Chatter integration for collaboration
        * Full-text search
        * Duplicate documents easily
        
        Perfect for:
        -----------
        * Company policies and procedures
        * Knowledge base articles
        * Meeting notes and documentation
        * Standard operating procedures (SOPs)
        * Project documentation
        * Training materials
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
