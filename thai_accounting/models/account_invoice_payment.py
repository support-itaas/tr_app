# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    payment_id = fields.Many2one('account.payment',string='Payment',copy=False)


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        print ('----------POST from Thai Accounting-----')
        precision = self.env['decimal.precision'].precision_get('Product Price')
        if self.payment_difference_handling == 'reconcile' and self.post_diff_acc == 'multi':
            amount = 0     ########### this is diff to put in simple "write off account"
            amount_final_diff = 0
            print('aaaaaaaaa')
            # caculate total write off amount
            if self.writeoff_multi_acc_ids:
                for payment in self.writeoff_multi_acc_ids:
                    amount += payment.amount
                    print('bbbbbb')
            if self.writeoff_account_id and float_compare(float(abs(self.payment_difference)), float(abs(amount)),
                                                          precision_digits=precision) != 0:
                amount_final_diff = self.payment_difference - amount
                print('cccccccccc')

            # recheck to ensure that writeoff amount is the same with payment difference
            #print "********************"
            print ('self.payment_difference',self.payment_difference)
            print ('amount',amount)
            print ('amount_final_diff',amount_final_diff)
            #print "********************"
            #############################28-04-2020 / self.payment_difference get zero when install dev_inovice_multi_payment ###################, so temporary remove
            # if self.payment_type == 'inbound' and float_compare(float(abs(self.payment_difference)), float(abs(amount+amount_final_diff)),
            #                                                     precision_digits=precision) != 0:
            #     raise UserError(
            #         _("The sum of write off amounts customer and payment difference amounts are not equal."))
            # elif self.payment_type == 'outbound' and float_compare(float(abs(self.payment_difference)), float(abs((amount+amount_final_diff))),
            #                                                        precision_digits=precision) != 0:
            #     raise UserError(
            #         _("The sum of write off amounts supplier and payment difference amounts are not equal."))
            #############################28-04-2020 / self.payment_difference get zero when install dev_inovice_multi_payment ###################

        # if customer invoice and not generate tax invoice, then will automatically generate and also will do tax reverse if require.
        if self.invoice_ids and self.invoice_ids[0].type in ('out_invoice'):
            for invoice in self.invoice_ids:
                if not invoice.tax_inv_generated and self.env.user.company_id.invoice_step == '2step':
                    date = self.payment_date
                    # หลาย inv รวมเป็น 1 Tax Inv
                    # invoice.action_generate_tax_inv(date)
                    print('ddddddddddd')

        # if vendor bill require reverse tax
        if self.invoice_ids and self.invoice_ids[0].type in ('in_invoice'):
            for invoice in self.invoice_ids:
                if invoice.adjust_require and invoice.adjust_move_id:
                    invoice.action_move_tax_reverse_create()
                    print('eeeeeee')




        print ('----xxx')
        super(account_payment, self).post()

        # if payment by cheque
        if self.bank_cheque and self.cheque_bank:
            # print "yes cheque"
            if self.invoice_ids and self.invoice_ids[0].type in ('out_invoice', 'out_refund'):
                type = 'rec'
            else:
                type = 'pay'

            amount = 0
            if self.writeoff_multi_acc_ids and len(self.invoice_ids) == 1:
                for payment in self.writeoff_multi_acc_ids:
                    amount += payment.amount
                # sum_amount = self.amount - amount
            # else:
                # sum_amount = self.amount

            # print("amount", amount)
            # print("sum_amount", sum_amount)
            print ('self.payment_difference',self.payment_difference)
            print ('self.amount',self.amount)

            vals_cheque_rec = {
                'issue_date': self.payment_date,
                'ref': self.communication,
                'cheque_bank': self.cheque_bank.id,
                'partner_id': self.partner_id.id,
                'cheque_branch': self.cheque_branch,
                'cheque_number': self.cheque_number,
                'cheque_date': self.cheque_date,
                'amount': self.amount,
                # 'amount': sum_amount,
                'journal_id': self.journal_id.id,
                'user_id': self.env.user.id,
                'communication': self.remark,
                'company_id': self.env.user.company_id.id,
                'type': type,
                'payment_id': self.id,
                'move_id': self.move_line_ids[0].move_id.id,
            }

            self.cheque_reg_id = self.env['account.cheque.statement'].create(vals_cheque_rec).id
            print("self.cheque_reg_id:",self.cheque_reg_id)
            # raise UserError(_('cheque_reg_id'))

        # add payment to each invoice

        if self.invoice_ids:
            if self.invoice_ids[0].type in ('out_invoice','out_refund'):
                if self.invoice_ids[0].number[0:2] == 'SH':
                    sequence = self.invoice_ids[0].journal_id.payment_sequence_id
                    tax_inv_no = sequence.with_context(ir_sequence_date=self.payment_date).next_by_id()
                    for inv in self.invoice_ids:
                        print('inv:',inv.number)
                        print('inv:',inv.number[0:2])
                        if inv.number[0:2] == 'SH':
                            inv.write({'payment_id': self.id,
                                       'tax_inv_no': tax_inv_no,
                                       'tax_inv_generated': True,
                                       })
                            if not inv.tax_inv_date:
                                inv.write({'tax_inv_date': self.payment_date,

                                           })
                            self.name = tax_inv_no
                            self.move_name = tax_inv_no
                            for account_move_ids in self.move_line_ids:
                                print('account_move_ids:', account_move_ids.move_id.name)
                                account_move_ids.move_id.name = tax_inv_no
                                account_move_ids.name = tax_inv_no

                else:
                    sequence = self.journal_id.payment_sequence_id
                    if sequence:
                        tax_inv_no = sequence.with_context(ir_sequence_date=self.payment_date).next_by_id()
                    else:
                        if self.payment_type == 'outbound':
                            tax_inv_no = self.journal_id.payment_sequence_id.with_context(
                                ir_sequence_date=self.payment_date).next_by_id()
                        else:
                            tax_inv_no = self.name

                    for inv in self.invoice_ids:
                        if not inv.tax_inv_no:
                            # sequence = self.journal_id.payment_sequence_id
                            # if sequence:
                            #     tax_inv_no = sequence.with_context(ir_sequence_date=self.payment_date).next_by_id()
                            # else:
                            #     if self.payment_type == 'outbound':
                            #         tax_inv_no = self.journal_id.payment_sequence_id.with_context(
                            #             ir_sequence_date=self.payment_date).next_by_id()
                            #     else:
                            #         tax_inv_no = self.name

                            inv.write({'payment_id': self.id,
                                       'tax_inv_no': tax_inv_no,
                                       'tax_inv_generated': True,
                                       })
                            if not inv.tax_inv_date:
                                inv.write({'tax_inv_date': self.payment_date,

                                           })
                            self.name = tax_inv_no
                            self.move_name = tax_inv_no
                            for account_move_ids in self.move_line_ids:
                                print('account_move_ids:', account_move_ids.move_id.name)
                                account_move_ids.move_id.name = tax_inv_no
                                account_move_ids.name = tax_inv_no

                        else:

                            inv.write({'payment_id': self.id,
                                       })
                            if not inv.tax_inv_date:
                                inv.write({'tax_inv_date': self.payment_date,
                                           })
                            self.name = tax_inv_no
                            self.move_name = tax_inv_no
                            for account_move_ids in self.move_line_ids:
                                print('account_move_ids:', account_move_ids.move_id.name)
                                account_move_ids.move_id.name = tax_inv_no
                                account_move_ids.name = tax_inv_no
            else:
                print('xxxxxxxxxxx')
                print('move_name:',self.move_name)
                print('move_name:',self.move_name)
                self.name = self.move_name
                for account_move_ids in self.move_line_ids:
                    print('account_move_ids:', account_move_ids.move_id.name)
                    account_move_ids.move_id.name = self.move_name
                    account_move_ids.name = self.move_name






