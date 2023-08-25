# -*- coding: utf-8 -*-
from __future__ import division
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare



class purchaseorder_discount(models.Model):
    _inherit = 'purchase.order'
    discount_view = fields.Selection([('After Tax', 'After Tax'), ('Before Tax', 'Before Tax')], string='Discount Type',
                                     states={'draft': [('readonly', False)]},
                                     help='Choose If After or Before applying Taxes type of the Discount')
    discount_type = fields.Selection([('Fixed', 'Fixed'), ('Percentage', 'Percentage')], string='Discount Method',
                                     states={'draft': [('readonly', False)]})
    discount_value = fields.Float(string='Discount Value', states={'draft': [('readonly', False)]},
                                  help='Choose the value of the Discount')
    discounted_amount = fields.Float(compute='disc_amount', string='Discounted Amount', readonly=True)

    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_amount_all')

    is_new_vat_compute = fields.Boolean(string='Round Global',default=True)

    @api.multi
    def apply_new_vat(self):
        self._amount_all()

    @api.multi
    def button_dummy(self):
        return True

    @api.depends('order_line.price_total','discount_type', 'discount_value','order_line.taxes_id')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        # ir_values = self.env['ir.values']
        # supplier_taxes_id = ir_values.get_default('product.template', 'supplier_taxes_id',
        #                                           company_id=self.company_id.id)

        s_id = self.env['account.tax'].search([('tax_report','=',True),('type_tax_use','=','purchase')],limit=1)


        for order in self:
            amount_untaxed = amount_tax = 0.0
            if not self.is_new_vat_compute:
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
            else:
                for line in order.order_line:
                    price_subtotal, price_tax = line.price_subtotal_round_global()
                    # print (price_subtotal[0])
                    # print (price_tax[0])
                    amount_untaxed += price_subtotal[0]
                    amount_tax += price_tax[0]

            #add for discount calculation
            if self.discount_view == 'After Tax':
                if self.discount_type == 'Fixed':
                    amount_total = amount_untaxed + amount_tax - self.discount_value
                elif self.discount_type == 'Percentage':
                    amount_to_dis = (amount_untaxed + amount_tax) * (self.discount_value / 100)
                    amount_total = (amount_untaxed + amount_tax) - amount_to_dis
                else:
                    amount_total = amount_untaxed + amount_tax
            elif self.discount_view == 'Before Tax':
                if self.discount_type == 'Fixed':
                    the_value_before = amount_untaxed - self.discount_value
                    if s_id.amount:
                        the_tax_before = amount_tax - (self.discount_value * s_id.amount / 100)
                    else:
                        the_tax_before = amount_tax - (self.discount_value * 0.07)
                    amount_tax = the_tax_before
                    amount_total = the_value_before + the_tax_before
                elif self.discount_type == 'Percentage':
                    amount_to_dis = amount_untaxed * (self.discount_value / 100)
                    the_value_before = amount_untaxed - amount_to_dis
                    if s_id.amount:
                        the_tax_before = amount_tax - (amount_to_dis * s_id.amount / 100)
                    else:
                        the_tax_before = amount_tax - (amount_to_dis * 0.07)

                    amount_tax = the_tax_before
                    amount_total = the_value_before + the_tax_before
                else:
                    amount_total = amount_untaxed + amount_tax
            else:
                amount_total = amount_untaxed + amount_tax

            # self.amount_tax = amount_tax
            # self.amount_total = amount_total
            # # print('PURCHASE-VAT')
            # amount_tax = order.currency_id.round(amount_untaxed) * 7/100
            # diff = amount_tax - self.amount_tax
            #
            # # print (float_compare(abs(diff),0.02,precision_digits=2))
            # # if diff more than 0.02 then not due to vat cal, back to use standard cal tax
            # if float_compare(abs(diff), 0.02, precision_digits=2) > 0:
            #     amount_tax = self.amount_tax
            #
            # # print (amount_tax)
            # amount_tax = round(amount_tax,2)





            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': order.currency_id.round(amount_total),
            })

    # Date: 25-04-60
    # Comment : แก้ไขการแสดงผลใน sale_order
    @api.one
    @api.depends('order_line.price_subtotal', 'discount_type', 'discount_value')
    def disc_amount(self):
        #orginal for V8
        # val = 0
        # for line in self.order_line:
        #     val += self._amount_line_tax(line)
        if self.discount_view == 'After Tax':
            if self.discount_type == 'Fixed':
                self.discounted_amount = self.discount_value
            elif self.discount_type == 'Percentage':
                #original on V8
                #amount_to_dis = (self.amount_untaxed + val) * (self.discount_value / 100)

                #adapt for v9
                # แก้ไข
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


purchaseorder_discount()

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def price_subtotal_round_global(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_amount > 0.0:
                if self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                    price -= line.discount_amount
                else:
                    price -= line.discount_amount/line.product_qty


            taxes = line.taxes_id.with_context(round=False).compute_all(price, line.order_id.currency_id, line.product_qty,
                                            product=line.product_id, partner=line.order_id.partner_id)


            price_tax = taxes['total_included'] - taxes['total_excluded'],
            price_subtotal =  taxes['total_excluded'],
            return price_subtotal, price_tax
