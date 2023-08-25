# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Sale Order Button',
    'version': '1.0',
    'category': 'Report Address Custom',
    'sequence': 1,
    'summary': 'Report Address Custom.',
    'description': """
                Report Address Custom""",
    'website': 'www.itaas.co.th/',
    'author': 'IT as a Service Co., Ltd',
    'depends': ['base','sale','purchase','account','thai_accounting'],
    'data': [
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/account_order.xml',
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
