# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Account Order and Sale Order",
    "category": 'itaas',
    'summary': 'Evaluation Supplier Extended.',
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','account'],
    "data": [
        'views/account_menu.xml',
        'views/account_form.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}