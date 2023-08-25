# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class material_purchase_requisition(models.Model):
    _inherit = "material.purchase.requisition"

    def action_confirm_order(self):
        # print('wwwwwwwwwwwwwwww')
        for line in self.item_ids:
            if line.product_id.min_uom_id:
                qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.min_uom_id, rounding_method='HALF-UP')
                if qty < line.product_id.min_quantity and line.product_qty != 0:
                        raise UserError(_('เบิกขั้นต่ำ %s %s %s') % (line.product_id.display_name,line.product_id.min_quantity,line.product_id.min_uom_id.name))
        res = super(material_purchase_requisition, self).action_confirm_order()
        return res


class dealer_purchase_order(models.Model):
    _inherit = 'dealer.purchase.order'

    def action_confirm(self):
        # print('qqqqqqqqqqqqq')
        for line in self.item_ids :
            # print('productttttt:',line.product_id.name)
            if line.product_id.min_uom_id:
                # print('ifffffffffffffffffff')
                qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.min_uom_id, rounding_method='HALF-UP')
                if qty < line.product_id.min_quantity and line.product_qty != 0:
                        raise UserError(_('เบิกขั้นต่ำ %s %s %s') % (line.product_id.display_name,line.product_id.min_quantity,line.product_id.min_uom_id.name))
        res = super(dealer_purchase_order, self).action_confirm()
        return res
