# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
# 17/10/2020 - 11.0.3.9
# fix - def create_actual_revenue(self), due to system does not work on coupon order from difference company between tr and dealer
# 04/11/2020 - 11.0.4.0
# add is_create_task for each coupon (product) and manage to create task or not from this flag


{
    'name': 'Upload Coupon Barcode',
    'version': '11.0.1.0',
    'summary': 'Upload Coupon Barcode',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Upload Coupon Barcode",
    'category': 'Coupons',
    'website': 'http://www.technaureus.com',
    'depends': ['wizard_partner', 'wizard_coupon'],
    'data': [

        'views/upload_coupon_barcode_view.xml',
        # 'wizard/wizard_customer_transfer_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
