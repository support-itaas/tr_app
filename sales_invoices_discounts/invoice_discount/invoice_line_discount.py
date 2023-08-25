from __future__ import division
from odoo import fields, models, api ,_
import odoo.addons.decimal_precision as dp
# from odoo.tools import amount_to_text_en
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    # Add by Book 2019/12/13 ಠ_ಠ
    compute_discount_amount = fields.Boolean('Compute Discount Amount', compute='_compute_discount_amount')

    @api.depends('so_line_id', 'discount_amount', )
    def _compute_discount_amount(self):
        print("def _compute_discount_amount")
        for line in self:
            print(line.so_line_id.name)
            if line.so_line_id:
                print("line")
                discount_amount = line.so_line_id.discount_amount
                line.update({
                    'discount_amount': discount_amount,
                })

    def price_subtotal_round_global(self):
        for line in self:
            currency = self.invoice_id and self.invoice_id.currency_id or None
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

            if line.discount_amount > 0.0:
                if self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                    price -= line.discount_amount
                else:
                    price -= line.discount_amount/line.quantity


            taxes = False
            if line.invoice_line_tax_ids:
                taxes = line.invoice_line_tax_ids.with_context(round=False).compute_all(price, currency, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            if taxes:
                price_tax = taxes['total_included'] - taxes['total_excluded'],
                price_subtotal = taxes['total_excluded'],
            else:
                price_subtotal = line.quantity * price
                price_tax = 0.00
            return price_subtotal, price_tax