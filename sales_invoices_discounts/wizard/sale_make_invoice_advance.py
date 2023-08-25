# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from openerp import api, fields, models, _

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order=order, so_line=so_line, amount=amount)
        if order.discount_view and order.discount_type and order.discount_value:
            res.write({'discount_view': order.discount_view})
            res.write({'discount_type': order.discount_type})
            res.write({'discount_value': order.discount_value})
        return res
