# -*- coding: utf-8 -*-

# Part of ITAAS (www.itaas.co.th)

{
    'name' : 'Itaas Print Res Partner',
    'version' : '11.0.0.0',
    'price' : '',
    'currency': '',
    'category': '',
    'summary' : '',
    'description': """
                
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['base',],
    'data' : [
        'views/res_partner_view.xml',

        'report/envelope_invoice_report.xml',

    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
