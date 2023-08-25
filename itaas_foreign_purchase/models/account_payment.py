# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api, _

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    exchange_rate = fields.Float('Exchange Rate', digits=(12, 6))

    @api.multi
    def post(self):
        if self.currency_id != self.company_id.currency_id and self.exchange_rate:
            context = self._context.copy()
            context['exchange_params'] = {'it_currency_rate': self.exchange_rate}
            self.env.context = context
        return super(AccountPayment, self).post()

    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'exchange_rate')
    def _compute_payment_difference(self):
        super(AccountPayment, self)._compute_payment_difference()


class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.model
    def _compute_total_invoices_amount(self):
        """ Compute the sum of the residual of invoices, expressed in the payment currency """
        payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        for inv in self.invoice_ids:
            if inv.currency_id != payment_currency:
                context = self._context.copy()
                context['exchange_params'] = {'it_currency_rate': self.exchange_rate}
                self.env.context = context
        return super(account_abstract_payment, self)._compute_total_invoices_amount()

        # """ Compute the sum of the residual of invoices, expressed in the payment currency """
        # res = super(account_abstract_payment, self)._compute_total_invoices_amount()
        # payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        # total = 0
        # for inv in self.invoice_ids:
        #     if inv.type in ['in_invoice', 'out_refund']:
        #         if self.exchange_rate and self.currency_id != self.company_id.currency_id:
        #             if inv.currency_id == payment_currency:
        #                 total += inv.residual_signed
        #             else:
        #                 total += inv.residual_company_signed * self.exchange_rate
        #             return abs(total)
        # return res

    @api.model
    def default_get(self, fields):
        rec = super(account_abstract_payment, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.invoice':
            return rec
        invoices = self.env['account.invoice'].browse(active_ids)
        exchange_rate = invoices[0].exchange_rate
        rec.update({
            'exchange_rate': exchange_rate
        })
        return rec
