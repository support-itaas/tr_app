# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

{
    'name' : 'Print POS Report',
    'version': '11.0.0.1',
    "category": "Sale",
    'author': 'IT as a Service Co., Ltd.',
    'website': 'http://www.itaas.co.th/',
    'license': 'AGPL-3',
    "depends": ['point_of_sale',],
    "data": [
        'views/report_saledetails.xml',
        'report/report_receipt.xml',
        'report/report_tax_invoice.xml',
        'report/report_reg.xml',
        'report/report_tax_invoice_pos.xml',
        'report/report_tax_invoice_pos_session.xml',

    ],
    'qweb': [
        'static/src/xml/pos_ticket_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
