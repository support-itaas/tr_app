# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class MrpProductProduce(models.TransientModel):
    _name = "mrp.product.produce"
    _description = "Record Production"
    _inherit = "mrp.product.produce"

    is_default_consume = fields.Boolean(string='Default Consume',default=True)

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.is_default_consume and self.lot_id:
            for line in self.produce_line_ids:
                if not line.qty_done:
                    line.qty_done = line.qty_to_consume
