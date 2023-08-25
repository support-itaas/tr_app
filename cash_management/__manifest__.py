# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Cash Management",
    "category": 'Account',
    'summary': 'Cash Management',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.1',
    "depends": ['base','account','thai_accounting','operating_unit','print_tr_report','point_of_sale','wizard_pos'],
    "data": [
        'views/point_of_sale_button.xml',
        'views/sale_make_order_advance_view.xml',
        # security
        'security/cash_management_security.xml',
        'security/ir.model.access.csv',
        'views/res_users_view.xml',
        # views
        # 'views/payment_journal.xml',
        'views/account_voucher_view.xml',
        'views/sequence.xml',
        'views/account_journal_view.xml',
        'views/account_account_inherit_view.xml',
        # 'views/account_bank_statement_view.xml', #############remove for now JA-30/05/2020 #######################
        'views/account_bank_statement_line_view.xml', ######### remove above and use this one instead 30/05/2020 ####
        'report/petty_cash_report.xml',
        'views/journal_account_inherit.xml',
        'report/report_reg.xml',
        'report/cash_mangement.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}