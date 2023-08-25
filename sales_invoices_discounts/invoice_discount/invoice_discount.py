from __future__ import division
from odoo import fields, models, api ,_
import odoo.addons.decimal_precision as dp
# from odoo.tools import amount_to_text_en
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class ResCompany(models.Model):
    _inherit = "res.company"

    default_sales_discount_account_id = fields.Many2one('account.account', string='Default Sales Discount Account')
    default_purchase_discount_account_id = fields.Many2one('account.account',
                                                           string='Default Purchase Discount Account')

# class account_config_settings(models.TransientModel):
#     _inherit = 'account.config.settings'
#
#     default_sales_discount_account_id = fields.Many2one('account.account', string='Default Sales Discount Account')
#     default_purchase_discount_account_id = fields.Many2one('account.account', string='Default Purchase Discount Account')
#
#     @api.model
#     def get_default_sales_discount_account_id(self, fields):
#         conf = self.env['ir.config_parameter']
#         company_id = self.env.user.company_id
#         # print company_id.default_sales_discount_account_id
#         return {
#             'default_sales_discount_account_id': company_id.default_sales_discount_account_id.id
#         }
#
#     @api.model
#     def get_default_purchase_discount_account_id(self, fields):
#         conf = self.env['ir.config_parameter']
#         company_id = self.env.user.company_id
#         # print company_id.default_purchase_discount_account_id
#         return {
#             'default_purchase_discount_account_id': company_id.default_purchase_discount_account_id.id
#         }
#
#     @api.multi
#     def set_default_sales_discount_account_id(self):
#         # conf = self.env['ir.config_parameter']
#         company_id = self.env.user.company_id
#         company_id.default_sales_discount_account_id = self.default_sales_discount_account_id
#
#     @api.multi
#     def set_default_purchase_discount_account_id(self):
#         # conf = self.env['ir.config_parameter']
#         company_id = self.env.user.company_id
#         company_id.default_purchase_discount_account_id = self.default_purchase_discount_account_id



class invoice_discount(models.Model):
    _inherit = 'account.invoice'

    discount_view = fields.Selection([('After Tax', 'After Tax'), ('Before Tax', 'Before Tax')], string='Discount Type',
                                     states={'draft': [('readonly', False)]},
                                     help='Choose If After or Before applying Taxes type of the Discount')

    discount_type = fields.Selection([('Fixed', 'Fixed'), ('Percentage', 'Percentage')], string='Discount Method',
                                     states={'draft': [('readonly', False)]},
                                     help='Choose the type of the Discount')
    discount_value = fields.Float(string='Discount Value', states={'draft': [('readonly', False)]},
                                  help='Choose the value of the Discount')
    discounted_amount = fields.Float(compute='disc_amount', string='Discounted Amount', readonly=True)
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_compute_amount')

    is_new_vat_compute = fields.Boolean(string='Round Global', default=True)

    @api.multi
    def apply_new_vat(self):
        self._compute_amount()

    # def get_amount(self, amt, row, bow):
    #     amount_in_word = amount_to_text_en.amount_to_text(amt, row, bow)
    #     return amount_in_word

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    # @api.one
    # @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'discount_type', 'discount_value', 'discount_view')
    # def _compute_amounts(self):
    #     self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
    #     self.amount_tax = sum(line.amount for line in self.tax_line)
    #     if self.discount_view == 'After Tax':
    #         if self.discount_type == 'Fixed':
    #             self.amount_total = self.amount_untaxed + self.amount_tax - self.discount_value
    #         elif self.discount_type == 'Percentage':
    #             amount_to_dis = (self.amount_untaxed + self.amount_tax) * (self.discount_value / 100)
    #             self.amount_total = (self.amount_untaxed + self.amount_tax) - amount_to_dis
    #         else:
    #             self.amount_total = self.amount_untaxed + self.amount_tax
    #     elif self.discount_view == 'Before Tax':
    #         if self.discount_type == 'Fixed':
    #             the_value_before = self.amount_untaxed - self.discount_value
    #             self.amount_total = the_value_before + self.amount_tax
    #         elif self.discount_type == 'Percentage':
    #             amount_to_dis = (self.amount_untaxed) * (self.discount_value / 100)
    #             self.amount_total = self.amount_untaxed + self.amount_tax - amount_to_dis
    #         else:
    #             self.amount_total = self.amount_untaxed + self.amount_tax
    #     else:
    #         self.amount_total = self.amount_untaxed + self.amount_tax

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id
        if not self.discount_view:
            if self.purchase_id.discount_view and self.purchase_id.discount_type and self.purchase_id.discount_value:
                self.discount_view = self.purchase_id.discount_view
                self.discount_type = self.purchase_id.discount_type
                self.discount_value = self.purchase_id.discount_value

        return super(invoice_discount, self).purchase_order_change()

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        self.ensure_one()
        company_id = self.env.user.company_id
        # ir_values = self.env['ir.values']
        # wht_lines = {}
        # for line in self.invoice_line_ids:
        #     if line.wht_id:
        #         wht_lines[line.wht_id] = wht_lines.get(line.wht_id, 0.0) + line.amount_wht_line
        # for wht_id in wht_lines.keys():
        #     if self.type in['in_invoice','out_refund']:
        #         for x in move_lines:
        #             acc_id = self.pool.get('res.partner').browse(self._cr, self._uid, x[2]['partner_id'], self._context).property_account_payable_id.id
        #             if x[2]['name'] is '/' and x[2]['account_id'] == acc_id:
        #                 x[2]['credit'] -= wht_lines[wht_id]
        #         # added one more line to reduce with holding tax from payable/receivable amount
        #         move_lines.append((0, 0, {
        #                                 'name': wht_id.name,
        #                                 'credit': wht_lines[wht_id],
        #                                 'debit': False,
        #                                 'partner_id': self.partner_id.id,
        #                                 'account_id': wht_id.account_id.id,
        #                                 }))
        #     else:
        #         for x in move_lines:
        #             acc_id = self.pool.get('res.partner').browse(self._cr, self._uid, x[2]['partner_id'], self._context).property_account_receivable_id.id
        #             if x[2]['name'] is '/' and x[2]['account_id'] == acc_id:
        #                 x[2]['debit'] -= wht_lines[wht_id]
        #         move_lines.append((0, 0, {
        #                                 'name': wht_id.name,
        #                                 'credit': False,
        #                                 'debit': wht_lines[wht_id],
        #                                 'partner_id': self.partner_id.id,
        #                                 'account_id': wht_id.account_id.id
        #                                 }))

        if self.discounted_amount:
            deduct_tax_due_amount = 0.0
            # taxes_id = ir_values.get_default('product.template', 'taxes_id', company_id=self.company_id.id)
            # supplier_taxes_id = ir_values.get_default('product.template', 'supplier_taxes_id',
            #                                           company_id=self.company_id.id)
            #
            #
            # t_id = self.env['account.tax'].browse(taxes_id)
            # s_id = self.env['account.tax'].browse(supplier_taxes_id)

            t_id = self.env['account.tax'].search([('tax_report', '=', True), ('type_tax_use', '=', 'sale')], limit=1)
            s_id = self.env['account.tax'].search([('tax_report', '=', True), ('type_tax_use', '=', 'purchase')],
                                                  limit=1)
            if self.type in ['in_invoice', 'out_refund']:
                if self.discount_view == "Before Tax":
                    if s_id.amount:
                        deduct_tax_due_amount = (self.discounted_amount * s_id.amount / 100)
                    else:
                        deduct_tax_due_amount = (self.discounted_amount * 7 / 100)

                for x in move_lines:
                    acc_id = self.env['res.partner'].browse(x[2]['partner_id']).property_account_payable_id.id

                    if x[2]['name'] is '/' and x[2]['account_id'] == acc_id:
                        x[2]['credit'] -= self.discounted_amount
                        x[2]['credit'] -= deduct_tax_due_amount
                    if x[2]['account_id'] == s_id.account_id.id:
                        x[2]['debit'] -= deduct_tax_due_amount
                # added one more line to reduce with holding tax from payable/receivable amount
                if not company_id.default_purchase_discount_account_id.id:
                    raise UserError(_('Please setup account code for discount'))
                move_lines.append((0, 0, {
                                        'name': 'Discount',
                                        'credit': self.discounted_amount,
                                        'debit': False,
                                        'partner_id': self.partner_id.id,
                                        'account_id': company_id.default_purchase_discount_account_id.id,
                                        }))
            else:
                # print "xxxxx"
                # print self.invoice_line_ids[0].invoice_line_tax_ids[0].price_include

                if self.discount_view == "Before Tax":
                    if t_id.amount:
                        # print "xx-1"
                        deduct_tax_due_amount = (self.discounted_amount * t_id.amount / 100)
                    else:
                        # print "xx-2"
                        deduct_tax_due_amount = (self.discounted_amount * 7 / 100)

                # print "deduct_tax_due_amount"
                # print deduct_tax_due_amount
                for x in move_lines:
                    # print x[2]['partner_id']
                    acc_id = self.env['res.partner'].browse(x[2]['partner_id']).property_account_receivable_id.id
                    # print "ACC and Name"
                    # print acc_id
                    # print x[2]['name']
                    if (x[2]['name'] == '/' or x[2]['name'] == self.name) and x[2]['account_id'] == acc_id:
                        # print "x[2]['debit']"
                        # print x[2]['debit']
                        # print "111-222"
                        x[2]['debit'] -= self.discounted_amount
                        x[2]['debit'] -= deduct_tax_due_amount
                    if x[2]['account_id'] == t_id.account_id.id:
                        # print "222-222"
                        # print "x[2]['credit']"
                        # print x[2]['credit']
                        x[2]['credit'] -= deduct_tax_due_amount

                if not company_id.default_sales_discount_account_id.id:
                    raise UserError(_('Please setup account code for discount'))
                move_lines.append((0, 0, {
                                        'name': 'Discount',
                                        'credit': False,
                                        'debit': self.discounted_amount,
                                        'partner_id': self.partner_id.id,
                                        'account_id': company_id.default_sales_discount_account_id.id,
                                        }))
        # print "Test MOVE"
        # print move_lines

        return super(invoice_discount, self).finalize_invoice_move_lines(move_lines)



    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice','discount_type', 'discount_value', 'discount_view')
    def _compute_amount(self):
        # print "1"
        amount_untaxed = amount_tax = 0.0
        if not self.is_new_vat_compute:
            print ('OLD')
            self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
            self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        else:
            print ('NEWWW')
            for line in self.invoice_line_ids:
                price_subtotal, price_tax = line.price_subtotal_round_global()
                # print (price_subtotal)
                # print (price_tax)
                try:
                    price_subtotal = price_subtotal[0]
                    price_tax = price_tax[0]
                except:
                    price_subtotal = price_subtotal
                    price_tax = price_tax

                amount_untaxed += price_subtotal
                amount_tax += price_tax

            self.amount_untaxed = amount_untaxed
            self.amount_tax = amount_tax



        t_id = self.env['account.tax'].search([('tax_report', '=', True), ('type_tax_use', '=', 'sale')], limit=1)
        s_id = self.env['account.tax'].search([('tax_report', '=', True), ('type_tax_use', '=', 'purchase')], limit=1)


        # print self.amount_untaxed
        # print self.amount_tax
        # xx = self.amount_untaxed + self.amount_tax
        # print xx

        if self.discount_view == 'After Tax':
            if self.discount_type == 'Fixed':
                self.amount_total = self.amount_untaxed + self.amount_tax - self.discount_value
            elif self.discount_type == 'Percentage':
                amount_to_dis = (self.amount_untaxed + self.amount_tax) * (self.discount_value / 100)
                self.amount_total = (self.amount_untaxed + self.amount_tax) - amount_to_dis
            else:
                self.amount_total = self.amount_untaxed + self.amount_tax
        elif self.discount_view == 'Before Tax':
            if self.discount_type == 'Fixed':
                the_value_before = self.amount_untaxed - self.discount_value
                if t_id.amount:
                    the_tax_before = self.amount_tax - (self.discount_value * t_id.amount / 100)
                else:
                    the_tax_before = self.amount_tax - (self.discount_value * 0.07)
                self.amount_tax = the_tax_before
                self.amount_total = the_value_before + the_tax_before
            elif self.discount_type == 'Percentage':
                amount_to_dis = (self.amount_untaxed) * (self.discount_value / 100)
                the_value_before = self.amount_untaxed - amount_to_dis
                if t_id.amount:
                    the_tax_before = self.amount_tax - (amount_to_dis * t_id.amount / 100)
                else:
                    the_tax_before = self.amount_tax - (amount_to_dis * 0.07)
                self.amount_tax = the_tax_before
                self.amount_total = the_value_before + the_tax_before
            else:
                self.amount_total = self.amount_untaxed + self.amount_tax
        else:
            self.amount_total = self.amount_untaxed + self.amount_tax

        # ----------------------------------------------------------
        # amount_tax = self.amount_untaxed * 7 / 100
        # # print('---------------')
        # # print (self.amount_tax)
        # diff = amount_tax - self.amount_tax
        # # print (diff)
        #
        # # print (float_compare(abs(diff),0.02,precision_digits=2))
        # # if diff more than 0.02 then not due to vat cal, back to use standard cal tax
        # if float_compare(abs(diff),0.02,precision_digits=2) > 0:
        #     # print ('DIFFF')
        #     amount_tax = self.amount_tax
        #
        #
        # ############### if include vat
        # if self.invoice_line_ids and self.invoice_line_ids[0].invoice_line_tax_ids and not self.invoice_line_ids[0].invoice_line_tax_ids[0].price_include:
        #     # print ('YYYYYYYYYYYYYY')
        #     amount_tax = round(amount_tax, 2)
        #     self.amount_tax = amount_tax
        #
        #
        # # print(self.amount_tax)
        # self.amount_total = round(self.amount_untaxed + self.amount_tax,2)

        # ---------------------------------------------------------------------------


        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1


        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign



    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'discount_type', 'discount_value')
    def disc_amount(self):
        if self.discount_view == 'After Tax':
            if self.discount_type == 'Fixed':
                self.discounted_amount = self.discount_value
            elif self.discount_type == 'Percentage':
                amount_to_dis = (self.amount_untaxed + self.amount_tax) * (self.discount_value / 100)
                self.discounted_amount = amount_to_dis
            else:
                self.discounted_amount = 0
        elif self.discount_view == 'Before Tax':
            if self.discount_type == 'Fixed':
                self.discounted_amount = self.discount_value
            elif self.discount_type == 'Percentage':
                amount_to_dis = self.amount_untaxed * (self.discount_value / 100)
                self.discounted_amount = amount_to_dis
            else:
                self.discounted_amount = 0
        else:
            self.discounted_amount = 0


invoice_discount()



