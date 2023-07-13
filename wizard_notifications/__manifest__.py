# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'Wizard Notifications',
    'version': '11.0.1.4',
    'summary': 'Wizard Notifications',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Wizard Notifications",
    'category': 'Project',
    'website': 'http://www.technaureus.com',
    'depends': ['wizard_project'],
    'data': ['views/notification_view.xml',
             'views/res_partner_view.xml',
             'security/ir.model.access.csv',
             'wizard/send_notification_wizard_view.xml',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
