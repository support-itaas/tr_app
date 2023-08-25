{
    'name': 'Itaas Foreign Purchase',
    'version': '11.0.0.3',
    'category': 'currency',
    'summary': 'New field Exchange Rate in Purchase Order, Vendor Bill, Vendor Payment, Normal Payment form',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
    'description': """
    """,
    'depends': ['purchase','account'],
    'data': [
        'views/purchase_view.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
