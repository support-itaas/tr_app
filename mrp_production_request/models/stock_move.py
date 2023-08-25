# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends('move_line_ids.qty_done', 'move_line_ids.product_uom_id', 'move_line_nosuggest_ids.qty_done')
    def _quantity_done_compute(self):
        """ This field represents the sum of the move lines `qty_done`. It allows the user to know
        if there is still work to do.

        We take care of rounding this value at the general decimal precision and not the rounding
        of the move's UOM to make sure this value is really close to the real sum, because this
        field will be used in `_action_done` in order to know if the move will need a backorder or
        an extra move.
        """
        for move in self:
            print('move:', move)
            quantity_done = 0
            for move_line in move._get_move_lines():
                print('move_line:', move_line)
                quantity_done += move_line.product_uom_id._compute_quantity(move_line.qty_done, move.product_uom,
                                                                            round=False)

            move.quantity_done = quantity_done
            print('quantity_done:', quantity_done)

    created_mrp_production_request_id = fields.Many2one(
        comodel_name='mrp.production.request',
        string='Created Production Request',
    )

    @api.model
    def create(self, vals):
        if 'production_id' in vals:
            production = self.env['mrp.production'].browse(
                vals['production_id'])
            if production.mrp_production_request_id:
                vals['propagate'] = False
        return super(StockMove, self).create(vals)
