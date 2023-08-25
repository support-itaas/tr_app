# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Wizard Payroll Report",
    "category": 'Wizard Payroll Report',
    'summary': 'Wizard Payroll Report.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.0.2',
    "depends": ['base','hr_payroll','hr','report_hr'],
    "data": [
        'views/payroll_report_view_wizard.xml',
        'security/ir.model.access.csv',
        'report/report_reg.xml',
        'report/wizard_payroll_salary.xml',
        'views/hr_salary_rule_view.xml',
        'views/department_form.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}