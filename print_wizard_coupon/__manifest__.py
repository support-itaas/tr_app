# -*- coding: utf-8 -*-
# Copyright (C) 2020-24/05/2021 ITAAS (Dev K.Book)

{
    'name' : 'Print wizard coupon',
    'version': '11.0.1.2',
    "category": "coupon",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    "depends": ['wizard_coupon','wizard_coupon_production',],
    "data": [
        # security
        'security/security_group.xml',
        # view
        'views/wizard_coupon_view.xml',
        # report
        'report/wizard_coupon_template.xml',
        'report/wizard_coupon_voucher_template.xml',
        'report/wizard_coupon_delivery.xml',


    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
