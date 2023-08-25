# -*- coding: utf-8 -*-
# Copyright (C) 2021-today ITAAS (Dev K.IT)

{
    'name': 'Itaas Product Movement Report',
    'version': '12.0.0.4',
    'category': 'stock',
    'author': 'ITAAS',
    'sequence': 0.00,
    'description': """
    """,
    'author': 'ITAAS',
    'website': 'www.itaas.co.th',
    'license': 'LGPL-3',
    'support': 'info@itaas.co.th',
    'depends': ['stock','stock_extended'],
    'data': [

        'wizard/wizard_product_movement_report_view.xml',
        'report/product_movement_report.xml',
        'report/report_reg.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
