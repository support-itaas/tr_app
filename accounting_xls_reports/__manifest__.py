# -*- coding: utf-8 -*-

{
    "name": "XLS Reports For Accounting",
    "version": "0.1",
    "author": "KTree Computer Solutions India (P) Ltd",
    "category": "Generic Modules/Accounting",
    "description": """XLS Reports For Accounting  """,
    "summary" : """ Accounting Reports in XLS (General Ledger, P/L, Trail Balance, Balance Sheet, Partner Ledger, Aged Partner Balance)""",
    "website": "https://ktree.com",
    'images': ['images/main-screenshot.png'],
    "depends": ['base','account'],
    "data": [
             "views/account_view.xml", 
             "views/color_theme_view.xml",
             "security/ir.model.access.csv"
            ],
    "qweb":[],
    'demo': [],
    'test': [],
    "active": False,
    "installable": True,
    'application': True,
    'price':70.00,
    'currency':'EUR',
    'license':'AGPL-3'
}
