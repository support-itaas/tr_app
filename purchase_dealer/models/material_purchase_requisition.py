# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class material_purchase_requisition(models.Model):
    _inherit = 'material.purchase.requisition'


    item_ids = fields.One2many('dealer.purchase.order.line','requisition_id',string='Requisition Order List')


    @api.multi
    def get_product_list(self):
        self.item_ids.sudo().unlink()
        product_ids = self.env['product.product'].search([('is_dealer_order_available', '=', True)])
        for product in product_ids:

            val = {
                'product_id': product.id,
                'product_qty': 0,
                'product_uom_id': product.uom_id.id,
                'requisition_id': self.id,
            }
            self.env['dealer.purchase.order.line'].create(val)

    @api.multi
    def action_confirm_order(self):
        for line in self.item_ids:
            if line.product_qty > 0.0:
                val = {
                    'product_id': line.product_id.id,
                    'qty': line.product_qty,
                    'uom_id': line.product_uom_id.id,
                    'requisition_id': self.id,
                    'requisition_action': 'internal_picking',
                }
                self.env['requisition.line'].create(val)
            line.sudo().unlink()


class dealer_purchase_order_line(models.Model):
    _inherit = 'dealer.purchase.order.line'


    requisition_id = fields.Many2one('material.purchase.requisition',string='Requisition')