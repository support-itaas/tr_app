# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import UserError


class Stock_picking_batch(models.Model):
    _inherit = 'stock.picking.batch'

    confirm_check = fields.Boolean(string="Cofirm")

    @api.multi
    def confirm_picking(self):
        res = super(Stock_picking_batch, self).confirm_picking()


        for i in self.picking_ids:
            if i.move_lines:
                for o in i.move_lines:
                    if o.move_line_ids:
                        for line in o.move_line_ids:
                            if not line.qty_done:
                                if self.confirm_check == False:
                                    raise UserError(_(' You havent entered done quantities, by clicking on apply Odoo will process all the reserved quantitiesm.'))
                                else:
                                    line.qty_done = line.product_uom_qty


        return res