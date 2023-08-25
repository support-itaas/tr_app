# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
{
    "name": "PR Notification",
    "category": 'General',
    'summary': 'This is PR Notification',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['purchase_request'],
    "data": [
        'security/pr_security.xml',
        # 'view/purchase_request_views.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}