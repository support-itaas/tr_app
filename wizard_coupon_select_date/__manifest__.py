# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'Wizard Coupon Select Date',
    'version': '11.0.0.0',
    'summary': 'Wizard Coupon Select Date',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Wizard Coupon Select Date",
    'category': 'Coupons',
    'website': 'http://www.technaureus.com',
    'depends': ['base','wizard_coupon','wizard_pos'],
    'data': [
        'wizard/wizard_coupon_view.xml',
        'views/operating_unit_form.xml',
        'views/coupon_record_yearly_view.xml',
        'views/wizard_coupon_advance_view.xml',


    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
