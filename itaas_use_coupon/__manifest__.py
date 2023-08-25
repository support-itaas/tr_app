# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Wizard Use Coupon by Cashier",
    "category": 'Wizard Coupon',
    'summary': 'Use Wizard Coupon',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['wizard_coupon','barcodes'],
    "data": [
        'views/coupon_tree.xml',
        'security/ir.model.access.csv',
        'views/coupon_order_record_view.xml',


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
        # 'report/report_reg.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}