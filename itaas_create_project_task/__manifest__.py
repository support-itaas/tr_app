{
    'name': 'Itaas Create Project Task',
    'version': '11.0.0.1',
    'category': 'Point of Sale',
    'summary': 'Itaas Create Project Task',
    'sequence': 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    'description': """
    """,
    'depends': ['point_of_sale', 'pad_project','wizard_pos','itaas_promotion_buffet'],
    'data': [
        'views/por_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
