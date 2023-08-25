# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Print Wht To Txt Report",
    "category": 'Report',
    'summary': 'Print Wht To Txt Report.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['thai_accounting'],
    "data": [
        # 'report/report_reg.xml',
        # 'report/receipt_report.xml',
        'views/witholding_report_view.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}