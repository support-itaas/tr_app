# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Cash Management WHT",
    "category": 'Account',
    'summary': 'Cash Management WHT',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    "depends": ['base','account','thai_accounting','cash_management'],
    "data": [
        'views/account_voucher_view.xml',
        'reports/wht_pnd_3_voucher_report.xml',
        'reports/wht_pnd_53_voucher_report.xml',
        'reports/report_reg.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}