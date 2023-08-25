# -*- coding: utf-8 -*-

# Part of ITAAS (www.itaas.co.th)

{
    'name' : 'Print Property Counting Report',
    'version' : '13.0.0.2',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Print Property Counting Report',
    'summary' : 'Print Property Counting Report',
    'description': """
                 Print Property Counting Report:
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['stock','base','operating_unit','report_xlsx','thai_accounting'],
    'data' : [
        'wizard/property_counting_report_view.xml',

        'report/report_reg.xml',
    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
