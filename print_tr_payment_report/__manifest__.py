# -*- coding: utf-8 -*-
# Part of ITAAS (www.itaas.co.th)
#11.0.1.0 - 24/06/2021 - print payment report for tax invoice and receive

{
    'name' : 'Print Tr Payment Report',
    'version' : '11.0.1.11',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Tax Invoice/Receipt',
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

        'report/tax_invoice02_report.xml',

    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
