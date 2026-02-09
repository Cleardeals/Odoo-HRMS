{
    'name': 'ClearDeals HR India Customizations',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'ClearDeals-specific employee form with Indian statutory fields',
    'depends': ['hr', 'hr_employee_updation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}