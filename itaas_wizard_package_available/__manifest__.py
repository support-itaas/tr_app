# -*- coding: utf-8 -*-
# Copyright (C) IT as a Service Co., Ltd.(<http://www.itaas.co.th/>).


{
    'name': 'Wizard Package Availability',
    'version': '11.0.1.3',
    'summary': 'Wizard Package',
    'sequence': 1,
    'author': 'ITAAS',
    'description': "Wizard Package",
    'category': 'Coupon and Package',
    'website': 'http://www.itaas.co.th',
    'depends': ['wizard_partner', 'wizard_project', 'wizard_coupon','pos_combo_product','wizard_pos'],
    'data': [

        # 'views/wizard_coupon_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
