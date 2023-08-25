# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}



class RegisterBillingPayments(models.Model):
    _name = 'register.billing.payments'
    _inherit = "account.abstract.payment"

    current_account_id = fields.Many2one('account.account', string='Current Account', compute='get_current_account_id')
    is_change_account = fields.Boolean(string='Change Account')
    payment_account_id = fields.Many2one('account.account', string='New Account')

    @api.depends('journal_id')
    def get_current_account_id(self):
        if self.payment_type in ('outbound',
                                 'transfer') and self.journal_id.default_debit_account_id.id:
            self.current_account_id = self.journal_id.default_debit_account_id.id
        else:
            self.current_account_id = self.journal_id.default_credit_account_id.id

    @api.multi
    def _get_default_payment_option(self):
        # print 'payment_option'
        if self.env.user.company_id.payment_with_deduct:
            # print self.env.user.company_id.payment_with_deduct
            return 'partial'
        else:
            # print self.env.user.company_id.payment_with_deduct
            return 'full'

    payment_option = fields.Selection(
        [('full', 'Full Payment without Deduction'), ('partial', 'Full Payment with Deduction')],
        default=_get_default_payment_option, required=True, string='Payment Option')
    post_diff_acc = fields.Selection([('single', 'Single Account'), ('multi', 'Multiple Accounts')], default='single',
                                     string='Post Difference In To')
    writeoff_multi_acc_ids = fields.One2many('writeoff.accounts', 'payment_billing_id', string='Write Off Accounts')
    # wht = fields.Boolean(string="WHT")
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')],
                                                   default='open', string="Payment Difference", copy=False)
    payment_difference = fields.Monetary(compute='_compute_payment_difference', readonly=True)
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False)
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_payment_billing_rel', 'payment_billing_id',
                                   'invoice_id',
                                   string="Invoices", copy=False, readonly=True)
    purchase_or_sale = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')])
    # invoice_line_tax_id = fields.Many2one('account.tax')
    # tax_id = fields.Char(string='Tax ID')
    amount_untaxed = fields.Monetary(string='Payment Untax Amount')
    remark = fields.Char(string="Payment Remark")
    # this is the old bank text input
    # cheque_bank = fields.Char(string="Bank")
    bank_cheque = fields.Boolean(string='Is Cheque', related='journal_id.bank_cheque')
    # this is new bank list from res.bank
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    require_write_off_account = fields.Boolean(string='Require write off account')

    @api.onchange('payment_difference')
    def check_require_write_off_account(self):
        amount = 0
        if self.writeoff_multi_acc_ids:
            for payment in self.writeoff_multi_acc_ids:
                amount += payment.amount
        precision = self.env['decimal.precision'].precision_get('Product Price')

        if float_compare(float(abs(self.payment_difference)), abs(float(amount)), precision_digits=precision) != 0:
            self.require_write_off_account = True
        else:
            self.require_write_off_account = False
    
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type:
            return {'domain': {'payment_method_id': [('payment_type', '=', self.payment_type)]}}

    def _get_invoices(self):
        context = dict(self._context or {})
        # print "CONTEXT"
        # print context
        # active_id = context.get('active_id')
        # billing = self.env[context.get('active_model')].browse(active_id)
        # invoice_ids = [invoice.id for invoice in billing.invoice_ids]
        # invoices = self.env['account.invoice'].search([('state','=','open'),('id','in',invoice_ids)])
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        billing = self.env[active_model].browse(active_ids)[0]
        invoice_ids = [invoice.id for invoice in billing.invoice_ids]
        invoices = self.env['account.invoice'].search([('state', '=', 'open'), ('id', 'in', invoice_ids)])

        return invoices
    
    @api.model
    def default_get(self, fields):
        rec = super(RegisterBillingPayments, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(_("Programmation error: wizard action executed without active_model or active_ids in context."))
        if active_model != 'customer.billing':
            raise UserError(_("Programmation error: the expected model for this action is 'customer.billing'. The provided one is '%d'.") % active_model)

        # Checks on received invoice records
        billing = self.env[active_model].browse(active_ids)[0]
        invoice_ids = [invoice.id for invoice in billing.invoice_ids]
        #print invoice_ids
        invoices = self.env['account.invoice'].search([('state','=','open'),('id','in',invoice_ids)])
        #print invoices
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # if any(inv.commercial_partner_id != invoices[0].commercial_partner_id for inv in invoices):
        #     raise UserError(_("In order to pay multiple invoices at once, they must belong to the same commercial partner."))
        if any(MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] for inv in invoices):
            raise UserError(_("You cannot mix customer invoices and vendor bills in a single payment."))
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they must use the same currency."))

        total_amount = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)

        # for inv in invoices:
        #     if inv.type in ('')
        total_untaxed = sum(inv.amount_untaxed for inv in invoices)

        #print "Total billing untax"
        #print total_untaxed

        if invoices:
            if invoices[0].type in ['in_invoice', 'out_refund']:
                purchase_or_sale = 'purchase'
            else:
                purchase_or_sale = 'sale'
        else:
            raise UserError(_("There is no invoice to make a payment, please check an invoice status"))

        total_amount = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
        rec.update({
            'amount': abs(total_amount),
            'currency_id': invoices[0].currency_id.id,
            'payment_type': total_amount > 0 and 'inbound' or 'outbound',
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'amount_untaxed': abs(total_untaxed),
            'purchase_or_sale': purchase_or_sale,
            # 'invoice_ids': [(4, inv.id, None) for inv in invoices],
            'invoice_ids': invoices.ids,
        })

        return rec


    def get_payment_vals(self):
        """ Hook for extension """
        #update and return write off in order to pay with account.payment

        # print "Get Payment Vals"
        # print self.invoice_ids
        # for inv in self.invoice_ids:
        #     print inv.name

        writeoff_multi_ids = []
        for writeoff_multi in self.writeoff_multi_acc_ids:
            writeoff_multi_ids.append(writeoff_multi.id)

        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(4, inv.id, None) for inv in self.invoice_ids],
            'payment_type': self.payment_type,
            'amount': self.amount,
            'post_diff_acc': self.post_diff_acc,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': self.partner_type,
            'payment_account_id': self.payment_account_id.id,
            'payment_difference_handling': self.payment_difference_handling,
            'payment_difference': self.payment_difference,
            'writeoff_multi_acc_ids': [(4, writeoff_multi.id, None) for writeoff_multi in
                                       self.writeoff_multi_acc_ids],
            'amount_untaxed': self.amount_untaxed,
            'remark': self.remark,
            'cheque_bank': self.cheque_bank.id,
            'cheque_branch': self.cheque_branch,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,

        }
    
    @api.multi
    def create_payment(self):
        print ('create_payment_custome_1:')
        context = dict(self._context or {})
        active_id = context.get('active_id')
        payment = self.env['account.payment'].create(self.get_payment_vals())
        payment.post()
        bill_record = self.env[context.get('active_model')].browse(active_id)
        if bill_record.residual <= 0:
            bill_record.write({'state':'paid'})
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def billing_compute_total_invoices_amount(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        billing_ids = self.env[active_model].browse(active_ids)
        payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        total_invoice_amount = 0
        for billing_id in billing_ids:
            for inv in billing_id.invoice_ids:
                if inv.currency_id == payment_currency:
                    total_invoice_amount += inv.residual_signed
                else:
                    total_invoice_amount += inv.company_currency_id.with_context(date=self.payment_date).compute(
                        inv.residual_company_signed, payment_currency)

        return abs(total_invoice_amount)

    #new from register payment to apply for billing payment
    @api.one
    @api.depends('amount', 'payment_date', 'currency_id')
    def _compute_payment_difference(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        billing_id = self.env[active_model].browse(active_ids)
        # payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        # total_invoice_amount = 0
        # for inv in billing_id.invoice_ids:
        #     if inv.currency_id == payment_currency:
        #         total_invoice_amount += inv.residual_signed
        #     else:
        #         total_invoice_amount += inv.company_currency_id.with_context(date=self.payment_date).compute(
        #             inv.residual_company_signed, payment_currency)
        #
        # # print "_compute_payment_difference"
        # # print total_invoice_amount
        total_invoice_amount = self.billing_compute_total_invoices_amount()
        if len(billing_id.mapped('invoice_ids')) == 0:
            return

        if billing_id[0].type in ['in_invoice', 'out_refund']:
            self.payment_difference = self.amount - total_invoice_amount
        else:
            self.payment_difference = total_invoice_amount - self.amount

    @api.onchange('payment_option')
    def onchange_payment_option(self):
        if self.payment_option == 'full':
            self.payment_difference_handling = 'open'
            self.post_diff_acc = 'single'
        else:
            self.payment_difference_handling = 'reconcile'
            self.post_diff_acc = 'multi'

    # calculate writeoff amount
    @api.onchange('writeoff_multi_acc_ids')
    @api.multi
    def onchange_writeoff_multi_accounts(self):
        if self.writeoff_multi_acc_ids:
            diff_amount = sum([line.amount for line in self.writeoff_multi_acc_ids])
            total_invoice_amount = self.billing_compute_total_invoices_amount()
            self.amount = total_invoice_amount - diff_amount

