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


class account_payment(models.Model):
    _inherit = "account.payment"


    name_old = fields.Char(string='Name Old', copy=False)
    voucher_old = fields.Char(string='Voucher Old', copy=False)

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
    writeoff_multi_acc_ids = fields.One2many('writeoff.accounts', 'payment_id', string='Write Off Accounts')

    purchase_or_sale = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')])
    remark = fields.Char(string='Payment Remark')
    wht = fields.Boolean(string="WHT")
    # this is the old bank text input
    # cheque_bank = fields.Char(string="Bank")
    bank_cheque = fields.Boolean(string='Is Cheque', related='journal_id.bank_cheque')
    # this is new bank list from res.bank
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    payment_cut_off_amount = fields.Float(string='Cut Off Payment Amount', digits=dp.get_precision('Account'), readonly=True,compute="get_payment_cut_off_amount")
    cheque_reg_id = fields.Many2one('account.cheque.statement',string='Cheque Record')
    amount_untaxed = fields.Monetary(string='Full Amount')
    require_write_off_account = fields.Boolean(string='Require write off account')
    current_account_id = fields.Many2one('account.account',string='Current Account',compute='get_current_account_id')
    is_change_account = fields.Boolean(string='Change Account')
    payment_account_id = fields.Many2one('account.account',string='New Account')
    is_partial_selected_invoice = fields.Boolean(string='Is Partial Selected Invoice',default=False)

    @api.depends('journal_id')
    def get_current_account_id(self):
        for payment in self:
            if payment.payment_type in ('outbound',
                                  'transfer') and payment.journal_id.default_debit_account_id.id:
                payment.current_account_id = payment.journal_id.default_debit_account_id.id
            else:
                payment.current_account_id = payment.journal_id.default_credit_account_id.id

    @api.onchange('payment_difference')
    def check_require_write_off_account(self):
        amount = 0
        for payment_id in self:
            if payment_id.writeoff_multi_acc_ids:
                for payment in self.writeoff_multi_acc_ids:
                    amount += payment.amount
            precision = self.env['decimal.precision'].precision_get('Product Price')

            if float_compare(float(abs(payment_id.payment_difference)), abs(float(amount)), precision_digits=precision) != 0:
                payment_id.require_write_off_account = True
            else:
                payment_id.require_write_off_account = False

    @api.onchange('move_line_ids')
    def get_payment_cut_off_amount(self):
        payment_cut_off_amount = 0
        for payment in self:
            if payment.move_line_ids:
                for line in payment.move_line_ids:
                    if line.account_id.payment_cut_off:
                        # print "cut off"
                        payment_cut_off_amount += line.credit

            # print "payment_cut_off_amount"
            # print payment_cut_off_amount
            payment.payment_cut_off_amount = payment_cut_off_amount


    @api.onchange('payment_option')
    def onchange_payment_option(self):
        for payment in self:
            if payment.payment_option == 'full':
                payment.payment_difference_handling = 'open'
                payment.post_diff_acc = 'single'
            else:
                payment.payment_difference_handling = 'reconcile'
                payment.post_diff_acc = 'multi'

            if payment.invoice_ids[0].type in ['in_invoice', 'in_refund']:
                payment.purchase_or_sale = 'purchase'
            else:
                payment.purchase_or_sale = 'sale'

    #when add write off then new pay amount will be calculated by deduct from diff amount
    @api.onchange('writeoff_multi_acc_ids')
    @api.multi
    def onchange_writeoff_multi_accounts(self):
        if self.writeoff_multi_acc_ids:
            diff_amount = sum([line.amount for line in self.writeoff_multi_acc_ids])
            self.amount = self.invoice_ids and self.invoice_ids[0].residual - diff_amount
            self.amount_untaxed = sum([invoice.amount_untaxed for invoice in self.invoice_ids])
            # print "onchange_writeoff_multi_accounts(self):"
            # print self.amount_untaxed



    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)

        ############### Change name from normal journal to payment name #########
        ############### JA - 08-06-2020 (#1633 #############
        # old ###
        # name = journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
        # New ### same with payment name
        if self.partner_type == 'customer':
            name = self.name
            print(name)
            print('------------')
        else:
            name = journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
            print(name)
            print('===========================')

        wht_personal_company = False
        if self.writeoff_multi_acc_ids:
            print('writeoff_multi_acc_ids:')
            for woff_payment in self.writeoff_multi_acc_ids:
                if woff_payment.writeoff_account_id.wht and woff_payment.amt_percent and self.payment_type == 'outbound':
                    wht_personal_company = woff_payment.wht_personal_company


        return {
            'name': name,
            'date': self.payment_date,
            'ref': self.communication or '',
            'remark': self.remark,
            'cheque_bank': self.cheque_bank.id,
            'cheque_branch': self.cheque_branch,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'wht_personal_company' : wht_personal_company,
        }
    ############## Add this function for partial selected invoice#################
    ############## Jatupong - 28/04/2020 #########################################
    def _create_multi_payment_entry(self,amount):
        move = False
        return move

    #############call from account.payment post()############
    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        #print "_create_payment_entry"
        #print amount
        ################Step - 1
        if self.is_partial_selected_invoice:
            print ('-PARTIAL')
            move = self._create_multi_payment_entry(amount)
            return move

        # print ('---GO---_create_payment_entry--1')
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        ################Step - 1.5
        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id,
                                                          invoice_currency)
        ################Step - 2
        move = self.env['account.move'].create(self._get_move_vals())
        #print "MOVE LINE"
        #print len(move)
        # print move.name

        # Write line corresponding to invoice payment
        ################Step - 3
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        # print ('step-3-1')
        # print (counterpart_aml_dict)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        # print('step-3-2')
        # print (counterpart_aml_dict)
        #print "PART 1"
        #print counterpart_aml_dict
        counterpart_aml_dict.update({'currency_id': currency_id})
        ################Step - 4
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        #print "MOVE LINE"
        #print len(move)
        precision = self.env['decimal.precision'].precision_get('Product Price')

        # Reconcile with the invoices
        # print('---GO---_create_payment_entry--2')
        # print (self.payment_difference_handling)
        # print (self.payment_difference)

        if self.payment_difference_handling == 'reconcile' and (self.payment_difference or self.writeoff_multi_acc_ids):
            # print ("with deduction")
            if self.post_diff_acc == 'single':
                #print "RECONCILE, DIFF and Single"
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                    date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id,
                                                                  self.company_id.currency_id, invoice_currency)
                writeoff_line['name'] = _('Counterpart')
                writeoff_line['account_id'] = self.writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line['payment_id'] = self.id
                #print '9999999'
                aml_obj.create(writeoff_line)
                if counterpart_aml['debit']:
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit']:
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo
            if self.post_diff_acc == 'multi':
                print ("RECONCILE, DIFF and MULTI")
                write_off_total_amount = 0
                for woff_payment in self.writeoff_multi_acc_ids:
                    print ('----WRITE off detail ------')
                    if self.payment_type == 'inbound':
                        woff_amount = woff_payment.amount
                    else:
                        woff_amount = - woff_payment.amount

                    write_off_total_amount = woff_payment.amount
                    writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                        date=self.payment_date).compute_amount_fields(woff_amount, self.currency_id,
                                                                      self.company_id.currency_id, invoice_currency)
                    # if not self.currency_id != self.company_id.currency_id:
                    #     amount_currency_wo = 0
                    writeoff_line['name'] = woff_payment.name
                    writeoff_line['account_id'] = woff_payment.writeoff_account_id.id
                    writeoff_line['debit'] = debit_wo
                    writeoff_line['credit'] = credit_wo
                    writeoff_line['wht_personal_company'] = woff_payment.wht_personal_company
                    # writeoff_line['wht_type'] = woff_payment.wht_type

                    writeoff_line['amount_currency'] = amount_currency_wo
                    writeoff_line['currency_id'] = woff_payment.currency_id.id
                    writeoff_line['payment_id'] = self.id
                    writeoff_line['department_id'] = woff_payment.department_id.id

                    if woff_payment.currency_id != self.currency_id:
                        raise UserError(_('Deduction currency must be the same with payment currency'))

                    ###########amount before tax will allway in company currency
                    if self.currency_id != self.company_id.currency_id:
                        currency_id = self.currency_id.with_context(date=self.payment_date)
                        amount_before_tax = currency_id.compute(woff_payment.amount_untaxed, self.company_id.currency_id)
                    else:
                        amount_before_tax = woff_payment.amount_untaxed

                    writeoff_line['amount_before_tax'] = amount_before_tax
                    ###############################################################

                    if woff_payment.writeoff_account_id.wht and woff_payment.amt_percent and self.payment_type == 'outbound':
                        print (" ADD WHT %")
                        if abs(woff_payment.amt_percent) == 1:
                            writeoff_line['wht_type'] = '1%'
                        if abs(woff_payment.amt_percent) == 1.5:
                            writeoff_line['wht_type'] = '1.5%'
                        if abs(woff_payment.amt_percent) == 2:
                            writeoff_line['wht_type'] = '2%'
                        if abs(woff_payment.amt_percent) == 3:
                            writeoff_line['wht_type'] = '3%'
                        if abs(woff_payment.amt_percent) == 5:
                            writeoff_line['wht_type'] = '5%'

                        # print "record to journal wht personal company"
                        # print woff_payment.wht_personal_company
                        # writeoff_line['wht_personal_company'] = 'personal'

                    #print "Write off"
                    #print "PART 2"
                    # print (writeoff_line)
                    aml_obj.create(writeoff_line)
                    #print "MOVE LINE"
                    #print len(move)
                    # print "writeoff_line after"
                    # print writeoff_line

                    #############to update all counter part to total payment
                    if counterpart_aml['debit'] or (counterpart_aml['debit'] == 0.0 and self.payment_type == 'outbound'):
                        counterpart_aml['debit'] += credit_wo - debit_wo
                    if counterpart_aml['credit'] or (counterpart_aml['credit'] == 0.0 and self.payment_type == 'inbound'):
                        counterpart_aml['credit'] += debit_wo - credit_wo
                    counterpart_aml['amount_currency'] -= amount_currency_wo

                ############Additioanl write off account field - Jatupong - 28/04/2020
                if self.writeoff_account_id and float_compare(float(abs(self.payment_difference)), float(abs(write_off_total_amount)),
                                                                precision_digits=precision) != 0:

                    amount_final_diff = self.payment_difference - write_off_total_amount

                    if self.payment_type != 'inbound':
                        amount_final_diff = (-1)*amount_final_diff

                    writeoff_final_diff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount_final_diff, self.currency_id,
                                                                  self.company_id.currency_id, invoice_currency)
                    writeoff_final_diff_line['name'] = self.writeoff_account_id.name
                    writeoff_final_diff_line['account_id'] = self.writeoff_account_id.id
                    writeoff_final_diff_line['debit'] = debit_wo
                    writeoff_final_diff_line['credit'] = credit_wo
                    writeoff_final_diff_line['amount_currency'] = amount_currency_wo
                    writeoff_final_diff_line['currency_id'] = currency_id
                    writeoff_final_diff_line['payment_id'] = self.id

                    #print "Final Diff"
                    #print "PART 3"
                    print (writeoff_final_diff_line)
                    aml_obj.create(writeoff_final_diff_line)
                    #print "MOVE LINE"
                    #print len(move)
                    if counterpart_aml['debit']:
                        counterpart_aml['debit'] += credit_wo - debit_wo
                    if counterpart_aml['credit']:
                        counterpart_aml['credit'] += debit_wo - credit_wo
                    counterpart_aml['amount_currency'] -= amount_currency_wo

            ################# Add this process under "reconcile option - Jatupong - 28/04/2020"
            ################Step - 5
            print ('STEP-5')
            # print (counterpart_aml)

            # self.invoice_ids.register_payment(counterpart_aml)


        # Reconcile with the invoices
        if self.payment_difference_handling == 'open' and self.payment_difference:
            #print "OPEN and DIFF"
            if self.post_diff_acc == 'multi':
                #print "OPEN and DIFF and MULTI"
                for woff_payment in self.writeoff_multi_acc_ids:
                    if self.payment_type == 'inbound':
                        woff_amount = woff_payment.amount
                    else:
                        woff_amount = - woff_payment.amount

                    writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                        date=self.payment_date).compute_amount_fields(woff_amount, self.currency_id,
                                                                      self.company_id.currency_id,
                                                                      invoice_currency)
                    # if not self.currency_id != self.company_id.currency_id:
                    #     amount_currency_wo = 0
                    writeoff_line['name'] = woff_payment.name
                    writeoff_line['account_id'] = woff_payment.writeoff_account_id.id
                    writeoff_line['debit'] = debit_wo
                    writeoff_line['wht_personal_company'] = woff_payment.wht_personal_company
                    # writeoff_line['wht_type'] = woff_payment.wht_type
                    writeoff_line['credit'] = credit_wo
                    writeoff_line['amount_currency'] = amount_currency_wo
                    writeoff_line['currency_id'] = currency_id
                    writeoff_line['payment_id'] = self.id
                    writeoff_line['department_id'] = woff_payment.department_id.id
                    # print "before wht"
                    # print self.invoice_ids[0].amount_untaxed
                    writeoff_line['amount_before_tax'] = woff_payment.amount_untaxed

                    if woff_payment.writeoff_account_id.wht and woff_payment.amt_percent and self.payment_type == 'outbound':
                        if woff_payment.amt_percent == 1:
                            writeoff_line['wht_type'] = '1%'
                        if woff_payment.amt_percent == 1.5:
                            writeoff_line['wht_type'] = '1.5%'
                        if woff_payment.amt_percent == 2:
                            writeoff_line['wht_type'] = '2%'
                        if woff_payment.amt_percent == 3:
                            writeoff_line['wht_type'] = '3%'
                        if woff_payment.amt_percent == 5:
                            writeoff_line['wht_type'] = '5%'

                            # print "record to journal wht personal company"
                            # print woff_payment.wht_personal_company
                            # writeoff_line['wht_personal_company'] = 'personal'

                    #print "writeoff_line before"
                    #print writeoff_line
                    writeoff_line = aml_obj.create(writeoff_line)
                    #print "writeoff_line after"
                    #print writeoff_line

                    if counterpart_aml['debit'] or (
                                    counterpart_aml['debit'] == 0.0 and self.payment_type == 'outbound'):
                        counterpart_aml['debit'] += credit_wo - debit_wo
                    if counterpart_aml['credit'] or (
                                    counterpart_aml['credit'] == 0.0 and self.payment_type == 'inbound'):
                        counterpart_aml['credit'] += debit_wo - credit_wo

                    counterpart_aml['amount_currency'] -= amount_currency_wo


        self.invoice_ids.register_payment(counterpart_aml)
        # Write counterpart lines

        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0

        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))

        # print "BEFORE UPDATE"
        # print self.current_account_id
        # print self.payment_account_id
        if self.payment_account_id:
            # print "UPDATE ACC"
            # print self.current_account_id
            # print self.payment_account_id
            liquidity_aml_dict.update({'account_id':self.payment_account_id.id})

        aml_obj.create(liquidity_aml_dict)
        #print "MOVE LINE"
        #print len(move)
        #print "liquidity_aml_dict"
        # print ("PART4")
        # print (liquidity_aml_dict)
        move.post()
        return move

    def get_wht_amount_pay_diff_amount(self):
        # print "get wht_amount diff"
        wht_amount = 0.0
        bank_fee_amount = 0.0
        little_amount = 0.0
        move_id = self.move_line_ids[0].move_id
        move_line_ids = self.env['account.move.line'].search([('move_id', '=', move_id.id)])
        #print move_line_ids
        if move_line_ids:
            #print "found move"
            for move_line in move_line_ids:
                #print move_line.name
                if move_line.account_id.wht:
                    wht_amount += move_line.debit
                if move_line.account_id.bank_fee:
                    bank_fee_amount += move_line.debit
                if move_line.account_id.diff_little_money:
                    little_amount += move_line.debit

        return wht_amount

    def get_bank_fee_amount_pay_diff_amount(self):
        #print "get bank_fee_amount diff"

        wht_amount = 0.0
        bank_fee_amount = 0.0
        little_amount = 0.0
        move_id = self.move_line_ids[0].move_id
        move_line_ids = self.env['account.move.line'].search([('move_id','=',move_id.id)])
        if move_line_ids:
            #print "found move"
            for move_line in move_line_ids:
                #print move_line.name
                if move_line.account_id.wht:
                    wht_amount += move_line.debit
                if move_line.account_id.bank_fee:
                    bank_fee_amount += move_line.debit
                if move_line.account_id.diff_little_money:
                    little_amount += move_line.debit


        return bank_fee_amount

    def get_little_amount_pay_diff_amount(self):
        #print "get little_amount diff"

        wht_amount = 0.0
        bank_fee_amount = 0.0
        little_amount = 0.0
        move_id = self.move_line_ids[0].move_id
        move_line_ids = self.env['account.move.line'].search([('move_id', '=', move_id.id)])
        if move_line_ids:
            #print "found move"
            for move_line in move_line_ids:
                #print move_line.name
                if move_line.account_id.wht:
                    wht_amount += move_line.debit
                if move_line.account_id.bank_fee:
                    bank_fee_amount += move_line.debit
                if move_line.account_id.diff_little_money:
                    little_amount += move_line.debit

        return little_amount

    @api.multi
    def cancel(self):
        # print "NEW Cancel"
        for rec in self:
            rec.name_old = rec.name
            rec.voucher_old = rec.move_line_ids[0].move_id.name
            if rec.cheque_reg_id:
                rec.cheque_reg_id.sudo().action_cancel()
                rec.cheque_reg_id.sudo().unlink()
            super(account_payment, self).cancel()

class writeoff_accounts(models.Model):
    _name = 'writeoff.accounts'

    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False, required="1")
    wht = fields.Boolean(string="WHT",related='writeoff_account_id.wht',default=False)
    wht_personal_company = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53')],related='deduct_item_id.wht_personal_company',string="Personal/Company")
    name = fields.Char('Description')
    amt_percent = fields.Float(string='Amount(%)', digits=(16, 2))
    amount = fields.Float(string='Payment Amount', digits=(16, 2), required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    payment_id = fields.Many2one('account.payment', string='Payment Record')
    deduct_item_id = fields.Many2one('account.tax', string='Deduction Item')

    # new for payment wizard only.
    payment_wizard_id = fields.Many2one('account.register.payments', string='Payment Record')
    payment_billing_id = fields.Many2one('register.billing.payments', string='Payment Record')
    amount_untaxed = fields.Float(string='Full Amount')
    department_id = fields.Many2one('hr.department', string='Department')

    @api.onchange('writeoff_account_id')
    @api.multi
    def _onchange_writeoff_account_id(self):
        if self.writeoff_account_id:
            self.name = self.writeoff_account_id.name

    @api.onchange('amt_percent','amount_untaxed')
    def _onchange_amt_percent(self):
        if self.amount_untaxed and self.amt_percent:
            self.amount = self.amount_untaxed * self.amt_percent / 100

    @api.onchange('deduct_item_id')
    @api.multi
    def _onchange_deduct_item_id(self):
        if self.payment_wizard_id:
            payment_vals = self.payment_wizard_id.get_payment_vals()
            self.amount_untaxed = payment_vals['amount_untaxed']

            # new for payment billing only
        if self.payment_billing_id:
            payment_vals = self.payment_billing_id.get_payment_vals()
            self.amount_untaxed = payment_vals['amount_untaxed']


        if self.deduct_item_id:
            self.writeoff_account_id = self.deduct_item_id.account_id.id
            self.amt_percent = self.deduct_item_id.amount
            self.name = self.deduct_item_id.name
            if not self.amount_untaxed:
                self.amount_untaxed = self.payment_id.invoice_ids[0].amount_untaxed
            self.amount = self.amount_untaxed * self.deduct_item_id.amount / 100


#class account_abstract_payment(models.AbstractModel):
#    _inherit = "account.abstract.payment"

#    @api.one
#    @api.constrains('amount')
#    def _check_amount(self):
#        if not self.amount > 0.0:
#            print ('The payment amount must be strictly positive.')
            # raise ValidationError('The payment amount must be strictly positive.')
