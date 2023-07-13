# -*- coding: utf-8 -*-


{
    'name': 'Wizard Coupon Production',
    'version': '11.0.1.7',
    'summary': 'Wizard Coupon Production',
    'sequence': 1,
    'author': 'ITAAS',
    'description': "Wizard Coupon Production",
    'category': 'Coupons',
    'website': 'http://www.itaas.co.th',
    'depends': ['wizard_coupon','point_of_sale','wizard_pos', 'itaas_use_coupon'],
    'data': [
        'security/ir.model.access.csv',
        'sequence.xml',

        'views/wizard_coupon_view.xml',
        'views/pos_order_view.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
