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




class account_register_payments(models.Model):
    _name = "account.register.payments"
    _inherit = 'account.abstract.payment'

    @api.multi
    def _get_default_payment_option(self):
        # print 'payment_option'
        if self.env.user.company_id.payment_with_deduct:
            # print self.env.user.company_id.payment_with_deduct
            return 'partial'
        else:
            # print self.env.user.company_id.payment_with_deduct
            return 'full'

    multi = fields.Boolean(string='Multi',
                           help='Technical field indicating if the user selected invoices from multiple partners or from different types.')

    payment_option = fields.Selection(
        [('full', 'Full Payment without Deduction'), ('partial', 'Full Payment with Deduction')],
        default=_get_default_payment_option, required=True, string='Payment Option')
    post_diff_acc = fields.Selection([('single', 'Single Account'), ('multi', 'Multiple Accounts')], default='single',
                                     string='Post Difference In To')
    writeoff_multi_acc_ids = fields.One2many('writeoff.accounts', 'payment_wizard_id', string='Write Off Accounts')
    # wht = fields.Boolean(string="WHT")
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')],
                                                   default='open', string="Payment Difference", copy=False)
    payment_difference = fields.Monetary(compute='_compute_payment_difference', readonly=True)
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False)
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_payment_wizard_rel', 'payment_wizard_id',
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
    current_account_id = fields.Many2one('account.account', string='Current Account', compute='get_current_account_id')
    is_change_account = fields.Boolean(string='Change Account')
    payment_account_id = fields.Many2one('account.account', string='New Account')
    is_partial_selected_invoice = fields.Boolean(string='Is Partial Selected Invoice', default=False)


    @api.depends('journal_id')
    def get_current_account_id(self):
        if self.payment_type in ('outbound',
                                 'transfer') and self.journal_id.default_debit_account_id.id:
            self.current_account_id = self.journal_id.default_debit_account_id.id
        else:
            self.current_account_id = self.journal_id.default_credit_account_id.id

    @api.onchange('payment_difference')
    def check_require_write_off_account(self):
        amount = 0
        if self.writeoff_multi_acc_ids:
            for payment in self.writeoff_multi_acc_ids:
                amount += payment.amount
        precision = self.env['decimal.precision'].precision_get('Product Price')

        print (amount)
        print (self.payment_difference)
        if float_compare(float(abs(self.payment_difference)), float(abs(amount)), precision_digits=precision) != 0:
            self.require_write_off_account = True
        else:
            self.require_write_off_account = False

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type:
            return {'domain': {'payment_method_id': [('payment_type', '=', self.payment_type)]}}

    #############better way to compute payment amount######
    @api.model
    def _compute_payment_amount(self, invoice_ids):
        payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id

        total = 0
        for inv in invoice_ids:
            if inv.currency_id == payment_currency:
                total += MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] * inv.residual
            else:
                amount_residual = inv.company_currency_id.with_context(date=self.payment_date).compute(
                    inv.residual, payment_currency)
                total += MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] * amount_residual
        return total

    @api.multi
    def _groupby_invoices(self):
        '''Split the invoices linked to the wizard according to their commercial partner and their type.

        :return: a dictionary mapping (commercial_partner_id, type) => invoices recordset.
        '''
        results = {}
        # Create a dict dispatching invoices according to their commercial_partner_id and type
        print ('-----------GROUP BY INV------')
        print (self)
        for inv in self._get_invoices:
            key = (inv.commercial_partner_id.id, MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type])
            if not key in results:
                results[key] = self.env['account.invoice']
            results[key] += inv
        return results

    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        print ('------_prepare_payment_vals')


        amount = self._compute_payment_amount(invoices) if self.multi else self.amount

        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        ############## new for multi-write-off############
        writeoff_multi_ids = []
        for writeoff_multi in self.writeoff_multi_acc_ids:
            writeoff_multi_ids.append(writeoff_multi.id)

        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'payment_account_id': self.payment_account_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            #################
            'post_diff_acc': self.post_diff_acc,
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
            'is_partial_selected_invoice': self.is_partial_selected_invoice,
        }

    @api.multi
    def get_payments_vals(self):
        '''Compute the values for payments.

        :return: a list of payment values (dictionary).
        '''

        print ('get_payments_vals')
        print (self.multi)

        #############This is remove due to difference partner register at the same time, so could not group
        # if self.multi:
        #     groups = self._groupby_invoices()
        #     return [self._prepare_payment_vals(invoices) for invoices in groups.values()]
        ############ 07-12-2019

        return [self._prepare_payment_vals(self._get_invoices())]

    @api.multi
    def create_payments(self):
        '''Create payments according to the invoices.
        Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
        leads to multiple payments.
        In case of all the invoices are related to the same commercial_partner_id and have the same type,
        only one payment will be created.

        :return: The ir.actions.act_window to show created payments.
        '''
        Payment = self.env['account.payment']
        payments = Payment
        for payment_vals in self.get_payments_vals():
            payments += Payment.create(payment_vals)
        payments.post()
        return {
            'name': _('Payments'),
            'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    @api.model
    def default_get(self, fields):
        rec = super(account_register_payments, self).default_get(fields)
        context = dict(self._context or {})
        #print "DEFAULT"
        #print context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _("Programmation error: wizard action executed without active_model or active_ids in context."))
        if active_model != 'account.invoice':
            raise UserError(_(
                "Programmation error: the expected model for this action is 'account.invoice'. The provided one is '%d'.") % active_model)

        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        print ("OROGI")
        print (invoices)

        # print "Default Get"
        # print invoice_ids
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))

        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they must use the same currency."))

        #########this is V10- function pay only one partner #########################################
        # if any(inv.commercial_partner_id != invoices[0].commercial_partner_id for inv in invoices):
        #     raise UserError(
        #         _("In order to pay multiple invoices at once, they must belong to the same commercial partner."))

        # if any(MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] for inv in
        #        invoices):
        #     raise UserError(_("You cannot mix customer invoices and vendor bills in a single payment."))

        ##################### new function to paid multiple invoice with multiple partner#############
        # Look if we are mixin multiple commercial_partner or customer invoices with vendor bills
        ######### Multi check#1 - by partner
        multi = any(inv.commercial_partner_id != invoices[0].commercial_partner_id
                    or MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
                    for inv in invoices)

        ######### Multi check#2 - by bill_to - add by JA - 25/03/2020
        if multi and invoices[0].bill_to_id:
            multi = any(inv.bill_to_id != invoices[0].bill_to_id
                        or MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
                        for inv in invoices)


        total_amount = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
        total_untaxed = sum(inv.amount_untaxed for inv in invoices)

        if invoices[0].type in ['in_invoice', 'in_refund']:
            purchase_or_sale = 'purchase'
        else:
            purchase_or_sale = 'sale'

        rec.update({
            'amount': abs(total_amount),
            'currency_id': invoices[0].currency_id.id,
            'payment_type': total_amount > 0 and 'inbound' or 'outbound',
            'partner_id': False if multi else invoices[0].commercial_partner_id.id,
            'partner_type': False if multi else MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': ' '.join([ref for ref in invoices.mapped('reference') if ref]),
            'amount_untaxed': abs(total_untaxed),
            'purchase_or_sale': purchase_or_sale,
            'multi': multi,
        })
        return rec

    def _get_invoices(self):
        context = dict(self._context or {})
        #print "CONTEXT"
        #print context
        active_model = context.get('active_model')
        #print "ACTIVE MODEL"
        #print active_model
        active_ids = context.get('active_ids')
        #print "ACTIVE IDS"
        #print active_ids
        invoice_ids = self.env[active_model].browse(active_ids)
        return invoice_ids

    ############# This function for onchange deduction item ############
    ############# consider to remove later - 31/04/2020    ############

    def get_payment_vals(self):
        """ Hook for extension """
        # update and return write off in order to pay with account.payment
        print('------get_payment_vals')
        writeoff_multi_ids = []
        for writeoff_multi in self.writeoff_multi_acc_ids:
            writeoff_multi_ids.append(writeoff_multi.id)

        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'payment_type': self.payment_type,
            'amount': self.amount,
            'post_diff_acc': self.post_diff_acc,
            'payment_account_id': self.payment_account_id,
            'payment_difference_handling': self.payment_difference_handling,
            'payment_difference': self.payment_difference,
            'writeoff_multi_acc_ids': [(4, writeoff_multi.id, None) for writeoff_multi in
                                       self.writeoff_multi_acc_ids],
            'amount_untaxed': self.amount_untaxed,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': self.partner_type,
            'remark': self.remark,
            'cheque_bank': self.cheque_bank.id,
            'cheque_branch': self.cheque_branch,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,
            'is_partial_selected_invoice': self.is_partial_selected_invoice,

        }

    # compute payment difference from total invoice and new pay amount for "register with wizard but" but single invoice use existing function

    @api.one
    @api.depends('amount', 'payment_date', 'currency_id')
    def _compute_payment_difference(self):
        print ('--_compute_payment_difference')
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        invoice_ids = self.env[active_model].browse(active_ids)
        total_invoice_amount = self._compute_payment_amount(invoice_ids)
        if len(invoice_ids) == 0:
            return
        if invoice_ids[0].type in ['in_invoice', 'in_refund']:
            # print ('supplier')
            # print (self.amount)
            # print (total_invoice_amount)
            # print (self.payment_difference)
            self.payment_difference = self.amount - abs(total_invoice_amount)
            # print (self.payment_difference)
        else:
            print('customer')
            print(total_invoice_amount)
            print(self.amount)
            print(self.payment_difference)
            self.payment_difference = abs(total_invoice_amount) - self.amount
            print (self.payment_difference)
            print ('-diff')

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
            # print "DIFF AMOUNT- AR"
            # print diff_amount

            context = dict(self._context or {})
            #print "CONTEXT"
            #print context
            active_model = context.get('active_model')
            #print "ACTIVE MODEL"
            #print active_model
            active_ids = context.get('active_ids')
            #print "ACTIVE IDS"
            #print active_ids
            invoice_ids = self.env[active_model].browse(active_ids)
            #print invoice_ids
            total_invoice_amount = self._compute_payment_amount(self._get_invoices())
            # print ("TOTAL INVOICE AR")
            # print (total_invoice_amount)
            self.amount = abs(total_invoice_amount) - diff_amount
