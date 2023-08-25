# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _,  tools
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_round
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError


class stock_landed_cost(models.Model):
    _inherit = 'stock.landed.cost'

    invoice_reference = fields.Many2one('account.invoice', string='Invoice Reference', copy=False)
    landcost_reference = fields.Char(string='Remark', copy=False)
    manufacturing_ids = fields.Many2many('mrp.production',string='Manufacturing', copy=False)

    @api.multi
    def action_update_cost(self):
        total_cost = 0
        if self.cost_lines and self.picking_ids:
            for picking in self.picking_ids.filtered(lambda x: x.state == 'done'):
                if picking.location_dest_id.usage == 'production':
                    for move in picking.move_lines:
                        total_cost += move.product_uom_qty * move.price_unit

                else:
                    for move in picking.move_lines:
                        total_cost += move.product_uom_qty * move.price_unit * (-1)

            self.cost_lines[0].update({'price_unit': total_cost})



    @api.multi
    def compute_landed_cost(self):
        if self.manufacturing_ids and not self.picking_ids:
            AdjustementLines = self.env['stock.valuation.adjustment.lines']
            AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

            digits = dp.get_precision('Product Price')(self._cr)
            towrite_dict = {}
            for cost in self.filtered(lambda cost: cost.manufacturing_ids):
                total_qty = 0.0
                total_cost = 0.0
                total_weight = 0.0
                total_volume = 0.0
                total_line = 0.0
                all_val_line_values = cost.get_valuation_lines()
                for val_line_values in all_val_line_values:
                    for cost_line in cost.cost_lines:
                        val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                        self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                    total_qty += val_line_values.get('quantity', 0.0)
                    total_weight += val_line_values.get('weight', 0.0)
                    total_volume += val_line_values.get('volume', 0.0)

                    former_cost = val_line_values.get('former_cost', 0.0)
                    # round this because former_cost on the valuation lines is also rounded
                    total_cost += tools.float_round(former_cost, precision_digits=digits[1]) if digits else former_cost

                    total_line += 1

                for line in cost.cost_lines:
                    value_split = 0.0
                    for valuation in cost.valuation_adjustment_lines:
                        value = 0.0
                        if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                            if line.split_method == 'by_quantity' and total_qty:
                                per_unit = (line.price_unit / total_qty)
                                value = valuation.quantity * per_unit
                            elif line.split_method == 'by_weight' and total_weight:
                                per_unit = (line.price_unit / total_weight)
                                value = valuation.weight * per_unit
                            elif line.split_method == 'by_volume' and total_volume:
                                per_unit = (line.price_unit / total_volume)
                                value = valuation.volume * per_unit
                            elif line.split_method == 'equal':
                                value = (line.price_unit / total_line)
                            elif line.split_method == 'by_current_cost_price' and total_cost:
                                per_unit = (line.price_unit / total_cost)
                                value = valuation.former_cost * per_unit
                            else:
                                value = (line.price_unit / total_line)

                            if digits:
                                value = tools.float_round(value, precision_digits=digits[1], rounding_method='UP')
                                fnc = min if line.price_unit > 0 else max
                                value = fnc(value, line.price_unit - value_split)
                                value_split += value

                            if valuation.id not in towrite_dict:
                                towrite_dict[valuation.id] = value
                            else:
                                towrite_dict[valuation.id] += value
            for key, value in towrite_dict.items():
                AdjustementLines.browse(key).write({'additional_landed_cost': value})
            return True
        else:
            return super(stock_landed_cost, self).compute_landed_cost()


    def get_valuation_lines(self):
        lines = []
        if self.picking_ids and not self.manufacturing_ids:
            print ('------1111111111')
            return super(stock_landed_cost,self).get_valuation_lines()

        elif self.manufacturing_ids:
            print('------2222')
            for move in self.mapped('manufacturing_ids').mapped('finished_move_line_ids'):
                # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if move.product_id.valuation != 'real_time' or move.product_id.cost_method != 'fifo':
                    continue
                vals = {
                    'product_id': move.product_id.id,
                    'move_id': move.move_id.id,
                    'quantity': move.qty_done,
                    'former_cost': move.move_id.value,
                    'weight': move.product_id.weight * move.product_qty,
                    'volume': move.product_id.volume * move.product_qty
                }
                lines.append(vals)

            if not lines and self.mapped('picking_ids'):
                raise UserError(_('The selected picking does not contain any move that would be impacted by landed costs. Landed costs are only possible for products configured in real time valuation with real price costing method. Please make sure it is the case, or you selected the correct picking'))
            return lines

        else:
            if not lines:
                raise UserError(_('The selected picking does not contain any move that would be impacted by landed costs. Landed costs are only possible for products configured in real time valuation with real price costing method. Please make sure it is the case, or you selected the correct picking'))
            return lines

    @api.model
    def create(self, vals):
        print('create')
        print('date:',vals.get('date'))
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=vals.get('date')).next_by_code('stock.landed.cost')
        return super(stock_landed_cost, self).create(vals)

