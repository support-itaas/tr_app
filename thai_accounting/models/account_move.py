# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import math
from bahttext import bahttext




class account_move(models.Model):
    _inherit = "account.move"
    _order = 'date asc'

    wht_reference = fields.Char(string="WHT Reference",default=False)
    wht_generated = fields.Boolean(string='WHT Generated',default=False)
    invoice_date = fields.Date(string="Invoice/Bill Date", readonly=True, states={'draft': [('readonly', False)]})
    remark = fields.Char(string="Payment Remark")
    # this is the old bank text input
    # cheque_bank = fields.Char(string="Bank")

    # this is new bank list from res.bank
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    cash_advance_status = fields.Boolean(string="Cash Advance Pending",default=False)
    department_id = fields.Many2one('hr.department',string="แผนก")
    supplier_name_text = fields.Char('Partner Name (Manual)')
    supplier_address_text = fields.Char('Partner Address')
    supplier_branch_text = fields.Integer('Partner Branch (Manual)')
    supplier_taxid_text = fields.Char('Tax ID (Manual)')
    wht_personal_company = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53'),('50-1', 'ภงด1')],string="WHT Type")
    is_closing_month = fields.Boolean(string='Closing Month')
    is_manual_partner = fields.Boolean(string='Partner Manual')



    def print_account(self):

        # print ('----------print_account')
        journal_item = []
        journal_ids = []

        # print len(self.line_ids)

        move_line_ids = self.get_payment_invoice()
        if move_line_ids:
            print ('5555')
            new_move_line_ids = self.line_ids + move_line_ids
        else:
            new_move_line_ids = self.line_ids
        # print ('---------------------')
        # print move_line_ids
        # print ('--------ALL')
        # print len(new_move_line_ids)

        if new_move_line_ids:
            for line in new_move_line_ids:
                print ('--------------------------------------')
                print (line.id)
                account_id_code = line.account_id.code
                account_id_name = line.account_id.name
                department_id_name = line.department_id.name
                account_id_label = line.name

                # print ('^^^^^^^^^^^^^^^^^^^^^^^')
                # print(account_id_name)
                # print(account_id_code)
                # print line.department_id.name
                # print line.debit
                # print line.credit
                # print ('--------------------')



                ##############This is per line - change to group by account code jatupong - 23-04-2020 ##########
                # value = {'account_id_name': account_id_name,
                #          'account_id_code': account_id_code,
                #          'department_id_name': department_id_name,
                #          'account_id_label': account_id_label,
                #          'debit': line.debit,
                #          'credit': line.credit}
                # journal_item.append(value)
                ############################################################################

                ############################################### Check duplicate account code to one line ###################
                # val_new = {
                #     'account_id_code': account_id_code,
                #     'department_id_name':department_id_name,
                # }


                if account_id_code not in journal_ids:
                    print ('-NEW')
                    journal_ids.append(account_id_code)

                    value = {'account_id_name': account_id_name,
                             'account_id_code': account_id_code,
                             'department_id_name':department_id_name,
                             'account_id_label': account_id_label,
                             'debit': line.debit,
                             'credit': line.credit}

                    journal_item.append(value)

                ############## same account, then consider department ##########3
                else:
                    print ('EXIST ACCOUNT')
                    same_account_same_department_id = False
                    ############# has department #########
                    if line.department_id:
                        print ('YES DEPT:')
                        # print (line.department_id.name)
                        ############ USE to get record with same department of new line ##########
                        same_account_same_department_id = list(
                            filter(lambda x: x['department_id_name'] == (line.department_id.name) and x['account_id_code'] == (account_id_code), journal_item))

                        ############ has department and found the same dept ##########
                        if same_account_same_department_id:
                            print ('-SAME ACCOUNT and SAME DEPT')
                            match_same_account_same_department_same_debit_same_credit = False

                            for count in range(0,len(same_account_same_department_id)):
                                ############ has department and found the same dept and same debit value ##########
                                if same_account_same_department_id[count]['debit'] and line.debit:
                                    print ('------SAME DEBIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_debit = same_account_same_department_id[count]['debit']
                                    new_debit = old_debit + line.debit
                                    same_account_same_department_id[count]['debit'] = new_debit
                                    print (same_account_same_department_id[count]['debit'])

                                ############ has department and found the same dept and same credit value ##########
                                elif same_account_same_department_id[count]['credit'] and line.credit:
                                    print ('------SAME CREDIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_credit = same_account_same_department_id[count]['credit']
                                    new_credit = old_credit + line.credit
                                    same_account_same_department_id[count]['credit'] = new_credit
                                    print (same_account_same_department_id[count]['credit'])


                            #########################if not same debit, credit
                            if not match_same_account_same_department_same_debit_same_credit:
                                print ('------DIFF DEBIT-CREDIT')
                                journal_ids.append(account_id_code)
                                value = {'account_id_name': account_id_name,
                                         'account_id_code': account_id_code,
                                         'department_id_name': department_id_name,
                                         'account_id_label': account_id_label,
                                         'debit': line.debit,
                                         'credit': line.credit}

                                journal_item.append(value)

                        ############ has department but could not found the same dept ##########
                        else:
                            # print ('2222')
                            print ('-SAME ACCOUNT, NEW DEP')
                            journal_ids.append(account_id_code)
                            value = {'account_id_name': account_id_name,
                                     'account_id_code': account_id_code,
                                     'department_id_name': department_id_name,
                                     'account_id_label': account_id_label,
                                     'debit': line.debit,
                                     'credit': line.credit}

                            journal_item.append(value)


                    ################### NO department and same account
                    else:
                        print ('NO-DEP, SAME ACCOUNT')
                        same_account_no_department_id = list(
                            filter(lambda x: x['account_id_code'] == (line.account_id.code) and not x['department_id_name'], journal_item))
                        # print ('-SAME - NO DEPT')
                        # print (same_account_no_department_id)
                        ################### if found same account and found no department ###########
                        if same_account_no_department_id:
                            print ('SAME ACCOUNT and NO DEP')
                            match_same_account_same_department_same_debit_same_credit = False
                            for count in range(0,len(same_account_no_department_id)):

                                ############ same debit
                                if same_account_no_department_id[count]['debit'] and line.debit:
                                    print ('------SAME DEBIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_debit = same_account_no_department_id[count]['debit']
                                    new_debit = old_debit + line.debit
                                    same_account_no_department_id[count]['debit'] = new_debit
                                    print (same_account_no_department_id[count]['debit'])

                                ############ same credit
                                elif same_account_no_department_id[count]['credit'] and line.credit:
                                    print ('------SAME CREDIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_credit = same_account_no_department_id[count]['credit']
                                    new_credit = old_credit + line.credit
                                    same_account_no_department_id[count]['credit'] = new_credit
                                    print (same_account_no_department_id[count]['credit'])

                            if not match_same_account_same_department_same_debit_same_credit:
                                ############ not the same debit, credit
                                print ('------DIFF DEBIT-CREDIT')
                                value = {'account_id_name': account_id_name,
                                         'account_id_code': account_id_code,
                                         'department_id_name': department_id_name,
                                         'account_id_label': account_id_label,
                                         'debit': line.debit,
                                         'credit': line.credit}

                                journal_item.append(value)

                        ##################### in case same account but not found no department #######
                        else:
                            print ('NO DEP, SAME ACCOUNT')
                            value = {'account_id_name': account_id_name,
                                     'account_id_code': account_id_code,
                                     'department_id_name': department_id_name,
                                     'account_id_label': account_id_label,
                                     'debit': line.debit,
                                     'credit': line.credit}

                            journal_item.append(value)

        return journal_item

    @api.multi
    def get_payment_invoice(self):
        payment_ids = []
        invoice_ids = []
        tax_move_line_ids = []
        line_ids = self.line_ids.filtered(lambda x: x.payment_id != False)
        for line in line_ids:
            if line.payment_id not in payment_ids:
                payment_ids.append(line.payment_id)


        for payment in payment_ids:
            if payment.invoice_ids:
                for invoice in payment.invoice_ids:
                    if invoice not in invoice_ids:
                        invoice_ids.append(invoice)


        # print payment_ids
        # print invoice_ids
        adjust_move_ids = []
        for invoice in invoice_ids:
            if invoice.adjust_move_id and invoice.adjust_move_id not in adjust_move_ids:
                ##############for multiple invoice with same adjust, then only one is require
                ##############Jatupong - 29/03/2020

                adjust_move_ids.append(invoice.adjust_move_id)
                for line in invoice.adjust_move_id.line_ids:
                    tax_move_line_ids.append(line.id)

        print (tax_move_line_ids)
        move_line_ids = self.env['account.move.line'].browse(tax_move_line_ids)
        ########################## Order by credit or debit
        return move_line_ids


        #########################Default by ID #############
        # return move_line_ids.sorted(key=lambda r: r.id)




    @api.multi
    def get_invoice(self):
        invoice_id = self.env['account.invoice'].search([('move_id','=',self.id)])
        # print invoice_id.number
        return invoice_id

    @api.multi
    def action_gen_wht(self):
        print('action_gen_wht')
        # in case need to refer specificate date, similar syntax can be applied - with_context(ir_sequence_date=move.date)
        wht_partner_ids = []
        last_wht = ''
        for line in self.line_ids:
            print('line')
            if not self.is_check_ref:
                print('not Check REF')
                if line.account_id.wht and line.wht_type and not line.wht_reference and line.partner_id:
                    if line.wht_personal_company == 'personal':
                        print('personal:')
                        line.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
                            'wht3.no') or '/'
                        last_wht = line.wht_reference
                    elif line.wht_personal_company == 'company':
                        print('company:')

                        line.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
                            'wht53.no') or '/'
                        last_wht = line.wht_reference
                    # เอาออก ลูกค้าบอกควรเรียงเป็น seq ต่อๆ กันไม่ใช่ ซ้ำกัน
                    # wht_partner_ids.append(line.partner_id)
                # elif line.account_id.wht and line.wht_type and not line.wht_reference and line.partner_id in wht_partner_ids:
                #     line.wht_reference = last_wht
            else:
                if line.wht_personal_company == 'personal':
                    line.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
                        'wht3.no') or '/'
                    last_wht = line.wht_reference
                elif line.wht_personal_company == 'company':
                    line.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
                        'wht53.no') or '/'
                    last_wht = line.wht_reference


    # @api.multi
    # def action_gen_wht(self):
    #     # in case need to refer specificate date, similar syntax can be applied - with_context(ir_sequence_date=move.date)
    #     if self.wht_personal_company == 'personal':
    #         self.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code('wht3.no') or '/'
    #         self.wht_generated = True
    #     elif self.wht_personal_company == 'company':
    #         self.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
    #             'wht53.no') or '/'
    #         self.wht_generated = True


    @api.multi
    def post(self):
        print('=============Posttttt==============')
        invoice = self._context.get('invoice', False)
        self._post_validate()

        for move in self:
            move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    print('uuuuuuuuuuuuuuuuuuuuuuuu')
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            sequence = journal.refund_sequence_id
                        if invoice and invoice.debit_note and journal.debit_sequence_id:
                            sequence = journal.debit_sequence_id
                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))
                print('new_name:',new_name)
                if new_name:
                    move.name = new_name
                    print('move_name:',move.name)

            for line in move.line_ids:
                if line.wht_type:
                    print('wht_type')
                    self.action_gen_wht()
                    break

        return self.write({'state': 'posted'})

    def roundup(self,x):
        #print x
        #print int(math.ceil(x / 6.0)) * 6
        return int(math.ceil(x / 6.0)) * 6

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    # _order = 'debit desc'
    _order = 'is_debit desc, id asc'

    wht_type = fields.Selection([('1%','1%'),('1.5%','1.5%'),('2%','2%'),('3%','3%'),('5%','5%')],string="WHT",default=False)
    wht_personal_company = fields.Selection([('personal','ภงด3'),('company','ภงด53'),('50-1', 'ภงด1')],string="WHT Personal/Company")
    wht_reference = fields.Char(string="WHT Reference")
    invoice_date = fields.Date(string='Invoice/Bill Date',store=True)
    department_id = fields.Many2one('hr.department', string="Department")
    ref = fields.Char(related=False, string='Partner Reference', copy=False, index=True)
    sale_tax_report = fields.Boolean(string='รายงานภาษีขาย', related='account_id.sale_tax_report')
    purchase_tax_report = fields.Boolean(string='รายงานภาษีซื้อ', related='account_id.purchase_tax_report')
    amount_before_tax = fields.Float(string='Amt Before Tax')
    is_closing_month = fields.Boolean(string='Closing Month', related='move_id.is_closing_month', store=True)
    is_debit = fields.Boolean(string='Is Debit', compute='get_is_debit_credit', store=True)


    def baht_text(self, amount_total):
        return bahttext(amount_total)


    @api.depends('debit', 'credit')
    def get_is_debit_credit(self):
        for line in self:
            if line.debit:
                line.is_debit = True
            else:
                line.is_debit = False


    @api.model
    def create(self, vals, apply_taxes=True):
        print ('vals:',vals)
        MoveObj = self.env['account.move']
        if vals.get('move_id', False):
            move = MoveObj.browse(vals['move_id'])
            # print "move with new partner and ref"
            # print vals.get('ref')
            # print vals.get('partner_id')
            if not vals.get('ref', False):
                vals['ref'] = move.ref
            if not vals.get('partner_id', False):
                vals['partner_id'] = move.partner_id.id
        return super(AccountMoveLine, self).create(vals)

    def roundup(self,x):
        # print x
        # print int(math.ceil(x / 6.0)) * 6
        return int(math.ceil(x / 6.0)) * 6

    def roundupto(self,x):
        # print x
        # print int(math.ceil(x / 7.0)) * 7
        return int(math.ceil(x / 7.0)) * 7





    
