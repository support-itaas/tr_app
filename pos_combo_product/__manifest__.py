# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    'name': 'Pos Combo/Pack',
    'version': '11.0.0.1.0',
    'category': 'Point of Sale',
    'summary': "Point of Sale Combo/Pack",
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt.Ltd.',
    'website': 'http://www.technaureus.com/',
    "support": "support@technaureus.com",
    'license': 'Other proprietary',
    'description': """ 
Allows to create combo/Pack type product.
Combo/Pack: Facility to create Combo/Pack product with list of products.
         """,
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_product_pack_view.xml',
        'views/pos_pack_template_view.xml',
    ],
    'qweb': ['static/src/xml/pos_view.xml'],
    'auto_install': True,
    'installable': True,
    'images': [],

}
