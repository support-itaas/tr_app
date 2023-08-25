# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Personal Tax Management",
    "category": 'General',
    'summary': 'This is Personal Tax Management',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['hr'],
    "data": [

        'views/social_security_view.xml',
        'views/personal_income_tax_view.xml',
        'views/employee_tax_deduction_view.xml',
        'views/hr_contract_view.xml',
        'security/ir.model.access.csv',
        'data/tax_deduction_type.xml',
        # 'data/tax_deduction.xml',


    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}