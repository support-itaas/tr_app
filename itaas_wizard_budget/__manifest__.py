# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
# 11.0.1. - 24/06/2021 - จัด Format ข้อมุล และ ตัวเลข
# 11.0.2. - 11/08/2021 - เมื่อมี acount เดียวกันจะรวมกัน
{
    "name": "Itaas Wizard Budget",
    "category": 'Itaas Wizard Budget',
    'summary': 'Itaas Wizard Budget',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.2',
    "depends": ['base','account','point_of_sale','stock','thai_accounting','analytic','project','wizard_pos','product','cash_management'],
    "data": [
        'views/budget_report_view.xml',
        'views/account_account_view.xml',
        'views/product_product_view.xml',
        'views/bank_post_balance_report_view.xml',
        'views/cheque_balance_report_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}