# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import api, fields, models
from odoo.tools import float_is_zero


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wallet_balance = fields.Float(compute='_compute_wallet_balance', string="Wallet Balance")

    @api.multi
    @api.depends('debit', 'credit')
    def _compute_wallet_balance(self):
        for partner in self:
            total_wallet_amount = 0
            total_amount_to_show = 0
            # domain = [('account_id', '=', partner.property_account_receivable_id.id),
            #           ('partner_id', '=', partner.id),
            #           ('reconciled', '=', False), ('credit', '>', 0), ('debit', '=', 0),
            #           '|',
            #           '&', ('amount_residual_currency', '!=', 0.0), ('currency_id', '!=', None),
            #           '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id', '=', None),
            #           ('amount_residual', '!=', 0.0)]
            # lines = self.env['account.move.line'].search(domain)
            # currency_id = partner.currency_id
            # if len(lines) != 0:
            #     for line in lines:
            #         if line.currency_id and line.currency_id == partner.currency_id:
            #             amount_to_show = abs(line.amount_residual_currency)
            #         else:
            #             amount_to_show = line.company_id.currency_id.with_context(date=line.date).compute(
            #                 abs(line.amount_residual), partner.currency_id)
            #         if float_is_zero(amount_to_show, precision_rounding=partner.currency_id.rounding):
            #             continue
            #         total_amount_to_show = total_amount_to_show + amount_to_show
            # orders = self.env['pos.order'].search([
            #     ('partner_id', '=', partner.id),
            #     ('state', '=', 'paid'),
            #     ('wallet_amount', '>', 0),
            # ])
            # for order in orders:
            #     total_wallet_amount = total_wallet_amount + order.wallet_amount
            total_wallet_balance = total_amount_to_show - total_wallet_amount
            partner.wallet_balance = total_wallet_balance

    @api.multi
    def action_view_wallet_trans(self):
        self.ensure_one()
        action = self.env.ref('wizard_wallet.action_account_payments_wallet').read()[0]
        action['domain'] = [('add_to_wallet', '=', True), ('partner_id', '=', self.id),
                            ('payment_type', '=', 'inbound')]
        return action
