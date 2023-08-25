
# -*- coding: utf-8 -*-

{
    'name': 'Requests For Quotation',
    'version': '11.0.1.2.0',
    'category': 'Apps',
    'summary': "Requests For Quotation",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': ['purchase','operating_unit','thai_accounting','stock_picking_batch','account'],
    'data': [
        'views/operating_unit_inherit.xml',
        'views/cheque_recieve.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
