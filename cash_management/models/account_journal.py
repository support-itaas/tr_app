# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime, date

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    return_cash_account_id = fields.Many2one('account.account',string='Return Cash Account')
    cheque_journal_id = fields.Many2one('account.journal',string='Cheque Journal')
    voucher_sequence_id = fields.Many2one('ir.sequence',string='Voucher Sequence')
    is_cash_management = fields.Boolean(string='เงินสดย่อย')
    is_bank_post = fields.Boolean(string='นำฝาก',default=False)

    payment_sequence_id = fields.Many2one('ir.sequence',string=" Payment Sequence")
    billing_sequence_id = fields.Many2one('ir.sequence',string=" Billing Sequence ")

