# -*- coding: utf-8 -*-

# Part of ITAAS (www.itaas.co.th)
#11.0.1.1 - fix gl by account for department and analytic
{
    'name' : 'Print Report Account',
    'version' : '11.0.1.1',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Quotations',
    'summary' : 'Print Report Account',
    'description': """
                Quotations Report:
                    - Creating Quotations Report
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['sale','base','account','purchase','project','report_xlsx','account_asset','account_update','mrp'],
    'data' : ['report/report_reg.xml',
              'report/report_invoice_inherit.xml',
              'report/account_vat_report.xml',
              'sequence_location.xml',
              # 'views/view_account_vat.xml',
              'views/view_account_financial_view.xml',
              'views/account_move_view.xml',
              'wizard/account_report_paper_balance_view.xml',
              'wizard/account_report_general_ledger_view.xml',
              'wizard/account_report_trial_balance_view.xml',
              'wizard/account_report_aged_partner_balance_view.xml',
              'report/report_trial_balance.xml',
              'report/report_stock_inventory.xml',
              'report/report_paper_balance.xml',
              'report/report_generalledger.xml',
              'report/report_financial.xml',
              'views/account_asset.xml',
              'security/ir.model.access.csv',
              'views/manu_lock_unlock.xml',

              'report/report_asset_report.xml',
              'sequence.xml',

              ],


    #'report/productvariant_report.xml'],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
