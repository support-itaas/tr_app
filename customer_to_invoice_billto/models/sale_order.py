# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(sale_order,self).action_invoice_create(grouped,final)
        for order in self:
            if order.partner_id and order.partner_id.bill_to_id and order.invoice_ids:
                for invoice in order.invoice_ids:
                    if not invoice.bill_to_id:
                        invoice.bill_to_id = order.partner_id.bill_to_id
        return res