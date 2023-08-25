# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class InheritAccountInvoicelie(models.Model):
    _inherit = 'account.invoice.line'

    new_name_for_1_case = fields.Char(string="Name" ,related='invoice_id.number')
