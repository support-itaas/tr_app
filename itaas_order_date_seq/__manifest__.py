# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Itaas.
# 11.0.1.1 :  button Wht reference
{
    'name': 'Itaas Order Date Seq',
    'version': '11.0.1.1',
    'category': 'sale',
    'summary': 'Itaas Order Date Seq',
    'sequence': 1,
    'author': 'Itaas Ltd',
    'website': 'http://www.itaas.co.th/',
    'description': """
    """,
    'depends': ['stock','purchase','account'],
    "demo": [],
    "data": [
        'views/invoice_supplier_button.xml',
        # "security/ir.model.access.csv",
        # "views/view_purchase_order_type.xml",
        # "views/view_purchase_order.xml",
        # "views/view_res_partner.xml",
        # "data/default_type.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
