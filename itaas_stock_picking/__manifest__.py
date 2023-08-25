# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Create Stock Picking",
    "category": '',
    'summary': '',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.0.2',
    "depends": ['stock','sales_invoices_discounts'],
    "data": [
        'views/stock_picking_views.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}