{
    'name': 'Account Asset',
    'version': '11.0.1.2.0',
    'category': 'itaas',
    'summary': "Account Asset Dev",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    'depends': ['base','account_asset','thai_accounting'],
     'data': [
         'views/account_asset.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
