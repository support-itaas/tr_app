# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class account_payment(models.Model):
    _inherit = 'account.payment'

    payment_for = fields.Selection([('multi_payment', 'AP Payment')], string='Payment Method')
    line_ids = fields.One2many('advance.payment.line', 'account_payment_id')
    full_reco = fields.Boolean('Full Reconcile')
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_payment_rel', 'payment_id', 'invoice_id',
                                   string="Invoices", copy=False, readonly=False)

    @api.multi
    @api.onchange('payment_for')
    def onchange_payment_for(self):
        if self.payment_for == 'multi_payment':
            self.onchange_partner_id()
        elif self.payment_for != 'multi_payment':
            if self.line_ids:
                for line in self.line_ids:
                    line.account_payment_id = False
            if self.invoice_ids:
                self.invoice_ids = False

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.payment_for == 'multi_payment':
            acc_invoice = []
            account_inv_obj = self.env['account.invoice']
            invoice_ids = []
            if self.partner_type == 'customer':
                invoice_ids = account_inv_obj.search(
                    [('partner_id', 'in', [self.partner_id.id]), ('state', '=', 'open'),
                     ('type', 'in', ['out_invoice', 'out_refund']), ('company_id', '=', self.company_id.id)])
            else:
                invoice_ids = account_inv_obj.search(
                    [('partner_id', 'in', [self.partner_id.id]), ('state', '=', 'open'),
                     ('type', 'in', ['in_invoice', 'in_refund']), ('company_id', '=', self.company_id.id)])
            curr_pool = self.env['res.currency']
            for vals in invoice_ids:
                original_amount = vals.amount_total
                balance_amount = vals.residual
                allocation = vals.residual
                if vals.currency_id.id != self.currency_id.id:
                    original_amount = vals.amount_total
                    balance_amount = vals.residual
                    allocation = vals.residual
                    if vals.currency_id.id != self.currency_id.id:
                        currency_id = self.currency_id.with_context(date=self.payment_date)
                        original_amount = curr_pool._compute(vals.currency_id, currency_id, original_amount, round=True)
                        balance_amount = curr_pool._compute(vals.currency_id, currency_id, balance_amount, round=True)
                        allocation = curr_pool._compute(vals.currency_id, currency_id, allocation, round=True)

                acc_invoice.append({'invoice_id': vals.id, 'account_id': vals.account_id.id,
                                    'date': vals.date_invoice, 'due_date': vals.date_due,
                                    'original_amount': original_amount, 'balance_amount': balance_amount,
                                    'allocation': 0.0, 'full_reconclle': False, 'currency_id': self.currency_id.id})
            self.line_ids = acc_invoice
            self.invoice_ids = [(6, 0, invoice_ids.ids)]

    @api.onchange('currency_id')
    def onchange_currency(self):
        curr_pool = self.env['res.currency']
        if self.currency_id and self.line_ids:
            total_allocation_amt = 0
            for line in self.line_ids:
                if line.currency_id.id != self.currency_id.id:
                    currency_id = self.currency_id.with_context(date=self.payment_date)
                    line.original_amount = curr_pool._compute(line.currency_id, currency_id, line.original_amount,
                                                              round=True)
                    line.balance_amount = curr_pool._compute(line.currency_id, currency_id, line.balance_amount,
                                                             round=True)
                    line.allocation = curr_pool._compute(line.currency_id, currency_id, line.allocation, round=True)
                    line.currency_id = self.currency_id and self.currency_id.id or False
            for line in self.line_ids:
                if line.diff_amt == 0:
                    line.full_reconclle = True
                total_allocation_amt += line.allocation

            print ('---total_allocation_amt----')
            self.amount = total_allocation_amt

    @api.multi
    def post(self):
        print ('-FINAL POST')
        if self.line_ids and self.payment_for == 'multi_payment':
            amt = 0.0
            invoice_ids = []
            for line in self.line_ids:
                invoice_ids.append(line.invoice_id.id)
                amt += line.allocation

            ########### Remove this condition to support multiple write off
            # if not amt and not self.amount:
            #     raise ValidationError(("Add Allocation Amount in payment item"))
                
            pay_amt = "{:.2f}".format(self.amount)
            amt = "{:.2f}".format(amt)

            ########### Remove this condition to support multiple write off
            # if pay_amt < amt:
            #     raise ValidationError(("Amount is must be greater or equal '%s'") % (amt))
            #

            if pay_amt > amt:
                self.full_reco = True
            self.invoice_ids = [(6, 0, invoice_ids)]
        return super(account_payment, self).post()

    @api.multi
    def get_inv_pay_amount(self, inv):
        amt = 0
        if self.partner_type == 'customer':
            for line in self.line_ids:
                if line.invoice_id.id == inv.id:
                    if inv.type == 'out_invoice':
                        amt = -(line.allocation)
                    else:
                        amt = line.allocation
        else:
            for line in self.line_ids:
                if line.invoice_id.id == inv.id:
                    if inv.type == 'in_invoice':
                        amt = line.allocation
                    else:
                        amt = -(line.allocation)
        return amt

    @api.multi
    def _create_multi_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment
            references invoice(s) they are reconciled.
            Return the journal entry.
        """
        move = super(account_payment, self)._create_multi_payment_entry(amount)
        if not move:
            # print ('---_XXX')
            # print (amount)
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            invoice_currency = False
            if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
                # if all the invoices selected share the same currency, record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id

            move = self.env['account.move'].create(self._get_move_vals())

            ################ Prepare for liquidity #############################
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id,
                                                                  invoice_currency)
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0

            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            ################ Prepare for liquidity #############################


            p_id = str(self.partner_id.id)
            pay_amt = 0
            for inv in self.invoice_ids:
                amt = self.get_inv_pay_amount(inv)
                if amt:
                    pay_amt += amt
                    debit, credit, amount_currency, currency_id = \
                        aml_obj.with_context(date=self.payment_date). \
                            compute_amount_fields(amt, self.currency_id,
                                                  self.company_id.currency_id,
                                                  invoice_currency)
                    # Write line corresponding to invoice payment
                    counterpart_aml_dict = \
                        self._get_shared_move_line_vals(debit,
                                                        credit, amount_currency,
                                                        move.id, False)
                    counterpart_aml_dict.update(
                        self._get_counterpart_move_line_vals(inv))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    # print('-COUNTER')
                    # print(counterpart_aml_dict)
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    # Reconcile with the invoices and write off
                    inv.register_payment(counterpart_aml)

                    # Write counterpart lines
                    # if not self.currency_id != self.company_id.currency_id:
                    #     amount_currency = 0
                    # liquidity_aml_dict = \
                    #     self._get_shared_move_line_vals(credit, debit,
                    #                                     -amount_currency, move.id,
                    #                                     False)
                    #
                    # liquidity_aml_dict.update(
                    #     self._get_liquidity_move_line_vals(-amount))
                    # print ('liquidity_aml_dict')
                    # print (liquidity_aml_dict)
                    # aml_obj.create(liquidity_aml_dict)

            ##################### for Write off while still open ###############
            if self.payment_difference_handling == 'open' and self.payment_difference:
                # print "OPEN and DIFF"
                if self.post_diff_acc == 'multi':
                    # print "OPEN and DIFF and MULTI"
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

                        # print ('WRITE-off')
                        # print (writeoff_line)
                        writeoff_line = aml_obj.create(writeoff_line)
                        # print "writeoff_line after"
                        # print writeoff_line
                        #
                        # print ('------')
                        # print (liquidity_aml_dict['debit'])
                        # print (liquidity_aml_dict['credit'])
                        # print (credit_wo)
                        # print(debit_wo)
                        # print (amount_currency_wo)
                        # print (woff_payment.payment_id)
                        if not self.name_old:
                            ############# This condition difference from not account payment with wht, due to deduction on liquidity instead of counter part
                            if liquidity_aml_dict['debit'] or (
                                    liquidity_aml_dict['debit'] == 0.0 and self.payment_type == 'inbound'):
                                liquidity_aml_dict['debit'] += credit_wo - debit_wo
                            else:
                                liquidity_aml_dict['credit'] += debit_wo - credit_wo

                            liquidity_aml_dict['amount_currency'] -= amount_currency_wo

                        # if not woff_payment.payment_id:
                        #     if liquidity_aml_dict['debit'] or (
                        #                 liquidity_aml_dict['debit'] == 0.0 and self.payment_type == 'outbound'):
                        #         liquidity_aml_dict['debit'] += credit_wo - debit_wo
                        #     else:
                        #         liquidity_aml_dict['credit'] += debit_wo - credit_wo
                        #
                        #     liquidity_aml_dict['amount_currency'] -= amount_currency_wo
                        #

                        # print ('-AFTER')
                        # print(liquidity_aml_dict['debit'])
                        # print(liquidity_aml_dict['credit'])
            ##################### for Write off while still open ###############
            if self.full_reco:
                # print ('--------FULL REC')
                o_amt = amount - pay_amt

                debit, credit, amount_currency, currency_id = \
                    aml_obj.with_context(date=self.payment_date). \
                        compute_amount_fields(o_amt, self.currency_id,
                                              self.company_id.currency_id,
                                              invoice_currency)
                # Write line corresponding to invoice payment
                counterpart_aml_dict = \
                    self._get_shared_move_line_vals(debit,
                                                    credit, amount_currency,
                                                    move.id, False)
                counterpart_aml_dict.update(
                    self._get_counterpart_move_line_vals(False))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                # Reconcile with the invoices and write off
                #                inv.register_payment(counterpart_aml)

                # Write counterpart lines
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                liquidity_aml_dict = \
                    self._get_shared_move_line_vals(credit, debit,
                                                    -amount_currency, move.id,
                                                    False)
                liquidity_aml_dict.update(
                    self._get_liquidity_move_line_vals(-amount))

                aml_obj.create(liquidity_aml_dict)
            else:
                # print ('-NOT FULL')
                # print (liquidity_aml_dict)

                if self.payment_account_id:
                    liquidity_aml_dict.update({'account_id': self.payment_account_id.id})

                aml_obj.create(liquidity_aml_dict)
                #######################################################################







            move.post()
            return move

    ############################################ REMOVE THIS to work with thai accounting#################
    # @api.multi
    # def _create_payment_entry(self, amount):
    #     if self.invoice_ids and self.line_ids and self.payment_for == 'multi_payment':
    #         moves = self._create_multi_payment_entry(amount)
    #         return moves
    #     return super(account_payment, self)._create_payment_entry(amount)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
