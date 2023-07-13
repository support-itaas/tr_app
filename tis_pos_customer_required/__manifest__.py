# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

{
    'name': 'TIS POS Required/Mandatory Customer ',
    'version': '11.0.0.0',
    'category': 'Point of Sale',
    'summary': 'POS customer required or Mandatory',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
    'description': """
    This apps give option to make customer mandatory for the order.
    """,
    'price': 30,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_config_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
    'images': ['images/pos_customer_main_screenshot.png']
}
