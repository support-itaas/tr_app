# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Wizard Membership",
    "category": 'Itaas Wizard Membership',
    'summary': 'Itaas Wizard Membership',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.0',
    "depends": ['base','account','wizard_partner','wizard_partner_birthday','wizard_project'],
    "data": [
        'views/member_view.xml',
        'views/birthday_notification.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}