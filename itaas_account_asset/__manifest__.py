# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Accounting Asset Extended",
    "category": 'Asset',
    'summary': 'Asset Extended.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','account_asset','thai_accounting'],
    "data": [

        'views/account_asset_view.xml',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'wizard/asset_report_view.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}