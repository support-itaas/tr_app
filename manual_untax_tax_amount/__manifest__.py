# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
        "name": "Manual Untax Amount and Tax Amount in Sale Order, Purchase Order, Invoice",
    "category": 'repair',
    'summary': 'Item Extended.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '12.0.1',
    "depends": ['stock','purchase','sale','account','product','base','thai_accounting'],
    "data": [

        'views/purchase_order_view.xml',
        'views/sales_order_view.xml',
        'views/account_invoice_view.xml',
        'views/account_voucher.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
