# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    picking_count = fields.Integer(string='Picking Count', compute='_compute_picking_count')

    @api.multi
    def action_sent_demo(self):
        super(SaleOrder, self).action_sent_demo()

        self.ensure_one()
        wizard_form_id = self.env.ref('itaas_demo_stock_move.view_stock_move_wizard').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.move.wizard',
                'view_mode': 'form',
                'views': [(wizard_form_id, 'form')],
                'target': 'new'}

    @api.multi
    def _compute_picking_count(self):
        count_id = self.env['stock.picking'].search([('demo_sale_id', '=', self.id)])
        for order in self:
            order.picking_count = len(count_id)

    @api.multi
    def demo_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.env['stock.picking'].search([('demo_sale_id', '=', self.id)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action
