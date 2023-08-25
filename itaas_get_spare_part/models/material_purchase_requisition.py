# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class material_purchase_requisition(models.Model):
    _inherit = 'material.purchase.requisition'

    @api.multi
    def get_spare_part(self):
        self.item_ids.sudo().unlink()
        product_ids = self.env['product.product'].search([('is_dealer_order_available_get', '=', True)])
        for product in product_ids:

            val = {
                'product_id': product.id,
                'product_qty': 0,
                'product_uom_id': product.uom_id.id,
                'requisition_id': self.id,
            }
            self.env['dealer.purchase.order.line'].create(val)