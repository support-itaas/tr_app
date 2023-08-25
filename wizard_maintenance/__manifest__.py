# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Wizard Maintenance",
    "category": 'Wizard Maintenance',
    'summary': 'Wizard Maintenance.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.0.4',
    "depends": ['maintenance','mrp_repair'],
    "data": [
        'views/maintenance_report_view.xml',
        'views/repiar_form_view.xml',
        'security/ir.model.access.csv',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}