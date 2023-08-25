# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
# 11.0.1.4
# show cn as negative amount
########################################PASS#################################
# tested : if no partial then back to work as normal for account.reigster.payment
# tested : if partial and all are invoice, worked as expected
# tested : if partial and all are credit note, worked as expected
########################################FAIL#################################
# fail : if partial and mix between invoice and credit note, does not worked as expected, cn was not considered
##############################################################################
{
    'name': 'Multiple Invoice Payment',
    'version': '11.0.1.4',
    'sequence':1,
    'description': """
       App will allow multiple invoice payment from payment and invoice screen.
        
       Multiple invoice payment, Invoice Multiple payment, Payment , Partial Invoice Payment, Full invoice Payment,Payment write off,   Payment Invoice, 
    Multiple invoice payment
    Credit notes payment
    How can create multiple invoice
Invoice Management 
Odoo Multiple Invoice Payment 
Odoo Invoice Management 
Multiple invoice payment
Credit notes payment
How can create multiple invoice
How can create multiple invoice odoo
Multiple invoice payment in single click
Make multiple invoice payment
Partial invoice payment
Credit note multiple payment
Pay multiple invoice
Paid multiple invoice
Invoice payment automatic
Invoice wise payment
Odoo invoice payment
Openerp invoice payment
Partial invoice
Partial payment
Pay partially invoice
Pay partially payment
Invoice generation
Invoice payment
Website payment receipt
Multiple bill payment
Multiple vendor bill payment
Vendor bill
Manage vendor bill 
Odoo manage vendor bill 
Vendor bill management 
Odoo Vendor bill management
Make Multiple Invoice Payment in single click
Odoo Make Multiple Invoice Payment in single click
Select Multiple invoice then after make payment
Odoo Select Multiple invoice then after make payment
From payment screen select customer and system will load all open invoice to make payment.
Odoo From payment screen select customer and system will load all open invoice to make payment.
Full and Partial Invoice Payment
Odoo Full and Partial Invoice Payment
More then amount payment will be balance into customer account for next invoice redeem
Odoo More then amount payment will be balance into customer account for next invoice redeem
Process Credit Note Multiple Payment
Odoo Process Credit Note Multiple Payment
Select Multiple Invoice 
Odoo select multiple Invoice 
Manage selection of Multiple Invoice 
Odoo Manage Selection of Multiple Invoice 
Payment process 
Odoo payment process 
Paid multiple Invoice
Odoo Paid Multiple Invoice 
Multiple Invoice Payment 
Odoo Multiple Invoice Payment 
Manage multiple Invoice 
Odoo Manage Multiple Invoice 
Invoice Payment Journal Entry 
Odoo Invoice Payment Journal Entry 
Manage Invoice Payment Journal Entry 
Odoo Manage Invoice Payment Journal Entry 
           
    """,
    "category": 'Generic Modules/Accounting',
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',
    'depends': ['account_voucher','thai_accounting'],
    'data': [
        'security/ir.model.access.csv',
        'view/account_payment.xml',
        # 'wizard/bulk_invoice_payment.xml',
        'wizard/account_register_payment.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':35.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
