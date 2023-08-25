# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

{
    'name' : 'Print Repair Report',
    'version': '11.0.1.2.0',
    "category": "Repair",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    "depends": ['mrp_repair','base'],
    "data": [
        # 'security/ir.model.access.csv',
        # report
        'views/report_reg.xml',
        'views/report_mrprepairorder_inherit.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
