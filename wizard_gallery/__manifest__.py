# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
{
    'name': 'Wizard-Gallery',
    'version': '11.0.2.0',
    'category': 'Car Care',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd',
    'summary': 'Module to add Gallery under the configuration of Car Care Module',
    'description': 'Module to add Gallery under the configuration of Car Care Module',
    'website': 'https://www.technaureus.com/',
    'depends': ['wizard_project'],
    'data': [
        'security/ir.model.access.csv',
        'views/gallery_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
