# -*- coding: utf-8 -*-

{
    'name': 'MRP Extended',
    'version': '11.0.1.2.0',
    'category': 'Apps',
    'summary': "TR Functions",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': [
        'sale','purchase','base','account','mrp','stock','thai_accounting','bi_material_purchase_requisitions','hr'],
    'data': [


        'views/view_inventory.xml',


    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
