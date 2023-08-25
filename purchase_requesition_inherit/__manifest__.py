# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Purchase Reqestition Inherit',
    'version': '1.0',
    'category': 'Purchase Reqestition Inheritm',
    'sequence': 1,
    'summary': 'Purchase Reqestition Inherit.',
    'description': """
                Purchase Reqestition Inherit""",
    'website': 'www.itaas.co.th/',
    'author': 'IT as a Service Co., Ltd',
    'depends': ['base','hr','purchase','bi_material_purchase_requisitions','purchase_dealer'],
    'data': [
        'views/employee_inherit_add.xml',
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
