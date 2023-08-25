# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Itaas Partner Detail Address',
    'version': '11.0.0.0',
    'sequence': 1,
    'category': 'sale',
    'summary': 'Partner Detail Address',
    'author': 'Technaureus Info Solutions Pvt.Ltd',
    'website': 'http://www.technaureus.com/',
    'description': """
This module is for partner detail address
        """,
    'depends': ['sale', 'contacts','base'],
    'data': [
        'views/res_district_view.xml',
        'views/res_subdistrict_view.xml',
        'views/res_partner_view.xml',
        'data/res_country_data.xml',
        'security/ir.model.access.csv',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
