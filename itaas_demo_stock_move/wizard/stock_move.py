# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models


class StockMoveWizard(models.TransientModel):
    _name = 'stock.move.wizard'

    operation_type = fields.Many2one('stock.picking.type', string='Operation Type')

    @api.multi
    def proceed_stock_move(self):
        sale_order_id = self.env['sale.order'].browse(self.env.context.get('active_id'))
        order_line_list = []
        for line in sale_order_id.order_line:
            order_line_data = {'product_id': line.product_id.id, 'product_uom_qty': line.product_uom_qty,
                               'name': line.product_id.name, 'product_uom': line.product_uom.id,
                               'location_id': self.operation_type.default_location_src_id.id,
                               'location_dest_id': self.operation_type.default_location_dest_id.id,
                               }
            order_line_list.append((0, 0, order_line_data))
            route_id = self.env['stock.location.route'].search([('send_demo_route', '=', True)], limit=1)
            line.write({
                'route_id': route_id.id
            })
        delivery = self.env['stock.picking'].create({'partner_id': sale_order_id.partner_id.id,
                                                     'picking_type_id': self.operation_type.id,
                                                     'location_id': self.operation_type.default_location_src_id.id,
                                                     'location_dest_id': self.operation_type.default_location_dest_id.id,
                                                     'origin': sale_order_id.name,
                                                     'demo_sale_id': sale_order_id.id,
                                                     'move_lines': order_line_list})
        return delivery
