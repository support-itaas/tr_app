# -*- coding: utf-8 -*-

{
    'name': 'Import PO TO SO',
    'version': '11.0.1.2.0',
    'category': 'Apps',
    'summary': "Import PO TO SO",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': [
        'sale','purchase','base','account','stock','product'],
    'data': [
        'views/purchase_import_so_view.xml',
        'views/res_partner_form_inherit.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
