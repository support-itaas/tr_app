# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.
{
    'name': 'POS Customer Filter',
    'version': '11.0.0.1',
    'summary': 'Filter Customer Shown In POS',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Filter Customer Shown In POS",
    'website': 'http://www.technaureus.com',
    'depends': ['contacts', 'point_of_sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/templates.xml',
            ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
