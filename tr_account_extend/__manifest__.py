# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "TR Account Extend",
    "category": 'Stock',
    'summary': 'TR Account Extended.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','sale','stock','product','purchase'],
    "data": [


        'views/account_invoice_view.xml',
        'views/product_product_view.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}