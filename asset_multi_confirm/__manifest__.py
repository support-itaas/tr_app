# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Asset Multiple Confirm',
    'version': '11.0.1',
    'category': 'Sales',
    'author': 'ITAAS',
    'sequence': 15,
    'summary': 'Asset Multiple Confirm',
    'description': """
Manage asset Multi Confirmation.
    """,
    'author': 'ITAAS',
    'website': 'www.itaas.co.th',
    'license': 'LGPL-3',
    'support': 'info@itaas.co.th',
    'depends': ['account_asset','thai_accounting'],
    'data': [

        'wizard/asset_advance_confirm_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
