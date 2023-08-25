# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import itertools
from operator import itemgetter
import operator
from datetime import date
from odoo.tools.float_utils import float_compare

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}

class bulk_register_invoice(models.TransientModel):
    _name = 'bulk.register.invoice'
    
    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    customer_billing_id = fields.Many2one('customer.billing',string='Customer Billing')
    partner_id = fields.Many2one('res.partner',string='Partner')
    inv_amount = fields.Float('Original Amount')
    amount = fields.Float('Amount')
    paid_amount = fields.Float('Pay Amount') 
    bulk_invoice_id = fields.Many2one('account.register.payments')
    bulk_billing_id = fields.Many2one('register.billing.payments')
    currency_id = fields.Many2one('res.currency', string='Currency')


class AccountRegisterPayment(models.Model):
    _inherit = 'account.register.payments'

    @api.model
    def default_get(self, fields):
        res = super(AccountRegisterPayment, self).default_get(fields)
        print ('---RES-AccountRegisterPayment-default_get')
        print (res)
        inv_ids = self._context.get('active_ids')
        vals = []
        invoice_ids = self.env['account.invoice'].browse(inv_ids)
        inv_type = ''
        for invo in invoice_ids:
            inv_type = invo.type
            break
        curr_pool = self.env['res.currency']
        comp_currency = self.env.user.company_id.currency_id
        for inv in invoice_ids:
            ############# REMOVE BY JA - 28/09/2020 ##########
            # if inv_type != inv.type:
            #     raise ValidationError('You must select only invoices or refunds.')
            ############# REMOVE BY JA - 28/09/2020 ##########
            if inv.state != 'open':
                raise ValidationError('Please Select Open Invoices.')
            inv_currency = inv.currency_id
            pay_date = date.today()
            currency_id = comp_currency.with_context(date=pay_date)
            amount = curr_pool._compute(inv.currency_id, currency_id, inv.residual) * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type]
            inv_amt = curr_pool._compute(inv.currency_id, currency_id, inv.amount_total) * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type]

            vals.append((0, 0, {
                'invoice_id': inv and inv.id or False,
                'partner_id': inv and inv.partner_id.id or False,
                'inv_amount': inv_amt or 0.0,
                'amount': amount or 0.0,
                'paid_amount': amount or 0.0,
                'currency_id': currency_id and currency_id.id or False,
            }))
            ############ REMOVE on 11.0.1.4 due to type could not confirm in case mix between invoice and credit note
            # if inv.type in ('out_invoice', 'out_refund'):
            #     res.update({
            #         'partner_type': 'customer',
            #     })
            # else:
            #     res.update({
            #         'partner_type': 'supplier',
            #     })
        ############ REMOVE on 11.0.1.4 due to type could not confirm in case mix between invoice and credit note
        # if inv_type in ('out_invoice', 'out_refund'):
        #     res.update({
        #         'payment_type': 'inbound'
        #     })
        # else:
        #     res.update({
        #         'payment_type': 'outbound'
        #     })
        # print ('-------UPDATE')
        # print (vals)
        res.update({
            'invoice_register_ids': vals,
            'currency_id': self.env.user.company_id.currency_id and self.env.user.company_id.currency_id.id or False,
        })
        # print ('--------------LOOP INVOICE RGEITER')
        # for inv in res['invoice_register_ids']:
        #
        #     print (inv[0]['invoice_id'])
        #     print (inv[0]['partner_id'])
        # print (res)
        return res

    ####### duplicate with existing field
    # name = fields.Char('Name', default='hello')
    # payment_type = fields.Selection(
    #     [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Transfer')], string="Payment Type",
    #     required="1")
    # payment_date = fields.Date('Payment Date', required="1", default=fields.Datetime.now)
    # communication = fields.Char('Memo')
    # partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')], string='Partner Type')

    #########change from invoice_ids to invoice_register_ids
    invoice_register_ids = fields.One2many('bulk.register.invoice', 'bulk_invoice_id', string='Invoice')


    @api.onchange('invoice_register_ids','invoice_register_ids.paid_amount')
    def onchange_invoice_register_ids(self):
        due_amount = 0
        paid_amount = 0
        if self.invoice_register_ids:
            for line in self.invoice_register_ids:
                due_amount += line.amount
                paid_amount += line.paid_amount

            if float_compare(float(abs(due_amount)), float(abs(paid_amount)),precision_digits=2) != 0:
                self.is_partial_selected_invoice = True
                self.payment_difference_handling = 'open'

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        curr_pool = self.env['res.currency']
        if self.currency_id:
            # print ('------CURRENCY')
            # print (self.currency_id)
            for invoice in self.invoice_register_ids:
                if self.currency_id.id != invoice.currency_id.id:
                    currency_id = self.currency_id.with_context(date=self.payment_date)
                    amount = curr_pool._compute(invoice.currency_id, currency_id, invoice.amount)
                    paid_amount = curr_pool._compute(invoice.currency_id, currency_id, invoice.paid_amount)
                    inv_amount = curr_pool._compute(invoice.currency_id, currency_id, invoice.inv_amount)
                    invoice.inv_amount = inv_amount
                    invoice.amount = amount
                    invoice.paid_amount = paid_amount
                    invoice.currency_id = self.currency_id.id

    # @api.onchange('journal_id')
    # def onchange_journal(self):
    #     if self.journal_id:
    #         if self.journal_id and self.journal_id.currency_id:
    #             self.currency_id = self.journal_id.currency_id and self.journal_id.currency_id.id or False,
    #         else:
    #             self.currency_id = self.env.user.company_id and self.env.user.company_id.id or False
    #     else:
    #         self.currency_id = self.env.user.company_id and self.env.user.company_id.id or False

    ################Replace create_payments in account_register_payment file in Thai_Accounting#######Jatupong - 28/04/2020
    @api.multi
    def create_payments(self):
        print('------create_payments#2')
        vals = []
        # print ('-----------')
        print('INVOICE-MULTI-create_payments-2')
        if not self.is_partial_selected_invoice:
            print('---SIMPLE PAYMENT--')
            return super(AccountRegisterPayment, self).create_payments()
        else:
            print('PARTIAL PAYMENT')
            for line in self.invoice_register_ids:
                if line.paid_amount > 0.0:
                    # print (line.invoice_id)
                    # print(line.partner_id)
                    vals.append({
                        'invoice_id': line.invoice_id or False,
                        'partner_id': line.partner_id and line.partner_id.id or False,
                        'commercial_partner_id': line.invoice_id.bill_to_id and line.invoice_id.bill_to_id.id or False,
                        'amount': line.amount or 0.0,
                        'paid_amount': line.paid_amount or 0.0,
                        'currency_id': line.currency_id.id or False,
                        'inv_amount': line.inv_amount or 0.0,
                    })
            # print (vals)
            new_vals = sorted(vals, key=itemgetter('commercial_partner_id'))
            groups = itertools.groupby(new_vals, key=operator.itemgetter('commercial_partner_id'))
            result = [{'commercial_partner_id': k, 'values': [x for x in v]} for k, v in groups]
            new_payment_ids = []
            for res in result:
                payment_method_id = self.env['account.payment.method'].search([('name', '=', 'Manual')], limit=1)
                if not payment_method_id:
                    payment_method_id = self.env['account.payment.method'].search([], limit=1)

                ############Change pay_val to get_payment_values
                payment_val = self.get_payments_vals()
                pay_val = payment_val[0]
                print ('-PAY VAL-1')
                print (pay_val)
                ##################################################################Jatupong - 28/04/2020#########
                # pay_val = {
                #     'payment_type': self.payment_type,
                #     'payment_date': self.payment_date,
                #     'partner_type': self.partner_type,
                #     'payment_for': 'multi_payment',
                #     'partner_id': res.get('partner_id'),
                #     'journal_id': self.journal_id and self.journal_id.id or False,
                #     'communication': self.communication,
                #     'payment_method_id': payment_method_id and payment_method_id.id or False,
                #     'state': 'draft',
                #     'currency_id': self.currency_id and self.currency_id.id or False,
                #     'amount': 0.0,
                # }
                # pay_val['amount'] = 0.00
                pay_val['state'] = 'draft'
                pay_val['payment_for'] = 'multi_payment'
                # print('-PAY VAL-2')
                # print (pay_val)
                # print (xxx)
                ##################################################################Jatupong - 28/04/2020#########
                payment_id = self.env['account.payment'].create(pay_val)
                line_list = []
                paid_amt = 0
                inv_ids = []
                for inv_line in res.get('values'):
                    invoice = inv_line.get('invoice_id')
                    inv_ids.append(invoice.id)
                    full_reco = False
                    # print (invoice.number)
                    # print (invoice.residual)
                    # print (inv_line.get('paid_amount'))
                    if invoice.residual == inv_line.get('paid_amount'):
                        full_reco = True
                    line_list.append((0, 0, {
                        'invoice_id': invoice.id,
                        'account_id': invoice.account_id and invoice.account_id.id or False,
                        'date': invoice.date_invoice,
                        'due_date': invoice.date_due,
                        'original_amount': inv_line.get('inv_amount'),
                        'balance_amount': inv_line.get('amount'),
                        'allocation': inv_line.get('paid_amount'),
                        'full_reconclle': full_reco,
                        'account_payment_id': payment_id and payment_id.id or False,
                        'currency_id': inv_line.get('currency_id'),
                    }))
                    paid_amt += inv_line.get('paid_amount')


                # print ('------Payment Amount')
                # print (payment_id.amount)
                ############# TEMP Amount will be used to update after post ############
                temp_amount = payment_id.amount
                payment_id.write({
                    'line_ids': line_list,
                    'invoice_ids': [(6, 0, inv_ids)]
                })
                pay_amt = 0
                for pay in payment_id.line_ids:
                    pay_amt += pay.allocation

                #################This is for partial payment - JA - 02/11/2020 ########
                ################# if partial ,then has to send full amount due to multi payment need to correct something
                ################ if account.register.payment and not partial payment then use normal amount, this mean deduect some amount #######
                if self.is_partial_selected_invoice:
                    payment_id.amount = pay_amt


                #payment_id.onchange_currency()
                payment_id.post()
                payment_id.write({
                    'amount': temp_amount,
                })
                new_payment_ids.append(payment_id.id)

            # print (new_payment_ids)
            return {
                'name': _('Payments'),
                'domain': [('id', 'in', new_payment_ids), ('state', '=', 'posted')],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
            ####################Remove old return
            # return True
