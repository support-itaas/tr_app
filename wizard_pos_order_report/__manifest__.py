# -*- coding: utf-8 -*-
# 18/10/2020
# fix issue diff error and not balance when close session - post GL

{
    'name': 'POS Order Report',
    'images': [],
    'version': '11.0.2.8',
    'category': 'POS',
    'summary': 'POS Order Report',
    'author': 'ITAAS',
    'website': 'www.itaas.co.th',
    'depends': [
        'point_of_sale',
        'wizard_pos',
        'product',
        'wizard_coupon',
        'wizard_project',
    ],
    'data': [
        'views/pos_order_report.xml',
        'views/product_view.xml',
        'views/meter_type_view.xml',
        'security/ir.model.access.csv'
        # 'wizard/pos_payment_view.xml',
    ],
}
