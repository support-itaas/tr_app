# -*- coding: utf-8 -*-
{
    'name': "Credit Limit Warning During Sales Order Confirmation",
    'support': 'support@optima.co.ke',

    'summary': """
        Enforces credit limit for credit sales to your customers""",

    'description': """
        enforces credit limit for customers
    """,

    'author': "Optima ICT Services LTD",
    'website': "http://www.optima.co.ke",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales Management',
    'version': '0.3',

    'images': ['static/description/main.png'],
    'price': 49,
    'currency': 'EUR',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/res_config_views.xml',
        'data/mail_template_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
    'application': True,
}
