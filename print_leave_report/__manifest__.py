# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions(<http://www.technaureus.com/>).
{
    "name": "Print Leave report",
    "version": '12.0.0.1',
    "sequence": 1,
    "category": 'Report',
    "summary": 'Print Leave report',
    "author": "IT as a Service Co., Ltd.",
    "website": 'www.itaas.co.th',
    "description": """ """,
    "depends": ['base','hr','hr_holidays','calendar', 'resource'],
    "data": [
        # 'report/hr_holidays_templates_inherit.xml',
        # 'wizard/hr_holidays_summary_dept_form.xml',
        'views/view_hr_history_leaves_dept_form.xml',


    ],
    'images': [],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
