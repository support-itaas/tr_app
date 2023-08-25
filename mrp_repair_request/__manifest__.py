# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

{
    'name' : 'Repair Request Dev',
    'version': '11.0.1.2.0',
    "category": "Sale",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    "depends": ['mrp_repair',],
    "data": [
        # 'security/ir.model.access.csv',
        # views mrp.repair
        'views/repair_order_view.xml',
        # views maintenance.request
        'views/hr_equipment_request_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
