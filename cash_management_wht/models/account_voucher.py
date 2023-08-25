# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    def baht_text(self, amount_total):
        return bahttext(amount_total)

    def gen_wht_reference(self):
        line_ids = self.line_ids.filtered(lambda m: m.wht_type and m.wht_personal_company and not m.wht_reference)
        # print('line_ids :',line_ids)
        if line_ids:
            wht_personal_company = line_ids.mapped('wht_personal_company')
            for wht_pc in wht_personal_company:
                wht_line_ids = line_ids.filtered(lambda m: m.wht_personal_company == wht_pc)
                if wht_line_ids:
                    if wht_pc == 'personal':
                        wht_reference = self.env['ir.sequence'].with_context(
                            ir_sequence_date=self.date).next_by_code('wht3.no') or '/'
                    else:
                        wht_reference = self.env['ir.sequence'].with_context(
                            ir_sequence_date=self.date).next_by_code('wht53.no') or '/'

                    for wht_l in wht_line_ids:
                        wht_l.update({'wht_reference': wht_reference})


    @api.multi
    @api.depends('tax_correction', 'line_ids.price_subtotal')
    def _compute_total(self):
        tax_calculation_rounding_method = self.env.user.company_id.tax_calculation_rounding_method
        for voucher in self:
            total = 0
            tax_amount = 0
            tax_lines_vals_merged = {}
            auto_gen_wht = voucher.line_ids.filtered(lambda x: not x.price_unit)
            if auto_gen_wht:
                print('auto_gen_wht:',auto_gen_wht)
                for line in auto_gen_wht:
                    print('line:',line)
                    tax_info = line.tax_ids.compute_all(line.price_subtotal, voucher.currency_id, line.quantity, line.product_id, voucher.partner_id)
                    print('tax_info:',tax_info)
                    if tax_calculation_rounding_method == 'round_globally':
                        total += tax_info.get('total_excluded', 0.0)
                        for t in tax_info.get('taxes', False):
                            key = (
                                t['id'],
                                t['account_id'],
                            )
                            if key not in tax_lines_vals_merged:
                                tax_lines_vals_merged[key] = t.get('amount', 0.0)
                            else:
                                tax_lines_vals_merged[key] += t.get('amount', 0.0)
                    else:
                        total += tax_info.get('total_included', 0.0)
                        tax_amount += sum([t.get('amount', 0.0) for t in tax_info.get('taxes', False)])
                if tax_calculation_rounding_method == 'round_globally':
                    tax_amount = sum([voucher.currency_id.round(t) for t in tax_lines_vals_merged.values()])
                    voucher.amount = total + tax_amount + voucher.tax_correction
                else:
                    voucher.amount = total + voucher.tax_correction
                voucher.tax_amount = tax_amount
            else:
                print('not auto_gen_wht')
                return super(AccountVoucher, self)._compute_total()



class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    wht_reference = fields.Char('WHT Reference',copy=False)

    @api.one
    @api.depends('price_unit', 'tax_ids', 'quantity', 'product_id', 'voucher_id.currency_id')
    def _compute_subtotal(self):
        print('_compute_subtotal_custom;')
        if not self.price_unit and self.amount_before_tax and self.wht_type:
            print('aaaaaaa')
            wht_type_split = self.wht_type.split('%')
            wht_type = int(wht_type_split[0])
            self.price_subtotal = ((self.amount_before_tax * wht_type) / 100) * (-1)
            self.price_unit = self.price_subtotal
        else:

            return super(AccountVoucherLine, self)._compute_subtotal()




    def _prepare_voucher_to_move_line(self,move_id,credit_amount,debit_amount,amount_currency,currency_id,payment_id):
        # print('_prepare_voucher_to_move_line : ',self)
        res = super(AccountVoucherLine, self)._prepare_voucher_to_move_line(move_id,credit_amount,debit_amount,amount_currency,currency_id,payment_id)
        res.update({'wht_reference':self.wht_reference})
        # print('res : ', res)
        return res


class CashManagementAdvance(models.TransientModel):
    _inherit = "cash.management.advance"

    @api.multi
    def validate(self):
        res = super(CashManagementAdvance, self).validate()
        voucher_ids = self.env['account.voucher'].browse(self._context.get('active_ids', []))
        if voucher_ids:
            for vou in voucher_ids:
                vou.gen_wht_reference()
                vou.move_id.update({'wht_generated':True})
        return res