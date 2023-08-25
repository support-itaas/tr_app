# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt.Ltd.(<http://technaureus.com/>).
{
    'name': 'Itaas Purchase Request Type',
    'version': '11.0.0.0',
    'category': 'sale',
    'summary': 'Purchase Request Type',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt Ltd',
    'website': 'http://www.technaureus.com/',
    'description': """
    """,
    'depends': ['stock',
                'account',
                'purchase_request'],
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/view_purchase_request.xml",
        "views/view_purchase_request_type.xml",
        'views/stock_warehouse_orderpoint_view.xml',
        # "views/view_users_simple_form.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
