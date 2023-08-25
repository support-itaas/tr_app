# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    exchange_rate = fields.Float('Exchange Rate', digits=(12, 6), states={'draft': [('readonly', False)]})

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        self.exchange_rate = self.purchase_id.exchange_rate
        return super(AccountInvoice, self).purchase_order_change()

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.exchange_rate:
            context = self._context.copy()
            context['exchange_params'] = {'it_currency_rate': self.exchange_rate}
            self.env.context = context
        return super(AccountInvoice, self)._onchange_currency_id()

    @api.multi
    def action_move_create(self):
        if self.currency_id != self.company_id.currency_id and self.exchange_rate:
            context = self._context.copy()
            context['exchange_params'] = {'it_currency_rate': self.exchange_rate}
            self.env.context = context
        return super(AccountInvoice, self).action_move_create()
