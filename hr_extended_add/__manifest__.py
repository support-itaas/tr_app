# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  ITAAS

{
    'name': 'HR Extended Add',
    'version': '1.0',
    'category': 'Humance Resource',
    'sequence': 1,
    'summary': 'Humance Resource',
    'description': """
Human resource extended    """,
    'website': 'http://www.itaas.co.th/',
    'author': 'IT as a Service Co., Ltd.',
    'depends': ['hr','tr_extended','base','resource'],

    'data': [
        'security/ir_rule.xml',
        'security/user_groups.xml',
        'hr_payroll_view.xml',
        'views/hr_salary_rule_view.xml',
        'views/hr_contract_view.xml',
        'views/res_patner_view.xml',
        'views/hr_period_view.xml',
        'views/hr_holidays_view.xml',

        'data/message_data.xml',
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
