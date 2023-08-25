# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Dev Invoice Multi Billing",
    "category": 'Account',
    'summary': 'Dev Invoice Multi Billing',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    "depends": ['base','thai_accounting','dev_invoice_multi_payment'],
    "data": [
        'views/account_register_billing.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}