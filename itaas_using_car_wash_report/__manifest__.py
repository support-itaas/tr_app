# -*- coding: utf-8 -*-

# Part of ITAAS (www.itaas.co.th)

{
    'name' : 'Itaas Using Car Wash Report',
    'version' : '13.0.0.1',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Itaas Using Car Wash Report',
    'summary' : 'Itaas Using Car Wash Report',
    'description': """
                 Itaas Using Car Wash Report:
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['stock','base','operating_unit','report_xlsx','thai_accounting'],
    'data' : [
        'wizard/using_car_wash_report_view.xml',

        'report/report_reg.xml',
    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
