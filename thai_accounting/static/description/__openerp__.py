# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Thailand Accounting Enhancement",
    "category": 'Accounting',
    'summary': 'Thailand Accounting Enhancement.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','sale','stock','product','purchase'],
    "data": [

        'sequence.xml',
        #security
        'security/ir.model.access.csv',
        'security/security_group.xml',
        #view
        'views/account_payment_view.xml',
        'views/account_journal_view.xml',
        'views/account_tax_view.xml',
        'views/account_move_view.xml',
        'views/account_account_view.xml',
        'views/customer_billing_view.xml',
        'views/account_invoice_view.xml',
        'views/bahttxt_convert_view.xml',
        'views/sale_order_view.xml',
        # 'views/product_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/stock_valuation_history_view.xml',
        'views/report_stockhistory.xml',
        'views/tax_report_view.xml',
        'views/report_pnd3.xml',
        'views/report_pnd53.xml',
        'views/report_pnd53at1.xml',
        'views/report_taxsummary.xml',
        'views/report_billing.xml',
        #report
        'report/report_reg.xml',
        'report/report_generalledger.xml',
        'report/journal_daily_report.xml',
        'report/journal_summary_report.xml',
        'report/teejai_report.xml',
        'report/teejai_report_journal.xml',
        'report/teejai_report02.xml',
        'report/teejai_report02_journal.xml',
        'report/report_financial.xml',
        'report/product_report.xml',
        'report/sale_tax_report.xml',
        'report/purchase_tax_report.xml',
        # in case for some company define themselves
        # 'report/debitcredit_report.xml',
        # 'report/debitcredit_report01.xml',
        # 'report/debitcredit_report02.xml',
        # 'report/debitcredit_report03.xml',
        # 'report/debitcredit_report04.xml',
        # 'report/debitcredit_report05.xml',
        'report/vendor_report.xml',
        'report/customer_report.xml',
        #wizard
        'wizard/journal_report_view.xml',
        'wizard/creditor_report_view.xml',
        'wizard/receivable_report_view.xml',
        'wizard/purchase_report_view.xml',
        #custom report depend on customer
        # 'report_custom/receipt_report.xml',
        # 'report_custom/report_custom_reg.xml',


    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}