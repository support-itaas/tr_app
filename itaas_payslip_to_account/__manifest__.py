# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Payslip To Account",
    "category": 'base',
    'summary': 'Itaas Payslip To Account',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    'depends': ['base','hr_period','hr_payroll','hr_extended_add'],
    "data": [
        'views/hr_period_view_form.xml',
        'views/hr_salary_rule_form.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
