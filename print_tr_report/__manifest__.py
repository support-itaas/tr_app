# -*- coding: utf-8 -*-
# Part of ITAAS (www.itaas.co.th)
#11.0.1.2 - 25/05/2021 - fix amount before tax in wht report

{
    'name' : 'Print Tr Report',
    'version' : '11.0.1.12',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Quotations',
    'summary' : 'Print Tr Report',
    'description': """
                Quotations Report:
                    - Creating Quotations Report
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['sale','base','account','purchase','project','thai_accounting','tr_extended','account_asset','stock'],
    'data' : [
        'report/teejai_report02_account_move_line.xml',
        'report/teejai_report_journal_move_line_inherit.xml',
        'report/tax_invoice_report_new_receipt.xml',
        'report/holdingtax53_report_new.xml',
        'views/view_inventory.xml',
        'report/holdingtax3_report_new.xml',
        'report/holdingtax53_new.xml',
        'report/report_asset_location_report.xml',
        'views/form_asset.xml',
        'views/line_asset.xml',
        'report/report_reg.xml',
        'report/product_receipt.xml',
        'report/debitcredit_report01_inherit.xml',
        'report/debitcredit_report02_inherit.xml',
        'report/debitcredit_report03_inherit.xml',
        'report/debitcredit_report04_inherit.xml',
        'report/debitcredit_report05_inherit.xml',
        'report/report_production_inven.xml',
        'report/receipt_journal_inherit.xml',
        # 'report/chack_account_cheque_statement.xml',
        'report/cheque_print.xml',
        'views/view_res_bank_form.xml',


        'report/creditnote_report.xml',
        'report/quotation_report.xml',

        'report/purchase_order_report.xml',

        'report/product_bill_report.xml',
        'report/product_bill_report02.xml',

        'report/report_supplier_evaluation.xml',
        'report/supplier_assessment_report.xml',
        'wizard/supplier_evaluation_report_view.xml',

        'report/teejai_report_inherit.xml',
        'report/teejai_report02_inherit.xml',

        'report/teejai_report_journal_inherit.xml',
        'report/teejai_report02_journal_inherit.xml',

        'report/holdingtax53_inherit_report.xml',
        'report/holdingtax3_inherit_report.xml',

        'views/view_move_line_wht_tree_inherit.xml',

        'report/purchase_tax_inherit_report.xml',
        'report/sale_tax_inherit_report.xml',
        'report/report_mo.xml',
        'report/report_production.xml',
        'report/report_chack.xml',

        'report/print_payslip_report.xml',
        'report/debitnote_report.xml',

        'report/report_deliveryslip_inherit.xml',
        'report/tax_invoice01_report.xml',
        'report/tax_invoice02_report.xml',

        'report/debitcredit_report02_bt_inherit.xml',

        # view
        'views/view_purchase_order.xml',
        'views/view_date_demo.xml',
        'views/creditnote_add_taxinvoiceno_report.xml',

    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
