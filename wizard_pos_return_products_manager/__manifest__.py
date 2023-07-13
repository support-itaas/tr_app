# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.
{
    'name': 'POS Return Products Access',
    'version': '11.0.0.0',
    'summary': 'Only Managers Can Access Return Products',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Only Managers Can Access Return Products",
    'website': 'http://www.technaureus.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order.xml',
            ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
