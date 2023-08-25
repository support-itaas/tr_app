# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

{
    'name' : 'Purchase Change Update Line',
    'version': '11.0.1.2.0',
    "category": "Purchase",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    "depends": ['purchase',],
    "data": [
        # 'security/ir.model.access.csv',
        # views purchase.order
        'views/purchase_order_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
