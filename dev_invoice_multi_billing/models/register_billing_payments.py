# -*- coding: utf-8 -*-

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
class Register_billing_payments(models.Model):
    _inherit = 'register.billing.payments'

    
    
    invoice_register_ids = fields.One2many('bulk.register.invoice', 'bulk_billing_id', string='Invoice')
    is_partial_selected_invoice = fields.Boolean(string='Is Partial Selected Invoice', default=False)
    multi = fields.Boolean(string='Multi',
                           help='Technical field indicating if the user selected invoices from multiple partners or from different types.')
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

            print("total:",total)
        return total


    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        amount = self._compute_payment_amount(invoices) if self.multi else self.amount
        print("self.multi:",self.multi)
        print("self.amount:",self.amount)
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        ############## new for multi-write-off############
        writeoff_multi_ids = []
        for writeoff_multi in self.writeoff_multi_acc_ids:
            writeoff_multi_ids.append(writeoff_multi.id)
            print("writeoff_multi_ids:",writeoff_multi_ids)


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

        #############This is remove due to difference partner register at the same time, so could not group
        # if self.multi:
        #     groups = self._groupby_invoices()
        #     return [self._prepare_payment_vals(invoices) for invoices in groups.values()]
        ############ 07-12-2019

        return [self._prepare_payment_vals(self._get_invoices())]


    @api.multi
    def create_payment(self):
        print ('create_payment_custome_2:')
        if len(self.invoice_register_ids) == 1:
            print ('aaaa')
            context = dict(self._context or {})
            active_id = context.get('active_id')
            payment = self.env['account.payment'].create(self.get_payment_vals())
            payment.post()
            bill_record = self.env[context.get('active_model')].browse(active_id)
            if bill_record.residual <= 0:
                bill_record.write({'state':'paid'})
            return {'type': 'ir.actions.act_window_close'}
        else:
            print ('MULTI PAID BILLING')
            vals = []
            for line in self.invoice_register_ids:
                print ('LINE====:',line)
                print ('LINE====:',line.invoice_id)
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
            print ('valsssssssssss:',vals)
            new_vals = sorted(vals, key=itemgetter('commercial_partner_id'))
            print('new_vals:',new_vals)
            groups = itertools.groupby(new_vals, key=operator.itemgetter('commercial_partner_id'))
            print('groups:',groups)
            result = [{'commercial_partner_id': k, 'values': [x for x in v]} for k, v in groups]
            print('result:',result)
            new_payment_ids = []
            for res in result:
                print('resssssss:',res)
                payment_method_id = self.env['account.payment.method'].search([('name', '=', 'Manual')], limit=1)
                print ('payment_method_id:',payment_method_id)
                if not payment_method_id:
                    payment_method_id = self.env['account.payment.method'].search([], limit=1)
                payment_val = self.get_payments_vals()
                print ('payment_val:',payment_val)
                pay_val = payment_val[0]
                pay_val['state'] = 'draft'
                pay_val['payment_for'] = 'multi_payment'
                print ('pay_val:',pay_val)
                payment_id = self.env['account.payment'].create(pay_val)
                print('payment_id:',payment_id)
                line_list = []
                paid_amt = 0
                inv_ids = []
                print ('Value:',res.get('values'))
                for inv_line in res.get('values'):
                    invoice = inv_line.get('invoice_id')
                    inv_ids.append(invoice.id)
                    full_reco = False
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
                temp_amount = payment_id.amount
                print('line_list:',line_list)
                print('inv_ids:',inv_ids)
                payment_id.write({
                    'line_ids': line_list,
                    'invoice_ids': [(6, 0, inv_ids)]
                })
                pay_amt = 0
                for pay in payment_id.line_ids:
                    pay_amt += pay.allocation
                # if self.is_partial_selected_invoice:
                print('pay_amt:',pay_amt)
                payment_id.amount = pay_amt
                payment_id.is_partial_selected_invoice = True
                print ('temp_amount:',temp_amount)
                payment_id.post()
                payment_id.write({
                    'amount': temp_amount,
                })
                if payment_id.cheque_reg_id:
                    payment_id.cheque_reg_id.write({
                        'amount': temp_amount,
                    })
                new_payment_ids.append(payment_id.id)
            print ("new_payment_idsssssssss:",new_payment_ids)
            return {
                'name': _('Payments'),
                'domain': [('id', 'in', new_payment_ids), ('state', '=', 'posted')],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }


    @api.model
    def default_get(self, fields):
        res =  super(Register_billing_payments, self).default_get(fields)
        print ('---RES-AccountRegisterPayment-default_get')
        print (res)
        billing_ids = self._context.get('active_ids')
        print ('===START')
        print(billing_ids)
        vals = []
        invoice_ids = self.env['customer.billing'].browse(billing_ids)
        inv_type = ''
        for invo in invoice_ids:
            inv_type = invo.type
            break
        curr_pool = self.env['res.currency']
        comp_currency = self.env.user.company_id.currency_id
        for inv in invoice_ids.mapped('invoice_ids'):
            if inv.state != 'open':
                raise ValidationError('Please Select Open Invoices.')
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
        res.update({
            'invoice_register_ids': vals,
            'currency_id': self.env.user.company_id.currency_id and self.env.user.company_id.currency_id.id or False,
        })

        return res


    @api.onchange('invoice_register_ids','invoice_register_ids.paid_amount')
    def onchange_invoice_register_ids(self):
        print ('onchange_invoice_register_ids')
        due_amount = 0
        paid_amount = 0
        if self.invoice_register_ids:
            for line in self.invoice_register_ids:
                due_amount += line.amount
                paid_amount += line.paid_amount

            if float_compare(float(abs(due_amount)), float(abs(paid_amount)),precision_digits=2) != 0:
                print ('cccccccccccccccccc')
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
