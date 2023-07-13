# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
# 17/10/2020 - 11.0.3.9
# fix - def create_actual_revenue(self), due to system does not work on coupon order from difference company between tr and dealer
# 04/11/2020 - 11.0.4.0
# add is_create_task for each coupon (product) and manage to create task or not from this flag
#08/02/2021 - 11.0.5.0 by Jeng
# if product_id in not is_create_task will create deadline = redeem
# create button deadline for deadline != redeem

{
    'name': 'ITAAS Coupon Promotion',
    'version': '11.0.1.3',
    'summary': 'Coupon Promotion',
    'sequence': 1,
    'author': 'ITAAS',
    'description': "Wizard Coupon Promotion",
    'category': 'Coupons',
    'website': 'http://www.itaas.co.th',
    'depends': ['wizard_coupon'],
    'data': [
        'views/wizard_coupon_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
