# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Get Spare Part",
    "category": '',
    'summary': '',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.0.1',
    "depends": ['stock','sales_invoices_discounts','purchase_dealer','itaas_stock_picking'],
    "data": [
        'views/dealer_purchase_order_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}