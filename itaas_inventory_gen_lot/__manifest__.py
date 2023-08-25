{
    'name': 'Inventory Generate Lot',
    'version': '11.0.0.1',
    'category': 'sale',
    'summary': 'Gen LOT',
    'sequence': 1,
    'author': 'ITAAS',
    'website': 'http://www.itaas.co.th/',
    'description': """
    """,
    'depends': ['stock',],
    'data': [
        'views/stock_inventory_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
