# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Wizard E-Coupon Warranty",
    "category": 'Wizard Coupon',
    'summary': 'Wizard E-Coupon Warranty',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.1',
    "depends": ['wizard_coupon','product'],
    "data": [
        'wizard/wizard_warranty_view.xml',
        'views/wizard_warranty_record_view.xml',
        'views/product_product_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}