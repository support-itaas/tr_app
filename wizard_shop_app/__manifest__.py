# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

{
    'name': 'Wizard Shop App',
    'version': '11.0.3.4',
    'summary': 'Wizard Shop App',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Wizard Shop App",
    'category': '',
    'website': 'http://www.technaureus.com',
    'depends': ['product', 'contacts', 'project', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/system_parameters.xml',
        'data/payment_method.xml',
        'views/project_views.xml',
        'views/service_view.xml',
        'views/pos_order.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
