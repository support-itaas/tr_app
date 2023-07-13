# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'Help and Support',
    'version': '11.0.0.7',
    'summary': 'Help and Support for branch configuration',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Help and Support for branch configuration",
    'category': 'Project',
    'website': 'http://www.technaureus.com',
    'depends': ['wizard_project'],
    'data': [
        'views/help_support_view.xml',
        'views/terms_conditions_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
