# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Account Cheque Extended",
    "category": 'Account',
    'summary': 'Account Cheque Extended.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    "depends": ['account','thai_accounting'],
    "data": [
        'views/account_cheque_statement_view.xml',
        'views/res_partner_bank_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}