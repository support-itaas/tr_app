# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
#13.0.1.0 - initial compute amount_untaxed
#13.0.1.1 - add function to get income account from sale journal if income account for product or category does not exist
{
    "name": "Itaas Pos Extend",
    'version': '11.0.1.0',
    "category": 'itaas',
    'summary': 'Itaas Pos Extened.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','point_of_sale'],
    "data": [
        'views/pos_views.xml',
        'views/pos_config_views.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
