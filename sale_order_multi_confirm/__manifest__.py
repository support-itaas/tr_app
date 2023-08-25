# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Quotations/Sales Orders Multiple Confirm',
    'version': '11.0',
    'category': 'Sales',
    'author': 'ITAAS',
    'sequence': 15,
    'summary': 'Quotations/Sales Orders Multiple Confirm',
    'description': """
Manage sales quotations and orders Multi Confirmation.
    """,
    'author': 'ITAAS',
    'website': 'www.itaas.co.th',
    'license': 'LGPL-3',
    'support': 'info@itaas.co.th',
    'depends': ['base_setup','sale', 'sales_team'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'wizard/sale_approval_reason_view.xml',
        # 'views/res_user_views.xml',
        'wizard/sale_make_order_advance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
