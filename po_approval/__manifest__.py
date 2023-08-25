# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "PR & PO Approval",
    "category": 'General',
    'summary': 'This is Po Approval',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '11.0.1.1',
    "depends": ['hr','purchase','purchase_request','itaas_purchase_order_type','stock','stock_picking_invoice','bi_material_purchase_requisitions','sale',],
    "data": [
        'security/user_groups.xml',
        'security/pr_security.xml',
        'view/insert_field_purchase_request_views.xml',
        'view/purchase_approval_matrix_view.xml',
        'security/ir.model.access.csv',

        'view/purchase_order_views.xml',
        'data/mail_template_data.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}