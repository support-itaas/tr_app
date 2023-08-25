# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "HR Working Shift",
    "category": 'HR',
    'summary': 'HR Working Shift',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['hr', 'hr_attendance', 'hr_contract', 'hr_holidays', 'payroll_public_holidays'],
    "data": [
        'views/hr_contract_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}