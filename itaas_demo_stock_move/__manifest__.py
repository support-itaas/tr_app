# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt.Ltd.(<http://technaureus.com/>).
{
    'name': 'Itaas Demo Stock Move',
    'version': '11.0.0.0',
    'category': 'stock',
    'summary': 'Demo Stock Move',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt Ltd',
    'website': 'http://www.technaureus.com/',
    'description': """
    """,
    'depends': ['sale', 'stock', 'itaas_demo_status'],
    'data': [
        'wizard/stock_move_views.xml',
        'views/sale_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
