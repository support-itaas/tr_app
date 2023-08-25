# -*- coding: utf-8 -*-
# 18/10/2020
# fix issue diff error and not balance when close session - post GL
# add prduct pack compute balance per product and update to gl
{
    'name': 'POS Order Payment',
    'images': [],
    'version': '11.0.2.1',
    'category': 'POS',
    'summary': 'POS Order Payment',
    'author': 'ITAAS',
    'website': 'www.itaas.co.th',
    'depends': [
        'sale',
        'purchase',
        'point_of_sale',
        'pos_combo_product',
        'hr',
        'account',
        'cash_management',
        'operating_unit',
        'account_operating_unit',
    ],
    'data': [
        'views/pos_order_payment.xml',
        'views/hr_department_view.xml',
        'wizard/pos_payment_view.xml',
        'views/account_invoice_view.xml',

    ],
}
