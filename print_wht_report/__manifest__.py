# -*- coding: utf-8 -*-
# Copyright (C) 2020-26/26/2020 ITAAS (Dev K.Book)

{
    'name' : 'Print WHT Report',
    'version': '11.0.0.0.2',
    "category": "Account",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    "depends": ['account',],
    "data": [
        # report
        'reports/report_reg.xml',
        'reports/wht_pnd_53_invoice_report.xml',
        'reports/wht_pnd_3_invoice_report.xml',
        'reports/wht_pnd_53_entries_report.xml',
        'reports/wht_pnd_3_entries_report.xml',
        'reports/wht_pnd_2_entries_report.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
