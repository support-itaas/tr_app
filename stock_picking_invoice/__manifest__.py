# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Inventory Saleorder inherit",
    "category": 'Inventory Saleorder inherit',
    'summary': 'Inventory Saleorder inherit.',
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','stock','sale_stock'],
    "data": [
        'views/stock_picking.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}