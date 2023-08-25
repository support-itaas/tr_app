# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "Itaas Min Quantity Requisitions",
    "category": '',
    'summary': '',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.0.1',
    "depends": ['stock','sales_invoices_discounts','purchase_dealer','delivery','bi_material_purchase_requisitions'],
    "data": [
        'views/product_template_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}