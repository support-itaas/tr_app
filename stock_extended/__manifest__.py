# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Stock Inventory Extended",
    "category": 'Stock',
    'summary': 'Stock Inventory Extended.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.0.2',
    "depends": ['account','sale','stock','product','purchase','hr','stock_landed_costs',
                'warehouse_stock_restictions'],
    "data": [

        'report/report_stockpicking_operations.xml',
        'report/product_stock_report.xml',
        'report/report_stockhistory.xml',
        'report/product_report.xml',
        'views/stock_card_view.xml',
        'views/stock_valuation_history_view.xml',
        'views/stock_land_cost_view.xml',
        'views/product_template_view.xml',
        'views/stock_picking_view.xml',
        # 'wizard/inventory_age_wizard.xml',
        'report/report_reg.xml',
        'views/stock_picking_type_view.xml',
        'views/stock_record_yearly_view.xml',
        'security/ir.model.access.csv',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}