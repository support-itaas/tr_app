# -*- coding: utf-8 -*-
# Copyright (C) 2020-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'Wizard Car Detail',
    'version': '11.0.1.0',
    'summary': 'Adding Car Detail more',
    'sequence': 1,
    'author': 'ITAAS',
    'description': "Additional car Details",
    'category': 'Wizard Car Detail',
    'website': 'http://www.itaas.co.th',
    'depends': ['wizard_partner', 'fleet', 'sale', 'wizard_coupon'],
    'data': [
        'views/car_detail_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
