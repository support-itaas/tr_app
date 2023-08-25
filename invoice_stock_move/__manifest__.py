# -*- coding: utf-8 -*-

{
    'name': 'Invoice Stock Move',
    'version': '11.0.1.2.0',
    'category': 'Apps',
    'summary': "Invoice Stock Move",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': ['base','stock','account','stock_picking_invoice'],
    'data': [
        'views/stock_move_add.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
