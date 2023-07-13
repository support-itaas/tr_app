# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

{
    'name': 'Installement Config',
    'version': '11.0.0.1',
    'summary': 'Wizard Shop App',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Installement Config",
    'category': '',
    'website': 'http://www.technaureus.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
