# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Bill to Configuration',
    'version': '11.0',
    'category': 'Sales',
    'author': 'ITAAS',
    'sequence': 15,
    'summary': 'Partner Bill to Configuration',
    'description': """

    """,
    'author': 'ITAAS',
    'website': 'www.itaas.co.th',
    'license': 'LGPL-3',
    'support': 'info@itaas.co.th',
    'depends': ['base_setup','sale', 'sales_team','thai_accounting'],
    'data': [
        'views/res_partner_view.xml',
        'wizard/sale_make_order_advance_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
