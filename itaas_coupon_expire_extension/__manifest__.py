# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Wizard Coupon Extension",
    "category": 'Wizard Coupon',
    'summary': 'Itaas Wizard Coupon Extension',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    "depends": ['base','account','wizard_coupon','wizard_pos','wizard_partner','wizard_partner_birthday','wizard_project'],
    "data": [
        'views/res_partner_view.xml',
        'views/wizard_coupon_view.xml',
        'security/ir.model.access.csv',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}