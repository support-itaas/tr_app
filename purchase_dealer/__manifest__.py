# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
#11.0.1.1-23/10/2021-auto confirm purchase order of dealder order
{
    "name": "Purchase Dealer",
    "category": 'General',
    'summary': 'Purchase Dealer',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.1',
    "depends": ['base','purchase','project','po_approval','inter_company_rules','purchase_dealer_user','bi_material_purchase_requisitions'],
    "data": [
        'security/ir.model.access.csv',
        'view/product_template_views.xml',
        'view/purchase_order_views.xml',
        'view/bi_order_views.xml',
        'view/res_company_views.xml',
        'security/po_dealer_security.xml',


    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}