# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    exchange_rate = fields.Float('Exchange Rate', digits=(12, 6))

    @api.multi
    def _create_picking(self):
        res = super(PurchaseOrder, self)._create_picking()
        pickings = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        for picking in pickings:
            picking.write({'exchange_rate': self.exchange_rate,
                           'currency_id': self.currency_id.id
                           })
        return res

    @api.multi
    def _add_supplier_to_product(self):
        if self.currency_id != self.company_id.currency_id and self.exchange_rate:
            context = self._context.copy()
            context['exchange_params'] = {'it_currency_rate': self.exchange_rate}
            self.env.context = context
        return super(PurchaseOrder, self)._add_supplier_to_product()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)
        if not seller:
            return super(PurchaseOrderLine, self)._onchange_quantity()
        if self.order_id.exchange_rate and self.order_id.currency_id != seller.currency_id:
            context = self._context.copy()
            context['exchange_params'] = {'it_currency_rate': self.order_id.exchange_rate}
            self.env.context = context
        return super(PurchaseOrderLine, self)._onchange_quantity()
