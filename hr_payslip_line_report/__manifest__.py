# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  ITAAS

{
    'name': 'HR Payslip Line Report',
    'version': '11.0.1.0',
    'category': 'Humance Resource',
    'sequence': 1,
    'summary': 'Humance Resource',
    'description': """
Human resource extended    """,
    'website': 'http://www.itaas.co.th/',
    'author': 'IT as a Service Co., Ltd.',
    'depends': [
        'hr',
        'hr_payroll',
        'hr_extended',
        'hr_period',
    ],
    'data': [

        'views/hr_payroll_view.xml',


    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
