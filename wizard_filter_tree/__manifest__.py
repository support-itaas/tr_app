# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'Wizard Filter',
    'version': '11.0.3.8',
    'summary': 'Wizard Filter',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Wizard Filter",
    'category': 'Coupons',
    'website': 'http://www.technaureus.com',
    'depends': ['stock','base'],
    'data': [
        'views/form_wizard_inventory.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
