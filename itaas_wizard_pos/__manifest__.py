# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Wizard Pos",
    "category": 'Itaas Wizard Pos',
    'summary': 'Itaas Wizard Pos',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','account','point_of_sale'],
    "data": [
        'views/pos_report_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}