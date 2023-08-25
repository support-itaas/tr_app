# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Stock Picking Validate",
    "category": 'Stock',
    'summary': 'Stock Picking Validate',
    "description": """
        .
    """,
    "version": '11.0.1.0',
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','sale','stock','product','purchase','stock_landed_costs','wizard_coupon'],
    "data": [

        'views/stock_picking_view.xml',
        'data/stock_picking_validate_scheduler.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}