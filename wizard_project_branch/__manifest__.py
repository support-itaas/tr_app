# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).

{
    'name': 'Wizard Project',
    'version': '11.0.2.1',
    'category': 'project',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'summary': ' ',
    'website': 'http://www.technaureus.com/',
    'description': """ 
""",
    'depends': ['base_geolocalize', 'project', 'operating_unit'],
    'data': [
        'views/car_care_views.xml',
        'views/res_partner_views.xml',
        'views/project_views.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
