# -*- coding: utf-8 -*-

{
    'name': 'Itaas Supplier Evaluation',
    'version': '11.0.0.1',
    'category': 'Apps',
    'summary': "Itaas Supplier Evaluation",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': ['product','sale','purchase','base','stock','wizard_project_branch'],
    'data': [

        'views/res_partner_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
