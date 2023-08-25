from odoo import api, fields, models


class saleOrder(models.Model):
    _inherit = 'sale.order'


    manual_amount = fields.Boolean(string='Maunal Amount')


class PurchaseOrder1(models.Model):
    _inherit = 'purchase.order'

    manual_amount = fields.Boolean(string='Maunal Amount')

class AccountOrder1(models.Model):
    _inherit = 'account.invoice'

    manual_amount = fields.Boolean(string='Maunal Amount')

class CustomberOrder1(models.Model):
    _inherit = 'customer.billing'

    manual_amount = fields.Boolean(string='Maunal Amount')




