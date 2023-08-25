# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
#11.0.1.2 แก้ไขการ GENTAX หน้า Invoice
#11.0.1.3 แก้ไขการ การรัน seq ข้าม
#11.0.1.4 - 19/06/2021 - แก้ไขการ Run sequence กรณีที่ไม่ไช่ SH ไม่ต้องหา payment sequence ของ invoice journal
#11.0.1.5 - 29/11/2021 - fix tax report if no order of any session
#11.0.1.6 - 08.09.2021 - fix by add payment sequence name when create from voucher with "voucher_pay_now_payment_create" function
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
    "version": '11.0.0.6',
    "depends": ['account','account_invoicing','sale','product','stock','product','purchase','hr','purchase_discount','account_asset','account_cancel','account_voucher','operating_unit','po_approval'],
    "data": [

        'sequence.xml',
        #security
        'security/security_group.xml',
        'views/res_users_view.xml',
        #view
        # 'views/payment_journal.xml',
        'views/account_payment_view.xml',
        'views/account_journal_view.xml',
        'views/account_tax_view.xml',
        'views/account_move_view.xml',
        'views/account_account_view.xml',
        'views/customer_billing_view.xml',
        # 'views/account_invoice_payment_view.xml',
        ###########need before invoice refund view
        'wizard/account_invoice_debit_refund_view.xml',
        'wizard/account_invoice_without_gl_view.xml',
        'wizard/account_invoice_refund_view.xml',
        'views/account_invoice_view.xml',
        ############################################
        'views/account_tax_invoice_cancel.xml',
        'views/account_tax_invoice_view.xml',
        # 'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/product_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/tax_report_view.xml',
        'views/report_pnd3.xml',
        'views/report_pnd53.xml',
        # 'views/report_pnd53at1.xml',
        'views/report_taxsummary.xml',
        # 'views/report_billing.xml',
        'views/account_asset_asset_view.xml',
        'views/payment_term_view.xml',
        'views/account_cheque_statement_view.xml',
        'views/--sale_order_view.xml',
        'views/account_bank_view.xml',

        ################ Add voucher for cash management
        'views/account_voucher_view.xml',

        ##################includ  ing stock extend #########
        'views/stock_picking_view.xml',
        'views/view_cheque_receive_and_payment.xml',
        # 'views/stock_land_cost_view.xml',
        #report
        'report/report_reg.xml',
        'report/journal_daily_report.xml',
        'report/journal_summary_report.xml',
        'report/teejai_report.xml',
        'report/teejai_report_journal.xml',
        'report/teejai_report02.xml',
        'report/teejai_report02_journal.xml',
        'report/product_report.xml',
        'report/sale_tax_report.xml',
        'report/purchase_tax_report.xml',


        'report/holdingtax3_report.xml',
        'report/holdingtax53_report.xml',
        # in case for some company define themselves
        'report/debitcredit_report.xml',
        'report/debitcredit_report01.xml',
        'report/debitcredit_report02.xml',
        'report/debitcredit_report03.xml',
        'report/debitcredit_report04.xml',
        'report/debitcredit_report05.xml',
        'report/vendor_report.xml',
        'report/customer_report.xml',
        'report/asset_labels_report.xml',
        'report/asset_report.xml',

        #wizard
        'wizard/journal_report_view.xml',
        'wizard/creditor_report_view.xml',
        'wizard/receivable_report_view.xml',

        'wizard/asset_report_view.xml',

        #custom report depend on customer
        #'report_custom/receipt_report.xml',
        #'report_custom/report_custom_reg.xml',
        # 'report/product_stock_report.xml',
        # 'wizard/purchase_report_view.xml',
        # 'report/sale_tax_layout.xml',
        ##### -----------replace by stock extended module-----------
        # 'views/stock_valuation_history_view.xml',
        # 'views/report_stockhistory.xml',
        # 'views/stock_card_view.xml',
        # 'report/product_stock_report.xml',
        ##### -----------replace by stock extended module-----------
        #security
        'security/ir.model.access.csv',


    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
