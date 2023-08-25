# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.osv import expression
from openerp.tools import float_is_zero
from openerp.tools import float_compare, float_round
from openerp.tools.misc import formatLang
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, date


import time
import math



class AccountChequeStatement(models.Model):
    _inherit = 'account.cheque.statement'

    is_multiple_cheque = fields.Boolean(string='Multiple Cheque',default=False)

    @api.multi
    def action_validate(self):
        super(AccountChequeStatement,self).action_validate()
        if self.move_new_id:
            cheque_update = {
                'cheque_bank': self.cheque_bank.id,
                'cheque_branch': self.cheque_branch,
                'cheque_number': self.cheque_number,
                'cheque_date': self.cheque_date,
            }
            self.move_new_id.update(cheque_update)


    def cheque_move_line_reverse_get(self):

        if self.payment_id.is_multiple_cheque:
            res = self.cheque_move_line_reverse_get_multi_cheque()
        else:
            res = super(AccountChequeStatement,self).cheque_move_line_reverse_get()

        return res

    def cheque_move_line_reverse_get_multi_cheque(self):
        res = []
        line_id = self.env['account.move.line'].search(
            [('move_id', '=', self.move_id.id), ('account_id.is_cheque', '=', True)], limit=1)
        if not line_id:
            raise UserError(_(
                'Please check your journal and ensure that default "Debit" and "Credit" Account is marked as "Accoun for Cheque"'))

        original_account_id = line_id.account_id

        if self.account_id:
            new_account_id = self.account_id
        else:
            new_account_id = self.journal_id.bank_for_cheque_account_id

        ############### use cheque amount instead of debit and credit amount
        if line_id.debit:
            debit = 0
            credit = self.amount
        else:
            debit = self.amount
            credit = 0

        # print original_account_id.name
        # print new_account_id.name
        if original_account_id and new_account_id:
            # convert exsting line to remove the exist value
            res.append({
                'date_maturity': self.validate_date,
                'partner_id': self.partner_id.id,
                'ref': self.ref,
                'name': self.name,
                'debit': debit,
                'credit': credit,
                'account_id': original_account_id.id,
                'amount_currency': False,
                'currency_id': False,
                'quantity': 1.00,
                'product_id': False,
                'product_uom_id': False,
                'analytic_account_id': False,
                'invoice_id': False,
                'tax_ids': False,
                'tax_line_id': False,
            })

            # new line for new record
            res.append({
                'date_maturity': self.validate_date,
                'partner_id': self.partner_id.id,
                'ref': self.ref,
                'name': self.name,
                'debit': credit,
                'credit': debit,
                'account_id': new_account_id.id,
                'amount_currency': False,
                'currency_id': False,
                'quantity': 1.00,
                'product_id': False,
                'product_uom_id': False,
                'analytic_account_id': False,
                'invoice_id': False,
                'tax_ids': False,
                'tax_line_id': False,
            })

        else:
            raise UserError(_(
                'Please check your journal and ensure that default "Debit" and "Credit" Account is marked as "Accoun for Cheque"'))

        # print res
        return res

    @api.multi
    def action_cancel_state(self):
        self.write({'state': 'cancel'})

    ######################### Cancel need to do carefully due to one cheque is partial
    @api.multi
    def action_cancel(self):
        if self.payment_id.is_multiple_cheque:
            raise UserError(_(
                'Please reverse cheque payment manually and change cheque to cancel state with Cancel state button"'))

        else:
            return super(AccountChequeStatement,self).action_cancel()


