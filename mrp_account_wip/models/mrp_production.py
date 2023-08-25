# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def post_inventory(self):
        # print ('POST INVENTORY BY MRP ACCOUNT WIP')
        for order in self:
            ########### filter out done without consume that need to do (need to cal and apply is_consumed_by_fg)
            moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done' and x.is_consume_by_fg == True)
            print (moves_not_to_do)
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                move.product_uom_qty = move.quantity_done
            moves_to_do._action_done()
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
            order._cal_price(moves_to_do)
            moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done','cancel'))
            moves_to_finish._action_done()
            order.action_assign()
            consume_move_lines = moves_to_do.mapped('active_move_line_ids')
            for moveline in moves_to_finish.mapped('active_move_line_ids'):
                if moveline.product_id == order.product_id and moveline.move_id.has_tracking != 'none':
                    if any([not ml.lot_produced_id for ml in consume_move_lines]):
                        raise UserError(_('You can not consume without telling for which lot you consumed it'))
                    # Link all movelines in the consumed with same lot_produced_id false or the correct lot_produced_id
                    filtered_lines = consume_move_lines.filtered(lambda x: x.lot_produced_id == moveline.lot_id)
                    moveline.write({'consume_line_ids': [(6, 0, [x for x in filtered_lines.ids])]})
                    ######### Add this condition to confirm any material move is really assign to FG
                    ######### if post material first before FG, then WIP occure but next FG post will include this as the cost
                    for consume_move_line in filtered_lines:
                        if consume_move_line.move_id.is_consume_by_fg:
                            continue
                        else:
                            consume_move_line.move_id.write({'is_consume_by_fg': True})

                else:
                    # Link with everything
                    moveline.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
                    ######### Add this condition to confirm any material move is really assign to FG
                    ######### if post material first before FG, then WIP occure but next FG post will include this as the cost
                    for consume_move_line in consume_move_lines:
                        if consume_move_line.move_id.is_consume_by_fg:
                            continue
                        else:
                            consume_move_line.move_id.write({'is_consume_by_fg': True})

        return super(MrpProduction,self).post_inventory()