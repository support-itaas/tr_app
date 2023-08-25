# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

# class AccountInvoiceRegisterLine(models.Model):
#     _name = 'account.invoice.register.line'
#     _rec_name = 'invoice_id'
#
#     invoice_id = fields.Many2one('account.invoice')
#     invoice_amount = fields.Float(string='Amount')
#     to_pay_amount = fields.Float(string='To Pay Amount')
#     register_payment_id = fields.Many2one('account.register.payments',string='Account Register')


class Account_Invoice(models.Model):
    _inherit = 'account.invoice'

    def _get_default_payment_amount(self):
        for invoice in self:
            return invoice.residual_signed

    is_pay_partial = fields.Boolean(string='Pay Partial',default=False)
    to_pay_amount = fields.Float(string='Pay Amount',compute='get_default_payment_amount')

    @api.depends('residual_signed')
    def get_default_payment_amount(self):
        for invoice in self:
            invoice.to_pay_amount = invoice.residual_signed



class register_billing_payments(models.Model):
    _inherit = "register.billing.payments"
    is_multiple_cheque = fields.Boolean(string='Multiple Cheque')
    is_show_invoice = fields.Boolean(string='Show Invoice')
    cheque_line_ids = fields.One2many('payment.cheque.line', 'register_billing_payment_id', string='Cheque')

    def get_payment_vals(self):
        res = super(register_billing_payments, self).get_payment_vals()
        update_vals = {
            'cheque_line_ids': [(4, cheque_line.id, None) for cheque_line in
                                self.cheque_line_ids],
            'is_multiple_cheque': self.is_multiple_cheque,
        }
        res.update(update_vals)
        return res


class account_register_payments(models.Model):
    _inherit = "account.register.payments"

    ################ for multiple check ###########33
    is_multiple_cheque = fields.Boolean(string='Multiple Cheque')
    cheque_line_ids = fields.One2many('payment.cheque.line', 'register_payment_id', string='Cheque')
    ############### for reuse existing cheque ########## Jatupong - 28/04/2020 #########
    is_existing_cheque = fields.Boolean(string='Existing Cheque')
    cheque_existing_reg_id = fields.Many2one('account.cheque.statement',string='Existing Cheque')
    ############### for reuse existing cheque ########## Jatupong - 28/04/2020 #########

    ########## REMOVE THIS ######
    # invoice_for_payment_ids = fields.One2many('account.invoice.register.line', 'register_payment_id',
    ########### USE THIS ########
    is_show_invoice = fields.Boolean(string='Show Invoice')
    invoice_to_payment_ids = fields.Many2many('account.invoice',string='Invoice to Payment')
    #
    # @api.model
    # def default_get(self, fields):
    #     print ('-------1')
    #     res = super(account_register_payments, self).default_get(fields)
    #     print ('---after original')
    #     context = dict(self._context or {})
    #     active_model = context.get('active_model')
    #     active_ids = context.get('active_ids')
    #
    #     # Checks on context parameters
    #     if not active_model or not active_ids:
    #         raise UserError(
    #             _("Programmation error: wizard action executed without active_model or active_ids in context."))
    #     if active_model != 'account.invoice':
    #         raise UserError(_(
    #             "Programmation error: the expected model for this action is 'account.invoice'. The provided one is '%d'.") % active_model)
    #
    #     # Checks on received invoice records
    #     invoices = self.env[active_model].browse(active_ids)
    #     # invoice_to_payment_ids = [(4, invoice.id, None) for invoice in invoices]
    #     # print (invoice_to_payment_ids)
    #
    #     res.update({'invoice_to_payment_ids':invoices.ids})
    #
    #     # for invoice in invoices:
    #     #
    #     #     vals = {
    #     #         'invoice_id': invoice.id,
    #     #         'invoice_amount': invoice.residual,
    #     #         'to_pay_amount': invoice.residual,
    #     #         'register_payment_id': self.id,
    #     #     }
    #     #     print(vals)
    #     #     self.env['account.invoice.register.line'].create(vals)
    #     #
    #     # print(self.invoice_for_payment_ids)
    #
    #     return res

    @api.multi
    def _prepare_payment_vals(self, invoices):
        print ('-----------INV-IDS')
        print (self.invoice_ids)

        res = super(account_register_payments,self)._prepare_payment_vals(invoices)
        update_vals = {
            'cheque_line_ids': [(4, cheque_line.id, None) for cheque_line in
                                       self.cheque_line_ids],
            'is_multiple_cheque': self.is_multiple_cheque,
        }
        print ('BF')
        print (res)
        res.update(update_vals)
        print ('after')
        print (res)
        return res

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_multiple_cheque = fields.Boolean(string='Multiple Cheque')
    is_show_invoice = fields.Boolean(string='Show Invoice')
    cheque_line_ids = fields.One2many('payment.cheque.line','payment_id',string='Cheque')
    cheque_reg_ids = fields.One2many('account.cheque.statement','payment_id',string='Multi Cheque')

    @api.multi
    def post(self):
        super(AccountPayment, self).post()
        for payment in self:
            if payment.payment_type == 'inbound':
                type = 'rec'
            else:
                type = 'pay'

            for cheque_line in payment.cheque_line_ids:
                vals_cheque_rec = {
                    'issue_date': payment.payment_date,
                    'ref': payment.communication,
                    'cheque_bank': cheque_line.cheque_bank.id,
                    'partner_id': payment.partner_id.id,
                    'cheque_branch': cheque_line.cheque_branch,
                    'cheque_number': cheque_line.cheque_number,
                    'cheque_date': cheque_line.cheque_date,
                    'amount': cheque_line.cheque_amount,
                    'journal_id': payment.journal_id.id,
                    'user_id': self.env.user.id,
                    'communication': payment.remark,
                    'company_id': self.env.user.company_id.id,
                    'type': type,
                    'payment_id': payment.id,
                    'move_id': payment.move_line_ids[0].move_id.id,
                    'is_multiple_cheque': True,
                }
                self.env['account.cheque.statement'].create(vals_cheque_rec)



    @api.multi
    def cancel(self):
        # print "NEW Cancel"
        for rec in self:
            if rec.cheque_reg_ids:
                rec.cheque_reg_ids.sudo().action_cancel()
                rec.cheque_reg_ids.sudo().unlink()
            super(AccountPayment, self).cancel()


class PaymentChequeLie(models.Model):
    _name = 'payment.cheque.line'

    payment_id = fields.Many2one('account.payment',string='Payment')
    register_payment_id = fields.Many2one('account.register.payments', string='Payment')
    register_billing_payment_id = fields.Many2one('register.billing.payments', string='Payment')
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    cheque_amount = fields.Float(string='Cheque Amount')