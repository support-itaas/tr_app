# -*- coding: utf-8 -*-

{
    'name': 'Import Time In Out',
    'version': '11.0.1.2.0',
    'category': 'Apps',
    'summary': "Import Time In Out",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': ['hr','hr_extended','sale'],
    'data': [
        'views/import_time_in_out_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
