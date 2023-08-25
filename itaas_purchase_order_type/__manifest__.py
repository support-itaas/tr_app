# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt.Ltd.(<http://technaureus.com/>).
#11.0.1.1
#purchase order type effect to reordering rule need to pass order type in to it as well
{
    'name': 'Itaas Purchase Order Type',
    'version': '11.0.1.1',
    'category': 'sale',
    'summary': 'Purchase Order Type',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt Ltd',
    'website': 'http://www.technaureus.com/',
    'description': """
    """,
    'depends': ['stock',
                'account',
                'purchase'],
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "views/view_purchase_order_type.xml",
        "views/view_purchase_order.xml",
        "views/view_res_partner.xml",
        "views/stock_warehouse_orderpoint_view.xml",
        "data/default_type.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
