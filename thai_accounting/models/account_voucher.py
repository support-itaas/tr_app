# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    bank_cheque = fields.Boolean(string='Is Cheque', related='payment_journal_id.bank_cheque')
    # this is new bank list from res.bank
    cheque_bank = fields.Many2one('res.bank', string="Bank",copy=False)
    cheque_branch = fields.Char(string="Branch",copy=False)
    cheque_number = fields.Char(string="Cheque Number",copy=False)
    cheque_date = fields.Date(string="Cheque Date",copy=False)
    cheque_sequence_number = fields.Char(string='Check Sequence Number',copy=False)
    voucher_no = fields.Char(string='Voucher No', copy=False)


    # @api.model
    # def _default_journal(self):
    #     voucher_type = self._context.get('voucher_type', 'sale')
    #     company_id = self._context.get('company_id', self.env.user.company_id.id)
    #     domain = [
    #         ('type', '=', voucher_type),
    #         ('company_id', '=', company_id),
    #     ]
    #     return self.env['account.journal'].search(domain, limit=1)

    #
    # @api.multi
    # def update_bill_date(self):
    #     for line in self.line_ids:
    #         if line.bill_date and line.account_id and line.account_id:
    #             # print "11111111"
    #             journal_item_line = self.env['account.move.line'].search([('move_id','=',self.move_id.id),('account_id','=',line.account_id.id),('invoice_date','=',False)],limit=1)
    #             if journal_item_line:
    #                 # print "update-1"
    #                 journal_item_line.write({'invoice_date': line.bill_date})


    # @api.multi
    # def write(self, vals):
    #     print "WRITE AV-VALS"
    #     print vals
    #     res = super(AccountVoucher, self).write(vals)
    #     return res
    # payment_journal_id = fields.Many2one('account.journal', string='Payment Method', readonly=True,store=True,
    #                                      states={'draft': [('readonly', False)]},
    #                                      domain="[('type', 'in', ['cash', 'bank'])]",compute=False,inverse=False
    #                                      )


    # @api.onchange('payment_journal_id')
    # def onchange_payment_journal_id(self):
    #     if self.payment_journal_id and self.payment_journal_id.default_debit_account_id:
    #         self.account_id = self.payment_journal_id.default_debit_account_id

    # @api.depends('company_id', 'pay_now', 'account_id')
    # def _compute_payment_journal_id(self):
    #     print "Update 1"
    #     return True
    #     # for voucher in self:
    #     #     if voucher.pay_now != 'pay_now':
    #     #         continue
    #         # domain = [
    #         #     ('type', 'in', ('bank', 'cash')),
    #         # ]
    #         # if voucher.account_id and voucher.account_id.internal_type == 'liquidity':
    #         #     field = 'default_debit_account_id' if voucher.voucher_type == 'sale' else 'default_credit_account_id'
    #         #     domain.append((field, '=', voucher.account_id.id))
    #         # voucher.payment_journal_id = self.env['account.journal'].search(domain, limit=1)
    #
    # def _inverse_payment_journal_id(self):
    #     return True

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        for line in self.line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            line_subtotal = line.price_subtotal
            if self.voucher_type == 'sale':
                line_subtotal = -1 * line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(line.price_unit*line.quantity)

            if self.voucher_type == 'sale' and amount >= 0:
                credit_amount = abs(amount)
                debit_amount = 0.00
            elif self.voucher_type == 'sale' and amount < 0:
                credit_amount = 0.00
                debit_amount = abs(amount)

            elif self.voucher_type == 'purchase' and amount >= 0:

                credit_amount = 0.00
                debit_amount = abs(amount)

            elif self.voucher_type == 'purchase' and amount < 0:
                credit_amount = abs(amount)
                debit_amount = 0.00

            amount_currency = line_subtotal if current_currency != company_currency else 0.0
            currency_id = company_currency != current_currency and current_currency or False
            payment_id = self._context.get('payment_id')
            move_line = line._prepare_voucher_to_move_line(move_id,credit_amount,debit_amount,amount_currency,currency_id,payment_id)
            # move_line = {
            #     'journal_id': self.journal_id.id,
            #     'name': str(voucher_name) + "-" + str(line.name),
            #     'operating_unit_id': line.operating_unit_id.id or self.operating_unit_id.id,
            #     'account_id': line.account_id.id,
            #     'move_id': move_id,
            #     'partner_id': line.partner_id.id or self.partner_id.commercial_partner_id.id,
            #     'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
            #     'quantity': 1,
            #     'credit': credit_amount,
            #     'debit': debit_amount,
            #     'ref': line.bill_ref or self.reference,
            #     'invoice_date': line.bill_date or self.date,
            #     'date': self.account_date,
            #     'amount_before_tax': line.amount_before_tax,
            #     'tax_ids': [(4,t.id) for t in line.tax_ids],
            #     'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
            #     'currency_id': company_currency != current_currency and current_currency or False,
            #     'payment_id': self._context.get('payment_id'),
            #     'wht_type': line.wht_type,
            #     'wht_personal_company': line.wht_personal_company,
            # }
            # print "MOVE LINE VOUCHER"
            # print move_line
            move_line_id = self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)

            if move_line['tax_ids']:
                # print "-------tax-ids---"
                tax_move_line_id = self.env['account.move.line'].browse(move_line_id.id+1)
                if tax_move_line_id:
                    # print "-------found tax move line"
                    tax_move_line_id.write({'invoice_date': line.bill_date or self.date})
                    tax_move_line_id.write({'amount_before_tax': move_line['credit'] or move_line['debit']})
                    tax_move_line_id.write({'ref': move_line['ref']})
                    tax_move_line_id.write({'operating_unit_id': move_line['operating_unit_id']})

        # print "AFTER voucher_move_line_create"
        # print self.env['account.move'].browse(move_id).line_ids

        return line_total

    @api.multi
    def voucher_pay_now_payment_create(self):
        if self.voucher_type == 'sale':
            payment_methods = self.journal_id.inbound_payment_method_ids
            payment_type = 'inbound'
            partner_type = 'customer'
            sequence_code = 'account.payment.customer.voucher'
        else:
            payment_methods = self.journal_id.outbound_payment_method_ids
            payment_type = 'outbound'
            partner_type = 'supplier'
            sequence_code = 'account.payment.supplier.voucher'
        name = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(sequence_code)
        # print ('VOUCHER NAME',name)
        return {
            'name': name,
            'payment_type': payment_type,
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'partner_type': partner_type,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.date,
            'journal_id': self.payment_journal_id.id,
            'company_id': self.company_id.id,
            'communication': self.name,
            'state': 'reconciled',
        }


    @api.multi
    def action_move_line_create(self):
        res = super(AccountVoucher,self).action_move_line_create()
        print ("action_move_line_create--1")
        if self.move_id:
            for line in self.move_id.line_ids:
                if line.account_id.purchase_tax_report and not line.ref:
                    line_reference = self.move_id.line_ids.filtered(lambda x: x.partner_id.id == line.partner_id.id and x.id != line.id and x.ref != False)
                    if line_reference:
                        # print "1111111"
                        line.ref = line_reference[0].ref


        ################################################################# Create 2 Journal Item for Cash return from cheque #########

        if self.bank_cheque:
            if self.voucher_type == 'sale':
                type = 'rec'
            else:
                type = 'pay'

            vals_cheque_rec = {
                'issue_date': self.date,
                'ref': self.name,
                'cheque_bank': self.cheque_bank.id,
                'partner_id': self.partner_id.id,
                'cheque_branch': self.cheque_branch,
                'cheque_number': self.cheque_number,
                'cheque_date': self.cheque_date,
                'amount': self.amount,
                'journal_id': self.payment_journal_id.id,
                'user_id': self.env.user.id,
                # 'communication': self.remark,
                'company_id': self.env.user.company_id.id,
                'type': type,
                'move_id': self.move_id.id,
                # 'payment_id': self.id,
            }

            if self.cheque_sequence_number:

                vals_cheque_rec['name'] = self.cheque_sequence_number

            cheque_reg_id = self.env['account.cheque.statement'].create(vals_cheque_rec)

            if cheque_reg_id:
                self.cheque_sequence_number = cheque_reg_id.name
                self.cheque_regis_id = cheque_reg_id


        return res

    @api.multi
    def cancel_voucher(self):
        for voucher in self:
            if voucher.cheque_sequence_number:
                cheque_id = self.env['account.cheque.statement'].search(
                    [('name', '=', voucher.cheque_sequence_number),('company_id', '=', voucher.company_id.id)], limit=1)
                if cheque_id and cheque_id.state != 'confirm':
                    cheque_id.sudo().unlink()
                elif cheque_id and cheque_id.state == 'confirm':
                    cheque_id.sudo().action_cancel()
                    cheque_id.sudo().unlink()

            super(AccountVoucher, self).cancel_voucher()
        self.write({'state': 'cancel', 'move_id': False})

    @api.multi
    def account_move_get(self):
        if self.number:
            name = self.number
        elif self.journal_id.sequence_id:
            if not self.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move = {
            'name': name,
            'journal_id': self.journal_id.id,
            'narration': self.narration,
            'date': self.account_date,
            'ref': self.reference,
            'cheque_bank': self.cheque_bank.id,
            'cheque_branch': self.cheque_branch,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,
        }
        return move

class account_voucher_line(models.Model):
    _inherit = 'account.voucher.line'

    wht_type = fields.Selection([('1%', '1%'), ('2%', '2%'), ('3%', '3%'), ('5%', '5%')], string='WHT')
    wht_personal_company = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53')],string="WHT Type")
    partner_id = fields.Many2one('res.partner',string='Partner')
    bill_ref = fields.Char(string='Bill Ref')
    bill_date = fields.Date(string='Bill Date')
    amount_before_tax = fields.Float(string='Amount Before Tax')

    def _prepare_voucher_to_move_line(self,move_id,credit_amount,debit_amount,amount_currency,currency_id,payment_id):
        voucher_name = self.voucher_id.voucher_no or self.voucher_id.number
        move_line = {
            'journal_id': self.voucher_id.journal_id.id,
            'name': str(voucher_name) + "-" + str(self.name),
            'operating_unit_id': self.operating_unit_id.id or self.voucher_id.operating_unit_id.id,
            'account_id': self.account_id.id,
            'move_id': move_id,
            'partner_id': self.partner_id.id or self.voucher_id.partner_id.commercial_partner_id.id,
            'analytic_account_id': self.account_analytic_id and self.account_analytic_id.id or False,
            'quantity': 1,
            'credit': credit_amount,
            'debit': debit_amount,
            'ref': self.bill_ref or self.voucher_id.reference,
            'invoice_date': self.bill_date or self.voucher_id.date,
            'date': self.voucher_id.account_date,
            'amount_before_tax': self.amount_before_tax,
            'tax_ids': [(4, t.id) for t in self.tax_ids],
            'amount_currency': amount_currency,
            'currency_id': currency_id,
            'payment_id': payment_id,
            'wht_type': self.wht_type,
            'wht_personal_company': self.wht_personal_company,
        }

        return move_line


