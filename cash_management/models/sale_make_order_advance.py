# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class sale_advance_payment_inv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment"


    is_one_by_one = fields.Boolean(string='One by One')

    @api.multi
    def create_invoices(self):
        if not self.is_one_by_one:
            return super(sale_advance_payment_inv, self).create_invoices()
        else:
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            sale_orders.action_invoice_create(grouped=True,final=True)
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super(sale_advance_payment_inv,self)._create_invoice(order,so_line,amount)
        print ('---------_create_invoice')
        if invoice.partner_id and invoice.partner_id.bill_to_id:
            print ('--------XXX')
            invoice.bill_to_id = invoice.partner_id.bill_to_id
        return invoice