# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
{
    'name': 'News & Promotions',
    'version': '11.0.1.6',
    'summary': 'News and Promotions',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "News and Promotions",
    'category': 'Project',
    'website': 'http://www.technaureus.com',
    'depends': ['wizard_project'],
    'data': ['views/news_promotions.xml',
             'views/home_banner_view.xml',
             'views/promo_banner_view.xml',
             'security/ir.model.access.csv',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
