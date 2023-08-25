# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Manage Print Cheque",
    "category": 'Account',
    'summary': 'Cheque Management',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','thai_accounting'],
    "data": [

        'views/res_partner_view.xml'

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}