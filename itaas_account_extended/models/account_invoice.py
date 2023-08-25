# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from datetime import date, datetime
from odoo.tools import float_compare, float_is_zero

class Account_invoice(models.Model):
    _inherit = 'account.invoice'


    number_creditnote = fields.Float(string="Number Credit")

    @api.model
    def create(self, vals):
        print('vals:',vals)
        res = super(Account_invoice, self).create(vals)
        return res
