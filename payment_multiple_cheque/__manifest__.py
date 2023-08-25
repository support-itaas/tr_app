# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Single Payment with Multiple Cheque",
    "category": 'Account',
    'summary': 'To manage singple payment with multiple cheque',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','thai_accounting'],
    "data": [

        'security/ir.model.access.csv',
        # 'report/report_stockhistory.xml',
        # 'report/product_report.xml',
        # 'views/stock_card_view.xml',
        # 'views/stock_valuation_history_view.xml',
        # 'views/stock_land_cost_view.xml',
        'views/account_payment_view.xml',
        'views/account_cheque_statement_view.xml',
        # 'views/stock_picking_view.xml',
        # 'report/report_reg.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}