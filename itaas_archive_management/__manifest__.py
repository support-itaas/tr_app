# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Hide Archive Function",
    "category": 'base',
    'summary': 'Itaas Hide Archive Function',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','sale','purchase','wizard_coupon'],
    "data": [
        'security/archive_security.xml',
        'views/template.xml',
        'views/product_view.xml',
        'views/wizard_coupon.xml',
        'views/partner_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
