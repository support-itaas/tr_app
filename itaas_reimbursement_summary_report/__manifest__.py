# -*- coding: utf-8 -*-

# Part of ITAAS (www.itaas.co.th)

{
    'name' : 'Itaas Vehicles In Service Report',
    'version' : '13.0.0.1',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Itaas Vehicles In Service Report',
    'summary' : 'Itaas Vehicles In Service Report',
    'description': """
                 Itaas Vehicles In Service Report:
Tags: 
Stock report
            """,
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['stock','base','operating_unit','report_xlsx','thai_accounting'],
    'data' : [
        # 'wizard/vehicles_in_service_report_view.xml',

        'report/report_reg.xml',
    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
