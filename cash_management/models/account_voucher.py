# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from bahttext import bahttext

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, date
from odoo.osv import expression

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'
    _rec_name = 'number'

    employee_id = fields.Many2one('hr.employee',string="Employee", track_visibility='onchange')

    @api.model
    def _default_journal(self):
        voucher_type = self._context.get('voucher_type', 'sale')
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', '=', voucher_type),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    # @api.model
    # def _default_journal(self):
    #
    #     res = super(AccountVoucher, self)._default_journal()
    #     voucher_type = self._context.get('voucher_type', 'sale')
    #     voucher_type_new = self._context.get('voucher_type_new')
    #
    #     print('_default_journal')
    #     print(voucher_type)
    #     print(voucher_type_new)
    #
    #     if voucher_type_new == 'cash' and self.env.user.cash_management_journal_id:
    #         return self.env.user.cash_management_journal_id
    #
    #     else:
    #         company_id = self._context.get('company_id', self.env.user.company_id.id)
    #         domain = [
    #             ('type', '=', voucher_type),
    #             ('company_id', '=', company_id),
    #         ]
    #         return self.env['account.journal'].search(domain, limit=1)

    voucher_type_new = fields.Selection([('cash', 'cash'), ('normal', 'normal')], string='Voucher Type (New)')
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit',
                                        default=lambda self:
                                        self.env['res.users'].
                                        operating_unit_default_get(self._uid),
                                        readonly=True,
                                        states={'draft': [('readonly',False)]}, track_visibility='onchange')
    voucher_no = fields.Char(string='Voucher No',copy=False, track_visibility='onchange')
    cheque_regis_id = fields.Many2one('account.cheque.statement',string='Cheque ID',copy=False)
    account_id = fields.Many2one('account.account', 'Account',required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, track_visibility='onchange')
    reference = fields.Char('Bill Reference', readonly=True, states={'draft': [('readonly', False)]},
                            help="The partner reference of this document.", copy=False, track_visibility='onchange')
    amount = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_total', track_visibility='onchange')
    tax_amount = fields.Monetary(readonly=True, store=True, compute='_compute_total', track_visibility='onchange')
    tax_correction = fields.Monetary(readonly=True, states={'draft': [('readonly', False)]},
                                     help='In case we have a rounding problem in the tax, use this field to correct it', track_visibility='onchange')
    date_due = fields.Date('Due Date', readonly=True, index=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=_default_journal, track_visibility='onchange')
    cheque_bank = fields.Many2one('res.bank', string="Bank", copy=False, track_visibility='onchange')

    def baht_text(self, all_debit):
        return bahttext(all_debit)

    def _compute_payment_journal_id(self):
        for voucher in self:
            if voucher.voucher_type_new != 'cash':
                if voucher.pay_now != 'pay_now':
                    continue
                domain = [
                    ('type', 'in', ('bank', 'cash')),
                    ('company_id', '=', voucher.company_id.id),
                ]
                if voucher.account_id and voucher.account_id.internal_type == 'liquidity':
                    print ('--------111')
                    field = 'default_credit_account_id' if voucher.voucher_type == 'sale' else 'default_credit_account_id'
                    domain.append((field, '=', voucher.account_id.id))

                if voucher.voucher_type == 'sale':
                    print ('---------sale')
                    voucher.payment_journal_id = voucher.journal_id
                    if voucher.journal_id.bank_for_cheque_account_id:
                        print('11---')
                        voucher.account_id = voucher.journal_id.bank_for_cheque_account_id
                    else:
                        print('222---')
                        voucher.account_id = voucher.journal_id.default_credit_account_id
                else:
                    print ('---33')
                    voucher.payment_journal_id = self.env['account.journal'].search(domain, limit=1)
            else:
                print ("SKIP")

    def _inverse_payment_journal_id(self):
        for voucher in self:
            if voucher.voucher_type_new != 'cash':
                if voucher.pay_now != 'pay_now':
                    continue
                if voucher.voucher_type == 'sale':
                    print ('------xxxxxxxxxxx')
                    if voucher.journal_id.bank_for_cheque_account_id:
                        voucher.account_id = voucher.journal_id.bank_for_cheque_account_id
                    else:
                        voucher.account_id = voucher.payment_journal_id.default_credit_account_id
                else:
                    voucher.account_id = voucher.payment_journal_id.default_credit_account_id
            else:
                print ('SKIP2')

    @api.model
    def default_get(self, fields):
        vals = super(AccountVoucher, self).default_get(fields)
        # print ("DEFAULT")
        # print(vals)
        if self.env.user.cash_management_journal_id:
            vals['journal_id'] = self.env.user.cash_management_journal_id.id
            vals['account_id'] = self.env.user.cash_management_journal_id.default_credit_account_id.id
        # print(vals)
        return vals

    # @api.multi
    # def copy(self, default=None):
    #     # operating_unit_id = vals.get('operating_unit_id') or self.operating_unit_id
    #     # company_id = vals.get('company_id') or self.company_id
    #
    #     # if not operating_unit_id:
    #     #     raise UserError(_("Please setup OU/Branch first"))
    #     #
    #     sequence_id = self.env['ir.sequence'].search([('code', '=', 'cash.voucher.no'), ('operating_unit_id', '=', default['operating_unit_id']),
    #          ('company_id', '=', default['company_id'])], limit=1)
    #     if not sequence_id:
    #         raise UserError(_("Please setup sequence for Cash Management first"))
    #
    #     default['voucher_no'] = sequence_id.next_by_id()
    #
    #     return super(AccountVoucher,self).copy(default=default)

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        res = super(AccountVoucher,self).first_move_line_get(move_id,company_currency,current_currency)
        if self.voucher_type == 'cash':
            print (res)
            res['operating_unit_id'] = self.operating_unit_id.id
            # res['department_id'] = self.operating_unit_id.id
            # res['remark'] = 'aaaaaaaaaaaaaaaaaaa'
        return res

    @api.model
    def create(self, vals):
        print ('VOUCHER')
        voucher_no = vals.get('voucher_no') or self.voucher_no
        operating_unit_id = vals.get('operating_unit_id')
        # company_id = vals.get('company_id') or self.company_id
        voucher_type_new = vals.get('voucher_type_new') or self.voucher_type_new
        journal_id = vals.get('journal_id') or self.journal_id

        print (voucher_type_new)

        if voucher_type_new == 'cash' and not operating_unit_id:
            raise UserError(_("Please setup OU/Branch first"))

        if voucher_type_new == 'cash' and not voucher_no:

            # sequence_id = self.env['ir.sequence'].search([('code','=','cash.voucher.no'),('operating_unit_id','=',operating_unit_id.id),('company_id','=',company_id.id)],limit=1)

            if not journal_id:
                raise UserError(_("Please setup sequence for Cash Management Journal first"))

            sequence_id = self.env['account.journal'].browse(journal_id).voucher_sequence_id
            print(self.journal_id.name)
            print(journal_id)
            print(sequence_id)
            print('---------------')

            if not sequence_id:
                raise UserError(_("Please setup sequence for Cash Management Journal first"))
            print ('----CREATE-1')
            print (self.date)
            print (vals.get('date'))
            vals['voucher_no'] = sequence_id.with_context(ir_sequence_date=vals.get('date')).next_by_id()

        if voucher_type_new != 'cash':
            if not journal_id:
                raise UserError(_("Please setup sequence for Voucher first"))

            sequence_id = self.env['account.journal'].browse(journal_id).sequence_id



            if not sequence_id:
                raise UserError(_("Please setup sequence for Voucher first"))
            # print('----CREATE-2')
            # print(self.date)
            vals['number'] = sequence_id.with_context(ir_sequence_date=vals.get('date')).next_by_id()

        return super(AccountVoucher, self).create(vals)

    @api.multi
    def write(self, vals):
        for voucher_id in self:
            voucher_no = vals.get('voucher_no') or voucher_id.voucher_no
            operating_unit_id = vals.get('operating_unit_id') or voucher_id.operating_unit_id
            company_id = vals.get('company_id') or voucher_id.company_id
            voucher_type_new = vals.get('voucher_type_new') or voucher_id.voucher_type_new
            journal_id = vals.get('journal_id') or voucher_id.journal_id

            if voucher_type_new == 'cash' and not operating_unit_id:
                raise UserError(_("Please setup OU/Branch first"))

            if voucher_type_new == 'cash' and not voucher_no:
                print(journal_id)
                print('=========')
                # sequence_id = self.env['ir.sequence'].search([('code','=','cash.voucher.no'),('operating_unit_id','=',operating_unit_id.id),('company_id','=',company_id.id)],limit=1)
                sequence_id = journal_id.voucher_sequence_id
                if not sequence_id:
                    raise UserError(_("Please setup sequence for Cash Management Journal first"))
                vals['voucher_no'] = sequence_id.next_by_id()
        res = super(AccountVoucher, self).write(vals)
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            args = expression.AND([
                args or [],
                ['|',('number', operator, name), ('voucher_no', operator, name)]
            ])
        return super(AccountVoucher, self).name_search(name, args, operator, limit)

    @api.multi
    def update_department_voucher_one_by_one(self):
        # voucher_ids = self.env['account.voucher'].search(
        #     [('move_id', '!=', False), ('voucher_no', '!=', False), ('employee_id', '!=', False),
        #      ('voucher_type', '=', 'purchase')])
        for voucher in self:
            for ml in voucher.move_id.line_ids.filtered(lambda x: x.name and x.name[0:10] == voucher.voucher_no):
                ml.update({'invoice_date': voucher.date,
                           'department_id': voucher.employee_id.department_id.id})

    @api.multi
    def update_department_voucher(self):
        voucher_ids = self.env['account.voucher'].search([('move_id','!=',False),('voucher_no','!=',False),('employee_id','!=',False),('voucher_type','=','purchase')])
        for voucher in voucher_ids:
            for ml in voucher.move_id.line_ids.filtered(lambda x: x.name and x.name[0:10] == voucher.voucher_no):
                ml.update({'invoice_date': voucher.date,
                           'department_id': voucher.employee_id.department_id.id})


class account_move_line(models.Model):
    _inherit = 'account.move.line'
    _order = 'is_split asc, is_debit desc, id asc'

    is_split = fields.Boolean(string='Split Group')

    @api.model
    def create(self, vals):
        res = super(account_move_line, self).create(vals)
        # print('create : ', vals)
        if 'invoice_id' in vals and 'invoice_date' not in vals:
            invoice_id = self.env['account.invoice'].browse(vals.get('invoice_id'))
            # res.update({'invoice_date': invoice_id.date_invoice})
            res['invoice_date'] = invoice_id.date_invoice

        return res


class account_voucher_line(models.Model):
    _inherit = 'account.voucher.line'

    # invoice_date = fields.Date(string="Invoice/Bill Date")
    employee_id = fields.Many2one('hr.employee',string='Employee')
    department_id = fields.Many2one('hr.department', string="Department",readonly=False,related=False)
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit')
    note = fields.Char(string='Note')

    #Start ticket #2019
    ############ Add for employee and department get the same with voucher level and change able
    @api.model
    def create(self, vals):
        res = super(account_voucher_line, self).create(vals)
        if not res.employee_id and not res.department_id:
            res.write({'employee_id': res.voucher_id.employee_id.id})
            res.write({'department_id': res.voucher_id.employee_id.department_id.id})
        return res

    ########### add function change employee then department will also be update
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for line in self:
            if line.employee_id:
                line.department_id = line.employee_id.department_id
    #end ticket #2019

    @api.model
    def write(self, vals):
        res = super(account_voucher_line, self).write(vals)
        msg = ''
        if 'name' in vals:
            name = vals.get('name')
        else:
            name = self.name
        if 'account_id' in vals and vals.get('account_id'):
            account_id = self.env['account.account'].browse(vals.get('account_id'))
            msg += '<li><B>%s</B></li>' % (name)
            msg += '<li>Account: %s <B>--></B> %s </li>' % (self.account_id.name, account_id.name)

        if msg:
            message_post = '<ul>'+msg+'</ul>'
            # print('message_post : ',message_post)
            self.voucher_id.message_post(body=_(message_post))

        return res

    def _prepare_voucher_to_move_line(self, move_id, credit_amount, debit_amount, amount_currency, currency_id,
                                      payment_id):
        print('_prepare_voucher_to_move_line : ',self)
        res = super(account_voucher_line, self)._prepare_voucher_to_move_line(move_id, credit_amount, debit_amount,
                                                                              amount_currency, currency_id, payment_id)
        res.update({'department_id': self.department_id.id})
        # print('res : ', res)
        return res


class CashManagementAdvance(models.TransientModel):
    _name = "cash.management.advance"
    _description = "Cash Management Advance"

    cheque_bank = fields.Many2one('res.bank', string="เบิกชดเชยจากธนาคาร")
    account_id = fields.Many2one('account.account',sring='Account')
    validate_date = fields.Date(string='Date')
    remark = fields.Char(string='รายละเอียด')

    def create_cheque_record(self,move_id,total_amount,journal_id,voucher_ids):
        print('create_cheque_record')

        type = 'pay'

        if journal_id.cheque_journal_id:
            journal_id = journal_id.cheque_journal_id

        vals_cheque_rec = {
            'issue_date': self.validate_date,
            'ref': self.remark,
            'cheque_bank': self.cheque_bank.id,
            # 'partner_id': self.partner_id.id,
            # 'cheque_branch': self.cheque_branch,
            # 'cheque_number': self.cheque_number,
            'cheque_date': self.validate_date,
            'amount': total_amount,
            'journal_id': journal_id.id,
            'user_id': self.env.user.id,
            # 'communication': self.remark,
            'company_id': self.env.user.company_id.id,
            'type': type,
            'move_id': move_id.id,
            # 'payment_id': self.id,
        }
        print ('FOR CH')
        print (vals_cheque_rec)


        cheque_exist_ids = voucher_ids.filtered(lambda r: r.cheque_sequence_number != False)
        if cheque_exist_ids and len(voucher_ids) != len(cheque_exist_ids):
            raise UserError(_('Please check some voucher already issue check'))

        if cheque_exist_ids:
            vals_cheque_rec['name'] = cheque_exist_ids[0].cheque_sequence_number

        cheque_reg_id = self.env['account.cheque.statement'].create(vals_cheque_rec)

        if cheque_reg_id:
            for voucher in voucher_ids:
                voucher.cheque_sequence_number = cheque_reg_id.name
                voucher.cheque_regis_id = cheque_reg_id

        return cheque_reg_id.name

    @api.multi
    def create_return_cash_by_cheque(self,move_id,cheque_number):

        ##############Return Cash Account
        return_amount = sum(line.debit for line in move_id.line_ids)

        move_line_cash_return = {
            'journal_id': move_id.journal_id.id,
            'name': self.remark ,
            'account_id': move_id.journal_id.default_debit_account_id.id,
            'move_id': move_id.id,
            'operating_unit_id': move_id.line_ids[0].operating_unit_id.id,
            # 'partner_id': line.partner_id.id or self.partner_id.commercial_partner_id.id,
            # 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
            ''
            'quantity': 1,
            'credit': 0,
            'debit': return_amount,
            # 'ref': self.reference,
            # 'invoice  _date': line.bill_date or self.date,
            'date': self.validate_date,
            'is_split': True,
            # 'amount_before_tax': line.amount_before_tax,
            # 'tax_ids': [(4, t.id) for t in line.tax_ids],
            # 'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
            # 'currency_id': company_currency != current_currency and current_currency or False,
            # 'payment_id': self._context.get('payment_id'),
            # 'wht_type': line.wht_type,
            # 'wht_personal_company': line.wht_personal_company,
        }

        move_line_cash_return_from_cheque = {
            'journal_id': move_id.journal_id.id,
            'name': str(self.cheque_bank.name) + "-" + str(cheque_number),
            'account_id': move_id.journal_id.return_cash_account_id.id,
            'move_id': move_id.id,
            'operating_unit_id': move_id.line_ids[0].operating_unit_id.id,
            # 'partner_id': line.partner_id.id or self.partner_id.commercial_partner_id.id,
            # 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
            'quantity': 1,
            'credit': return_amount,
            'debit': 0,
            'is_split': True,
            # 'ref': line.bill_ref or self.reference,
            # 'invoice_date': line.bill_date or self.date,
            'date': self.validate_date,
            # 'amount_before_tax': line.amount_before_tax,
            # 'tax_ids': [(4, t.id) for t in line.tax_ids],
            # 'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
            # 'currency_id': company_currency != current_currency and current_currency or False,
            # 'payment_id': self._context.get('payment_id'),
            # 'wht_type': line.wht_type,
            # 'wht_personal_company': line.wht_personal_company,
        }
        # new_return_amount = move_line_cash_return_from_cheque + move_line_cash_return
        # self.env['account.move.line'].create(move_line_cash_return_from_cheque)
        # self.env['account.move.line'].create(move_line_cash_return)
        print("1")
        self.env['account.move.line'].with_context(check_move_validity=False).create(move_line_cash_return)
        print("3")
        self.env['account.move.line'].with_context(check_move_validity=False).create(move_line_cash_return_from_cheque)
        print("2")


        #############################################################################################################################



    @api.model
    def default_get(self, fields):
        res = super(CashManagementAdvance, self).default_get(fields)
        res.update({'validate_date': str(datetime.today().date())})
        return res

    @api.multi
    def prepare_voucher_pay_now_payment_create(self,voucher_ids):
        payment_methods = voucher_ids[0].journal_id.outbound_payment_method_ids
        payment_type = 'outbound'
        partner_type = 'supplier'
        sequence_code = 'account.payment.supplier.invoice'
        name = self.env['ir.sequence'].with_context(ir_sequence_date=self.validate_date).next_by_code(sequence_code)
        amount = sum(voucher.amount for voucher in voucher_ids)
        return {
            'name': name,
            'payment_type': payment_type,
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'partner_type': partner_type,
            # 'partner_id': self.partner_id.commercial_partner_id.id,
            'amount': amount,
            'currency_id': voucher_ids[0].currency_id.id,
            'payment_date': self.validate_date,
            'journal_id': voucher_ids[0].journal_id.id,
            'company_id': voucher_ids[0].company_id.id,
            # 'department_id': voucher_ids[0].department_id.id,
            # 'communication': self.name,
            'state': 'reconciled',
        }
    #
    # @api.multi
    # def validate_view(self):
    #     self.validate()
    #

    @api.multi
    def action_view_journal(self,move_id):
        # invoices = self.mapped('invoice_ids')
        # action = self.env.ref('action_cash_management_view_journal_form')
        # action['res_id'] = move_id.ids[0]
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = move_id.id

        return action

    @api.multi
    def validate(self):
        voucher_ids = self.env['account.voucher'].browse(self._context.get('active_ids', []))
        print(voucher_ids)
        print('========================')
        local_context = dict(self._context, force_company=voucher_ids[0].journal_id.company_id.id)
        if voucher_ids[0].move_id:
            voucher_ids[0]
        company_currency = voucher_ids[0].journal_id.company_id.currency_id.id
        current_currency = voucher_ids[0].currency_id.id or company_currency
        # we select the context to use accordingly if it's a multicurrency case or not
        # But for the operations made by _convert_amount, we always need to give the date in the context
        ctx = local_context.copy()
        ctx['date'] = self.validate_date
        ctx['check_move_validity'] = False
        # Create a payment to allow the reconciliation when pay_now = 'pay_now'.

        ###################Prepare and do it later
        # if self.pay_now == 'pay_now' and self.amount > 0:
        prepare_voucher_paymet = self.prepare_voucher_pay_now_payment_create(voucher_ids)
        ctx['payment_id'] = self.env['account.payment'].create(prepare_voucher_paymet).id
        # print(ctx['payment_id'])
        # Create the account move record.

        #####################
        move = self.env['account.move'].create(voucher_ids[0].account_move_get())

        final_line_total = 0
        # move_line_all =
        for voucher in voucher_ids:
            print(voucher)
            print('---------')

            voucher_first_line = voucher.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency)
            print ('first voucher line')
            print (voucher_first_line)
            print (move.line_ids)
            print (move.line_ids.filtered(lambda r: r.account_id.id == voucher_first_line['account_id']))
            print ('sssssss')


            if move.line_ids and move.line_ids.filtered(lambda r: r.account_id.id == voucher_first_line['account_id']):
                print ('11--')
                move_line = move.line_ids.filtered(lambda r: r.account_id.id == voucher_first_line['account_id'])
                move_line.debit += voucher_first_line['debit']
                move_line.credit += voucher_first_line['credit']
                # move_line.name = 'รวมเบิก'
                move_line.invoice_date = voucher.date

            else:
                print('22--')
                move_line = self.env['account.move.line'].with_context(ctx).create(voucher_first_line)
                move_line.invoice_date = voucher.date
                move_line.name = 'รวมเบิก'
                # move_line.voucher_line_id = voucher.line_ids[0].id

            # print (move_line.debit)
            # print (move_line.credit)

            line_total = move_line.debit - move_line.credit
            if voucher.voucher_type == 'sale':
                line_total = line_total - voucher._convert_amount(voucher.tax_amount)
            elif voucher.voucher_type == 'purchase':
                line_total = line_total + voucher._convert_amount(voucher.tax_amount)
            # Create one move line per voucher line where amount is not 0.0

            # ticekt#2101
            # final_line_total += line_total
            final_line_total += voucher.amount
            # ticekt#2101

            # print ('CREATE-ALL-LINE-BF')
            voucher.with_context(ctx).voucher_move_line_create(line_total, move.id, company_currency,
                                                               current_currency)
            # print('CREATE-ALL-LINE-AF')

            # Add tax correction to move line if any tax correction specified
            if voucher.tax_correction != 0.0:
                tax_move_line = self.env['account.move.line'].search(
                    [('move_id', '=', move.id), ('tax_line_id', '!=', False)], limit=1)
                if len(tax_move_line):
                    tax_move_line.write(
                        {'debit': tax_move_line.debit + voucher.tax_correction if tax_move_line.debit > 0 else 0,
                         'credit': tax_move_line.credit + voucher.tax_correction if tax_move_line.credit > 0 else 0})

            # We post the voucher.

            # move_line_no_voucher_ids = move.line_ids.filtered(lambda r: r.voucher_line_id == False)
            # if move_line_no_voucher_ids:
            #     for move_line_voucher in move_line_no_voucher_ids:
            #         move_line_voucher.voucher_line_id =

            voucher.write({
                'move_id': move.id,
                'state': 'posted',
                'number': move.name
            })
            # for voucher date----------------------------------------------------
            print('voucher.voucher_no')
            for ml in move.line_ids.filtered(lambda x: x.name[0:10] == voucher.voucher_no):
                ml.update({
                    'invoice_date': voucher.date,
                    # T22028604 แก้ไขที่แก้ไข department หน้า Cash Management ให้รายการที่แก้ไข department เปลี่ยนค่าด้วยที่ ่journal enter by IT
                    # 'department_id': voucher.employee_id.department_id.id
                })

        if self.cheque_bank:
            cheque_number = self.create_cheque_record(move, abs(final_line_total), voucher_ids[0].journal_id, voucher_ids)
            self.create_return_cash_by_cheque(move,cheque_number)


        move.post()

        if self._context.get('open_je', False):
            return self.action_view_journal(move)
        return {'type': 'ir.actions.act_window_close'}

        return True

