# -*- coding: utf-8 -*-
from __future__ import division
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare
from odoo.tools import float_round


class saleorder_discount(models.Model):
    _inherit = 'sale.order'
    discount_view = fields.Selection([('After Tax', 'After Tax'), ('Before Tax', 'Before Tax')], string='Discount Type',
                                     states={'draft': [('readonly', False)]},
                                     help='Choose If After or Before applying Taxes type of the Discount')
    discount_type = fields.Selection([('Fixed', 'Fixed'), ('Percentage', 'Percentage')], string='Discount Method',
                                     states={'draft': [('readonly', False)]})
    discount_value = fields.Float(string='Discount Value', states={'draft': [('readonly', False)]},
                                  help='Choose the value of the Discount')
    discounted_amount = fields.Float(compute='disc_amount', string='Discounted Amount', readonly=True)

    #original from V8
    # amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
    #                             store=True, readonly=True, compute='_compute_amounts')

    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                store=True, readonly=True, compute='_amount_all')

    is_new_vat_compute = fields.Boolean(string='Round Global',default=True)


    @api.multi
    def _prepare_invoice(self):
        res = super(saleorder_discount, self)._prepare_invoice()
        if self.discount_view and self.discount_type and self.discount_value:
            res['discount_view'] = self.discount_view
            res['discount_type'] = self.discount_type
            res['discount_value'] = self.discount_value

        return res

    @api.multi
    def apply_new_vat(self):
        self._amount_all()

    @api.depends('order_line.price_total','discount_type', 'discount_value','order_line.tax_id')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        # ir_values = self.env['ir.values']
        # taxes_id = ir_values.get_default('product.template', 'taxes_id', company_id=self.company_id.id)
        # t_id = self.env['account.tax'].browse(taxes_id)

        # Date:27-04-60
        # Comment:แก้ Error TRF
        for order in self:

            # ir_values = self.env['ir.values']
            # taxes_id = ir_values.get_default('product.template', 'taxes_id', company_id=order.company_id.id)


            t_id = self.env['account.tax'].search([('tax_report','=',True),('type_tax_use','=','sale')],limit=1)
            amount_untaxed = amount_tax = 0.0
            if not order.is_new_vat_compute:
                for line in order.order_line:
                    print (line.price_subtotal)
                    amount_untaxed += line.price_subtotal
                    # amount_tax += line.price_tax

                    if order.company_id.tax_calculation_rounding_method == 'round_globally':
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
                        amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    else:
                        amount_tax += line.price_tax
            else:
                for line in order.order_line:
                    ############## GET New price subtotal and price tax for amount total display with 7 digit
                    price_subtotal,  price_tax = line.price_subtotal_round_global()
                    amount_untaxed += price_subtotal[0]
                    amount_tax += price_tax[0]



            #add for discount calculation
            if order.discount_view == 'After Tax':
                if order.discount_type == 'Fixed':
                    amount_total = amount_untaxed + amount_tax - order.discount_value
                elif order.discount_type == 'Percentage':
                    amount_to_dis = (amount_untaxed + amount_tax) * (order.discount_value / 100)
                    amount_total = (amount_untaxed + amount_tax) - amount_to_dis
                else:
                    amount_total = amount_untaxed + amount_tax
            elif order.discount_view == 'Before Tax':
                if order.discount_type == 'Fixed':
                    the_value_before = amount_untaxed - order.discount_value
                    if t_id.amount:
                        the_tax_before = amount_tax - (order.discount_value * t_id.amount / 100)
                    else:
                        the_tax_before = amount_tax - (order.discount_value * 0.07)
                    amount_tax = the_tax_before
                    amount_total = the_value_before + the_tax_before
                elif order.discount_type == 'Percentage':
                    amount_to_dis = amount_untaxed * (order.discount_value / 100)
                    the_value_before = amount_untaxed - amount_to_dis
                    if t_id.amount:
                        the_tax_before = amount_tax - (amount_to_dis * t_id.amount / 100)
                    else:
                        the_tax_before = amount_tax - (amount_to_dis * 0.07)

                    amount_tax = the_tax_before
                    amount_total = the_value_before + the_tax_before
                else:
                    amount_total = amount_untaxed + amount_tax
            else:
                amount_total = amount_untaxed + amount_tax


            # ---------------------------------Manage Wrong Price Calculation------------------------------------------
            # order.amount_tax = amount_tax
            # order.amount_total = amount_total
            #
            # amount_tax = order.currency_id.round(amount_untaxed) * 7 / 100
            # amount_tax = round(amount_tax, 2)
            #
            # diff = amount_tax - order.amount_tax
            # if float_compare(abs(diff), 0.02, precision_digits=2) > 0:
            #     amount_tax = order.amount_tax
            #
            # ############### if include vat
            # if order.order_line and order.order_line[0].tax_id and not order.order_line[0].tax_id[0].price_include:
            #     # print ('YYYYYYYYYYYYYY')
            #     amount_tax = round(amount_tax, 2)
            # else:
            #     # print ('------XXXXXXXXxx')
            #     amount_tax = order.amount_tax
            #
            # # -------------------------------------------------------

            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total':amount_total,
                # 'amount_total': round(amount_untaxed + amount_tax,2),
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


saleorder_discount()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    discount_amount = fields.Float('Discount (Amount)', default=0.0)

    def price_subtotal_round_global(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_amount > 0.0:
                if self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                    price -= line.discount_amount
                else:
                    price -= line.discount_amount / line.product_uom_qty

            taxes = line.tax_id.with_context(round=False).compute_all(price, line.order_id.currency_id,
                                                                      line.product_uom_qty,
                                                                      product=line.product_id,
                                                                      partner=line.order_id.partner_id)

            price_tax = taxes['total_included'] - taxes['total_excluded'],
            price_subtotal = taxes['total_excluded'],
            return price_subtotal, price_tax

    #option discount amount per unit or price sub total
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """

        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_amount > 0.0:
                if self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                    price -= line.discount_amount
                else:
                    price -= line.discount_amount/line.product_uom_qty

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })



class res_company(models.Model):
    _inherit = "res.company"

    # sale_condition = fields.Text(string="เงื่อนไขการรับประกันสินค้า",translate=True)
    discount_amount_condition = fields.Selection([
        ('unit','Per Unit'),
        ('total','Per Total')
    ],default='total',string="Discount Amount Condition")
