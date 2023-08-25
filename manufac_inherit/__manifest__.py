# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).
{
    "name": "Manufacturing Inherit",
    "version": '11.0.0.1',
    "sequence": 1,
    "category": 'Sales',
    "summary": 'Manufacturing Inherit',
    "author": "Technaureus Info Solutions Pvt. Ltd.",
    "website": "http://www.technaureus.com/",
    "description": """ """,
    "depends": ['base','mrp','odoo_process_costing_manufacturing','project','wizard_coupon'],
    "data": [
        'views/job_cost_line_tree.xml',
        'views/project_tree.xml',
    ],
    'images': [],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
