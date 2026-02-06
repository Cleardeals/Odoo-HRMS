{
    'name': 'ClearDeals HR India Customizations',
    'version': '1.0',
    'category': 'Human Resources',
    'depends': ['hr', 'ohrms_core', 'oh_employee_documents_expiry'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
}