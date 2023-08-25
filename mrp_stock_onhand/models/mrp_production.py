# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round



class MrpProduction(models.Model):
    _inherit ='mrp.production'


    @api.multi
    def action_assign(self):
        for production in self:
            super(MrpProduction,production).action_assign()
            for move in production.move_raw_ids:
                move.onhand_qty = move.product_id.qty_available
                move.forecast_qty = move.product_id.virtual_available
                move.incomming_qty = move.product_id.incoming_qty
                move.outgoing_qty = move.product_id.outgoing_qty

            return True

class stock_move(models.Model):
    _inherit = 'stock.move'

    onhand_qty = fields.Float(string='On-hand QTY')
    incomming_qty = fields.Float(string='Incoming QTY')
    forecast_qty = fields.Float(string='Forecast QTY')
    outgoing_qty = fields.Float(string='Outgoing QTY')