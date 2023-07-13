# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Wizard Spinner Gift',
    'version': '11.0.2.7',
    'category': 'Wizard Spinner Gift',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd',
    'summary': 'Wizard Spinner Gift',
    'description': 'Wizard Spinner Gift',
    'website': 'https://www.technaureus.com/',
    'depends': ['wizard_pos', 'wizard_notifications', 'wizard_coupon', 'portal', 'website'],
    'data': [
        'views/assets.xml',
        'views/spinner_login.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/spinner_gift_website.xml',
        'views/spinner_wheel_template_portal.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
