# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Vat by Partner",
    "category": 'Account',
    'summary': 'VAT by Partner',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['account','sale','stock','product','purchase','purchase','inter_company_rules'],
    "data": [

        # 'report/report_stockpicking_operations.xml',
        # 'report/product_stock_report.xml',
        # 'report/report_stockhistory.xml',
        # 'report/product_report.xml',
        # 'views/stock_card_view.xml',
        # 'views/stock_valuation_history_view.xml',
        # 'views/stock_land_cost_view.xml',
        # 'views/product_template_view.xml',
        # 'views/stock_picking_view.xml',
        # 'wizard/inventory_age_wizard.xml',
        'views/res_partner_view.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}