{
    'name': 'Itaas Create Dealer Vendor Bill',
    'version': '11.0.0.1',
    'category': 'account',
    'summary': 'Create Vendor Bill',
    'sequence': 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    'description': """
    """,
    'depends': ['account','sale_order_type'],
    'data': [
        'views/account_invoice_view.xml',
        'views/account_account_view.xml',
        'views/account_journal_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
