# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class SaleAdvanceConfirmOrder(models.TransientModel):
    _name = "sale.advance.confirm.order"
    _description = "Sales Advance Confirm Order"

    # @api.model
    # def _count(self):
    #     return len(self._context.get('active_ids', []))

    # @api.model
    # def _get_advance_payment_method(self):
    #     if self._count() == 1:
    #         sale_obj = self.env['sale.order']
    #         order = sale_obj.browse(self._context.get('active_ids'))[0]
    #         if all([line.product_id.invoice_policy == 'order' for line in order.order_line]) or order.invoice_count:
    #             return 'all'
    #     return 'delivered'
    #
    # @api.model
    # def _default_product_id(self):
    #     product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
    #     return self.env['product.product'].browse(int(product_id))
    #
    # @api.model
    # def _default_deposit_account_id(self):
    #     return self._default_product_id().property_account_income_id
    #
    # @api.model
    # def _default_deposit_taxes_id(self):
    #     return self._default_product_id().taxes_id


    # order_date = fields.Date(string='Order Date')


    @api.multi
    def confirm_order(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        for order in sale_orders.filtered(lambda x: x.state in ('draft','request','validate','sent')):
            order.action_confirm()
        return {'type': 'ir.actions.act_window_close'}

