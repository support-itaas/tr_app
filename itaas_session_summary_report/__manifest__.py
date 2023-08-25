# -*- coding: utf-8 -*-

# Part of ITAAS (www.itaas.co.th)

{
    'name' : 'Itaas Session Summary Report',
    'version' : '11.0.0.1',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Itaas Session Summary Report',
    'summary' : 'Itaas Session Summary Report',
    'description': """
                 Itaas Session Summary Report:
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['stock','base','operating_unit','report_xlsx','thai_accounting'],
    'data' : [
        'wizard/session_summary_report.xml',

        'report/report_reg.xml',
        'report/session_summary_month_report.xml',
    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
