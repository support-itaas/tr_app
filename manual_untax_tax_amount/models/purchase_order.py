# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
import time
from odoo.exceptions import UserError


class purchase_order(models.Model):
    _inherit = "purchase.order"

    is_manual_amount = fields.Boolean(string='Manual Amount',default=False)

    new_amount_untaxed = fields.Float(string='New Amount Untaxed')
    new_amount_tax = fields.Float(string='New Amount Tax')
    new_amount_total = fields.Float(string='New Amount Total')

    @api.multi
    def apply_price(self):
        if self.new_amount_untaxed:
            self.amount_untaxed = self.new_amount_untaxed
        if self.new_amount_tax:
            self.amount_tax = self.new_amount_tax
        if self.new_amount_total:
            self.amount_total = self.new_amount_total
        print ('------apply price')
    # @api.multi
    # def action_done(self):
    #     res = super(stock_picking,self).action_done()
    #     if self.picking_type_id.new_sequence_id:
    #         self.picking_number = self.picking_type_id.sudo().new_sequence_id.next_by_id()
    #     return res


