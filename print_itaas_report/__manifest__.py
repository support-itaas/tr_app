# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Print ITAAS Report',
    'version': '11.0.0.1',
    'price': 'Free',
    'currency': 'THB',
    'category': 'MISC',
    'summary': 'Print Report',
    'description': """
                Report:
                    - Creating Report
Tags:
Report
            """,
    "author": "IT as a Service Co., Ltd.",
    'website': 'www.itaas.co.th',
    'depends': ['account','product','stock', 'purchase','hr','thai_accounting'],
    'data': [
        'report/set6/customer_billing_report.xml',
        'report/set6/report_reg.xml',
        'report/set6/customer_bill_report.xml',
        'report/set6/customer_invoice_receipt_dot.xml',
        'views/account_invoice_view.xml',
    ],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
