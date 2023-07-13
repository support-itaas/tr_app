# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
{
    'name': 'Wizard Wallet',
    'version': '11.0.2.5',
    'category': 'Accounting',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'summary': ' ',
    'website': 'http://www.technaureus.com/',
    'description': """ 
""",
    'depends': ['account_invoicing', 'wizard_project', 'wizard_pos'],
    'data': [
        'views/res_partner_views.xml',
        'views/wallet_views.xml',
        'data/ir_sequence_data.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
