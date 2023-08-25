# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
{
    'name': 'Itaas Websale Reply',
    'version': '10.0.0.1',
    'sequence': 1,
    'category': 'Website',
    'summary': 'Websale Reply',
    'author': 'Technaureus Info Solutions Pvt.Ltd',
    'website': 'http://www.technaureus.com/',
    'description': """
        """,
    'depends': ['base','portal', 'website_mail'],
    'data': [
        'views/website_mail_message_template.xml',
        'views/website_portal_sale_templates.xml',
        'views/websale_wizard_view_from.xml',
        'security/ir.model.access.csv',

    ],
    'images': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
