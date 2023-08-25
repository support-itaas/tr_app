# -*- coding: utf-8 -*-

{
    'name': 'TR POS Backend Functions',
    'version': '11.0.1.2.0',
    'category': 'Apps',
    'summary': "TR POS Backend Functions",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': ['base','point_of_sale','product','hr','sale','tr_extended'],
    'data': [
        'views/product_template_view.xml',
        'views/view_partner_form.xml',
        'views/pos_session_form_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
