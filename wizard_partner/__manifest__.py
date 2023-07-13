# -*- coding: utf-8 -*-
# Copyright (C) 2020-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'Wizard Partner',
    'version': '11.0.5.8',
    'summary': 'Adding Membership Related Fields',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "This module adds Membership related fields and car Details",
    'category': 'Wizard Partner',
    'website': 'http://www.technaureus.com',
    'depends': ['wizard_project', 'contacts', 'website', 'point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/wizard_partner.xml',
        'views/res_company_views.xml',
        'views/res_country_views.xml',
        'data/partner_data.xml',
        'data/membership_type_data.xml',
        'security/ir.model.access.csv',
        'sequence.xml',
            ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
