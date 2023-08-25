# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas POS Promotion Buffet",
    "category": 'Itaas Wizard POS Promotion',
    'summary': 'Itaas Wizard POS Promotion',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    "depends": ['base','account','pos_voucher','wizard_pos','wizard_partner'],
    "data": [
        'views/pos_order_view.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}