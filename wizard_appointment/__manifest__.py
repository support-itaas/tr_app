# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
{
    'name': 'Wizard Appointment',
    'version': '11.0.3.0',
    'sequence': 1,
    'category': 'Project',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': """
Manage appointments and slots.
    """,
    'summary': 'Create Appointments, Slots and manage them according to date and time',
    'website': 'https://www.Technaureus.com',
    'depends': ['wizard_coupon'],
    'data': ['views/wizard_views.xml',
             'data/ir_sequence_data.xml',
             'security/ir.model.access.csv',
             ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
