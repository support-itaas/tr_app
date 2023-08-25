# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).
{
    "name": "Itaas Stock Force Date",
    "version": '11.0.0.1',
    "sequence": 1,
    "category": 'Sales',
    "summary": 'Stock Force Date',
    "author": "Technaureus Info Solutions Pvt. Ltd.",
    "website": "http://www.technaureus.com/",
    "description": """ """,
    "depends": ['stock_account','purchase','stock_picking_invoice'],
    "data": [
        'views/stock_picking_views.xml',
        'views/stock_inventory_views.xml',

    ],
    'images': [],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
